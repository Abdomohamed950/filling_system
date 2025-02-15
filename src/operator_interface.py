from PyQt6 import QtCore, QtWidgets, QtGui
from database import get_ports, store_port_data_from_mqtt, create_table, get_flowmeter_value, log_action, update_log_on_stop, get_logs, server_log, get_operator_id, get_channel_entry, get_config, create_server_connection, get_addresses, insert_offline_data, get_offline_data, delete_offline_data
import threading
import time
import paho.mqtt.client as mqtt  
from login_window import LoginWindow 
import pyodbc
from PIL import Image, ImageDraw
import numpy as np

class WaterTankWidget(QtWidgets.QWidget):
    def __init__(self, max_level=100):
        super().__init__()
        self.max_level = max_level  
        self._water_level = 0 
        self.valve_state = "مغلق"  # Default valve state
        self.setMinimumSize(200, 400)  
        
        self.tank_image = Image.open('src/tank.png')
        ports = get_ports()
        num_ports = len(ports)
        if num_ports > 6:
            self.tank_image = self.tank_image.resize((200, 400))
        else:
            self.tank_image = self.tank_image.resize((350, 520)) 

    def setWaterLevel(self, level):
        self._water_level = max(0, min(level, self.max_level))
        self.update()  

    def getWaterLevel(self):
        return self._water_level

    waterLevel = QtCore.pyqtProperty(int, getWaterLevel, setWaterLevel)

    def setMaxLevel(self, max_level):
        self.max_level = max_level
        self.update()

    def setValveState(self, state):
        self.valve_state = state
        self.update()

    def paintEvent(self, event):
        ports = get_ports()
        num_ports = len(ports)
        with QtGui.QPainter(self) as painter:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

            new_img = self.tank_image.copy()
            draw = ImageDraw.Draw(new_img, "RGBA")

            mask = Image.new("L", new_img.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            if num_ports > 5:
                fill_start_y = 240 
                fill_end_y = 315    
                fill_x_min = 95     
                fill_x_max = 177
            else:
                fill_start_y = 312
                fill_end_y = 410
                fill_x_min = 166
                fill_x_max = 311

            mask_draw.ellipse([(fill_x_min, fill_start_y), (fill_x_max, fill_end_y)], fill=255)

            current_fill_level = int(fill_end_y - (self._water_level / self.max_level) * (fill_end_y - fill_start_y))

            water_layer = Image.new("RGBA", new_img.size, (0, 0, 0, 0))
            water_draw = ImageDraw.Draw(water_layer)
            water_draw.ellipse([(fill_x_min, current_fill_level), (fill_x_max, fill_end_y)], fill=(0, 150, 255, 150))

            new_img = Image.composite(water_layer, new_img, mask)

            if self.valve_state in ["مغلق", "جاري الغلق"]:
                mask2 = Image.new("L", new_img.size, 0)
                mask_draw2 = ImageDraw.Draw(mask2)
                if num_ports > 5:
                    fill_start_y2 = 220 
                    fill_end_y2 = 295    
                    fill_x_min2 = 95     
                    fill_x_max2 = 177
                else:
                    fill_start_y2 = 115
                    fill_end_y2 = 310
                    fill_x_min2 = 166
                    fill_x_max2 = 311

                mask_draw2.ellipse([(fill_x_min2, fill_start_y2), (fill_x_max2, fill_end_y2)], fill=255)

                current_fill_level2 = int(fill_end_y2 - (self._water_level / self.max_level) * (fill_end_y2 - fill_start_y2))

                water_layer2 = Image.new("RGBA", new_img.size, (0, 0, 0, 0))
                water_draw2 = ImageDraw.Draw(water_layer2)
                water_draw2.ellipse([(fill_x_min2, current_fill_level2), (fill_x_max2, fill_end_y2)], fill=(0, 150, 255, 150))

                new_img = Image.composite(water_layer2, new_img, mask2)

            new_img = new_img.convert("RGBA")
            data = new_img.tobytes("raw", "RGBA")
            qimage = QtGui.QImage(data, new_img.size[0], new_img.size[1], QtGui.QImage.Format.Format_RGBA8888)
            pixmap = QtGui.QPixmap.fromImage(qimage)
            
            painter.drawPixmap(0, 0, pixmap)
            
            painter.setFont(QtGui.QFont("Arial", 10))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 1))  
            painter.drawText(210, current_fill_level - 40, f"المتبقي: {self.max_level - self._water_level} L")
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0), 1)) 
            painter.drawText(210, 390, f"الممتلئ: {self._water_level} L")


class OperatorInterface(QtWidgets.QWidget):
    value = 0
    required_quantity = 0
    initial_flowmeter_value = 0

    # Define the signal correctly
    update_flowmeter_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, operator_name):
        super().__init__()
        self.operator_name = operator_name    
        self.flowmeter_values = {} 
        self.actual_quantities = {}  # Dictionary to store actual quantities for each port
        self.status = {}  
        self.sent_logs = set()
        self.connection_status_label = QtWidgets.QLabel()  # Initialize the label here
        self.db_connected = self.check_db_connection()
        self.init_ui()
        self.update_flowmeter_signal.connect(self.update_flowmeter_readings)
        self.start_mqtt_thread()                

    def check_db_connection(self):
        try:
            connection = create_server_connection()
            connection.close()
            self.db_connected = True
            self.connection_status_label.setText("متصل")
            self.resend_offline_data()  # Resend offline data when connection is restored
            self.connection_status_label.setStyleSheet("color: green;")
        except pyodbc.OperationalError:
            self.db_connected = False
            self.connection_status_label.setText("غير متصل")
            self.connection_status_label.setStyleSheet("color: red;")
        return self.db_connected

    def resend_offline_data(self):
        offline_data = get_offline_data()
        for record in offline_data:
            record_id, channel_number, actual_value = record
            try:
                server_log(channel_number, actual_value)
                delete_offline_data(record_id)
            except Exception as e:
                print(f"Error resending offline data: {e}")

    def init_ui(self):
        self.setWindowTitle(f"نظام تعبئة المياه - المشغل: {self.operator_name}")
        self.showFullScreen()

        layout = QtWidgets.QVBoxLayout()

        
        top_layout = QtWidgets.QHBoxLayout()

        
        logo_label = QtWidgets.QLabel(self)
        logo_pixmap = QtGui.QPixmap("src/logo.png")  
        logo_pixmap = logo_pixmap.scaled(150, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        top_layout.addWidget(logo_label)

        connection_layout = QtWidgets.QVBoxLayout()
        connection_status_text = QtWidgets.QLabel("حالة الاتصال:")
        connection_layout.addWidget(connection_status_text)
        connection_layout.addWidget(self.connection_status_label)

        reconnect_button = QtWidgets.QPushButton("اعادة الاتصال", self)
        reconnect_button.clicked.connect(self.check_db_connection)
        connection_layout.addWidget(reconnect_button)
        
        connection_layout_widget = QtWidgets.QWidget()
        connection_layout_widget.setLayout(connection_layout)
        connection_layout_widget.setFixedSize(200, 100)  # Set the desired size
        top_layout.addWidget(connection_layout_widget, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        self.clock_label = QtWidgets.QLabel(self)
        self.clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("color: #3EB489; font-size: 24px;")
        top_layout.addWidget(self.clock_label)

        radio_layout = QtWidgets.QVBoxLayout()
        manual_radio = QtWidgets.QRadioButton("يدوي")
        manual_radio.setChecked(True)
        manual_radio.toggled.connect(lambda: self.change_mode("manual"))

        barcode_radio = QtWidgets.QRadioButton("باركود")
        barcode_radio.toggled.connect(lambda: self.change_mode("barcode"))

        radio_layout.addWidget(manual_radio)
        radio_layout.addWidget(barcode_radio)
        top_layout.addLayout(radio_layout)        
        top_layout.setAlignment(radio_layout, QtCore.Qt.AlignmentFlag.AlignRight)

        layout.addLayout(top_layout)

        self.port_cards_layout = QtWidgets.QGridLayout()  # Change to QGridLayout
        self.load_ports()
        layout.addLayout(self.port_cards_layout)

        logout_button = QtWidgets.QPushButton("تسجيل الخروج", self)
        logout_button.clicked.connect(self.logout_action)
        layout.addWidget(logout_button)

        self.setLayout(layout)

        
        self.start_clock()

    def start_clock(self):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000) 
        self.update_clock()

    def update_clock(self):
        current_time = QtCore.QTime.currentTime().toString("hh:mm:ss")
        self.clock_label.setText(current_time)

    def logout_action(self):
        self.mqtt_client.disconnect()
        self.mqtt_thread.join(timeout=2)
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def load_ports(self):
        ports = get_ports()
        num_ports = len(ports)
        for idx, port in enumerate(ports):
            port_name, mode, config = port
            card = QtWidgets.QGroupBox(port_name)
            card_layout = QtWidgets.QVBoxLayout()

            truck_number_label = QtWidgets.QLabel(":رقم الشاحنة", self)
            truck_number_entry = QtWidgets.QLineEdit()
            truck_number_entry.setObjectName("truck_number_entry")        
            truck_number_entry.setFixedSize(100, 30)  # Adjust size

            receipt_number_label = QtWidgets.QLabel(":رقم الإيصال", self)
            receipt_number_entry = QtWidgets.QLineEdit()
            receipt_number_entry.setObjectName("receipt_number_entry")
            receipt_number_entry.setFixedSize(100, 30)  # Adjust size

            target_quantity_label = QtWidgets.QLabel(":الكمية المطلوبة", self)
            add_quantity_entry = QtWidgets.QLineEdit()
            add_quantity_entry.setObjectName("add_quantity_entry")
            add_quantity_entry.setFixedSize(100, 30)  # Adjust size

            actual_quantity_label = QtWidgets.QLabel("الكمية الفعلية: 0")
            actual_quantity_label.setObjectName("Actual Quantity")
            actual_quantity_label.setMaximumSize(200, 30)  # أكبر حجم ممكن: عرض 200 بكسل، ارتفاع 40 بكسل

            flow_meter_reading_label = QtWidgets.QLabel("قراءة العداد: 0")
            flow_meter_reading_label.setObjectName("Flow Meter Reading")
            flow_meter_reading_label.setMaximumSize(200, 30)  # أكبر حجم ممكن: عرض 200 بكسل، ارتفاع 40 بكسل


            valve_state_label = QtWidgets.QLabel("حالة المحبس: مغلق")
            valve_state_label.setObjectName("Valve State")
            valve_state_label.setMaximumSize(200, 30)  # أكبر حجم ممكن: عرض 200 بكسل، ارتفاع 40 بكسل

            water_tank = WaterTankWidget()
            water_tank.setObjectName("water_tank")
            # water_tank.setFixedSize(150, 300)  # Adjust the size as needed


            start_button = QtWidgets.QPushButton("ابدأ")
            start_button.clicked.connect(lambda _, pn=port_name, aqe=add_quantity_entry, rne=receipt_number_entry, tne=truck_number_entry, wt=water_tank: self.start_filling(pn, aqe, rne, tne, wt))

            stop_button = QtWidgets.QPushButton("توقف")
            stop_button.clicked.connect(lambda _, pn=port_name: self.stop_filling(pn))

            form_layout = QtWidgets.QGridLayout()
            if num_ports > 5:
                form_layout.addWidget(truck_number_label, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(truck_number_entry, 0, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(receipt_number_label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(receipt_number_entry, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(target_quantity_label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(add_quantity_entry, 2, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(actual_quantity_label, 3,0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(flow_meter_reading_label, 4, 0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(valve_state_label, 5,0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(water_tank, 6, 0,1,2)
                form_layout.addWidget(start_button, 7, 0, 1, 2)
                form_layout.addWidget(stop_button, 8, 0, 1, 2)
            else :
                form_layout.addWidget(truck_number_label, 0, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(truck_number_entry, 0, 1, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(receipt_number_label, 1, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(receipt_number_entry, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(target_quantity_label, 2, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                form_layout.addWidget(add_quantity_entry, 2, 1, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(actual_quantity_label, 3,0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(flow_meter_reading_label, 4, 0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)
                form_layout.addWidget(valve_state_label, 5, 0,1,2, QtCore.Qt.AlignmentFlag.AlignRight)  # نقل إلى نفس الصف
                form_layout.addWidget(water_tank, 6, 0, 1, 2)  # العنصر يمتد عبر عمودين
                form_layout.addWidget(start_button, 7, 0, 1, 2)  # العنصر يمتد عبر عمودين
                form_layout.addWidget(stop_button, 8, 0, 1, 2)  # العنصر يمتد عبر عمودين

            card_layout.addLayout(form_layout)
            card.setLayout(card_layout)
            if num_ports > 5:
                card.setFixedSize(210, 700)  # Adjust the size to fit 8 cards side by side
                self.port_cards_layout.addWidget(card, idx // 8, idx % 8)  # Add card to the grid layout
            else:
                card.setFixedSize(350, 800)  # Adjust the size for fewer cards
                self.port_cards_layout.addWidget(card, idx // 5, idx % 5)  # Add card to the grid layout


    def change_mode(self, mode):
        self.mode = mode
        if mode == "manual":
            self.quantity_entry.setEnabled(True)
            self.barcode_entry.setEnabled(False)
        elif mode == "barcode":
            self.quantity_entry.setEnabled(False)
            self.barcode_entry.setEnabled(True)
            self.barcode_entry.setFocus()

    def start_filling(self, port_name, add_quantity_entry, receipt_number_entry, truck_number_entry, water_tank):
        try:
            channel_entry = get_channel_entry(port_name)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            channel_entry = None

        if channel_entry is not None:
            chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter = channel_entry
            if(add_quantity_entry.text() and truck_number_entry.text() ):        
                if( not self.is_disabled(port_name)):            
                    truck_number = truck_number_entry.text()
                    operator_id = get_operator_id(self.operator_name)
                    receipt_number = receipt_number_entry.text()
                    quantity = add_quantity_entry.text()
                    self.flowmeter_values[port_name] = get_flowmeter_value(port_name)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    try:
                        log_action("station_name", port_name, self.operator_name, truck_number, receipt_number, quantity, None, None, timestamp, None)
                    except Exception as e:
                        print(f"Error logging action to database: {e}")
                    self.mqtt_client.publish(f"{port_name}/logdata", operator_id + "," + truck_number + "," + receipt_number + "," + quantity + "," + timestamp)
                    self.mqtt_client.publish(f"{port_name}/quantity", quantity)
                    self.mqtt_client.publish(f"{port_name}/state", "start")
                    water_tank.setMaxLevel(float(quantity))  
                    if self.db_connected:
                        try:
                            server_log(int(chanel_truck_number), int(truck_number))
                            server_log(int(chanel_operator_id), operator_id)
                            server_log(int(chanel_receipt_number), int(receipt_number))
                            server_log(int(chanel_required_quantity), quantity)
                        except (ValueError, ConnectionError, pyodbc.OperationalError) as e:
                            print(f"Error logging server data: {e}")
                            self.db_connected = False
                            self.connection_status_label.setText("غير متصل")
                            self.connection_status_label.setStyleSheet("color: red;")
                            insert_offline_data(int(chanel_truck_number), int(truck_number))
                            insert_offline_data(int(chanel_operator_id), operator_id)
                            insert_offline_data(int(chanel_receipt_number), int(receipt_number))
                            insert_offline_data(int(chanel_required_quantity), quantity)
                    else:
                        insert_offline_data(int(chanel_truck_number), int(truck_number))
                        insert_offline_data(int(chanel_operator_id), operator_id)
                        insert_offline_data(int(chanel_receipt_number), int(receipt_number))
                        insert_offline_data(int(chanel_required_quantity), quantity)
                else :
                        QtWidgets.QMessageBox.critical(self, "خطأ", "المنفذ قيد التعبئة بالفعل")
            else:
                QtWidgets.QMessageBox.critical(self, "خطأ", "يرجى ملء جميع الحقول")
        else:
            print(f"Error: get_channel_entry returned None for port_name {port_name}")

    def stop_filling(self, port_name):
        try:
            chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter = get_channel_entry(port_name)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter = None, None, None, None, None, None

        if self.mqtt_client:
            self.mqtt_client.publish(f"{port_name}/state", "stop")

    def get_actual_quantity(self, port_name):
        return self.actual_quantities.get(port_name, 0)

    def start_mqtt_thread(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        mqtt_address, server_address = get_addresses()
        try:
            self.mqtt_client.connect(mqtt_address, 1883, 60)
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
        self.mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever)
        self.mqtt_thread.start()

    def update_progress_bar(self, port_name, actual_quantity):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                water_tank = card.findChild(WaterTankWidget, "water_tank")
                water_tank.setWaterLevel(actual_quantity)
                break

    def update_flowmeter_label(self, port_name, flow_meter_value):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                flow_meter_reading_label = card.findChild(QtWidgets.QLabel, "Flow Meter Reading")
                flow_meter_reading_label.setText(f"قراءة العداد: {flow_meter_value}")
                break

    def update_actual_quantity_label(self, port_name, actual_quantity):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                actual_quantity_label = card.findChild(QtWidgets.QLabel, "Actual Quantity")
                actual_quantity_label.setText(f"الكمية الفعلية: {actual_quantity}")
                break

    def update_valve_state_label(self, port_name, valve_state):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                valve_state_label = card.findChild(QtWidgets.QLabel, "Valve State")
                valve_state_label.setText(f"حالة المحبس: {valve_state}")
                water_tank = card.findChild(WaterTankWidget, "water_tank")
                water_tank.setValveState(valve_state)
                break

    def disable_card_fields(self, port_name):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                for child in card.findChildren(QtWidgets.QWidget):
                    if isinstance(child, QtWidgets.QPushButton) and child.text() == "توقف":
                        continue
                    child.setDisabled(True)
                break

    def is_disabled(self, port_name):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                for child in card.findChildren(QtWidgets.QWidget):
                    if not child.isEnabled():
                        return True
                return False
        return False

    def enable_card_fields(self, port_name):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                for child in card.findChildren(QtWidgets.QWidget):
                    child.setDisabled(False)
                break

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("#")  

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        if "/flowmeter" in topic:
            port_name = topic.split('/')[0]
            flow_meter_value = payload
            try:
                store_port_data_from_mqtt(port_name, flow_meter_value, None)
            except Exception as e:
                print(f"Error storing flow meter data to database: {e}")
            self.update_flowmeter_signal.emit(port_name, flow_meter_value) 
        elif "/state" in topic:
            port_name = topic.split('/')[0]
            state = payload
            try:
                store_port_data_from_mqtt(port_name, None, state)
            except Exception as e:
                print(f"Error storing port data to database: {e}")
            if state == "filling":                
                self.disable_card_fields(port_name)
            elif state == "stop":
                try:
                    chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter= get_channel_entry(port_name)
                except Exception as e:
                    print(f"Error connecting to database: {e}")
                    chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter = None, None, None, None, None, None
                actual_quantity = self.get_actual_quantity(port_name)
                flow_meter_value = get_flowmeter_value(port_name)
                logout_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                try:
                    update_log_on_stop(port_name, actual_quantity, flow_meter_value, logout_time)
                except Exception as e:
                    print(f"Error updating log on stop: {e}")
                self.enable_card_fields(port_name)        
                if self.db_connected:
                    try:
                        server_log(chanel_actual_quantity, float(actual_quantity))
                    except (ValueError, pyodbc.OperationalError) as e:
                        print(f"Error logging actual quantity: {e}")
                        self.db_connected = False
                        self.connection_status_label.setText("غير متصل")
                        self.connection_status_label.setStyleSheet("color: red;")
                        insert_offline_data(int(chanel_actual_quantity), float(actual_quantity))
                else:
                    insert_offline_data(int(chanel_actual_quantity), float(actual_quantity))
        elif "/update" in topic:
            port_name = topic.split('/')[0]
            config = ','.join(get_config(port_name))
            self.mqtt_client.publish(f"{port_name}/conf", config)
            print(config)
        elif "/valve_state" in topic:
            port_name = topic.split('/')[0]
            valve_state = payload
            self.update_valve_state_label(port_name, valve_state)

    def get_card_by_port_name(self, port_name):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                return card
        return None

    def update_flowmeter_readings(self, port_name, flow_meter_value):
        self.update_flowmeter_label(port_name, flow_meter_value)
        if port_name in self.flowmeter_values:
            initial_value = self.flowmeter_values[port_name]
            if initial_value is not None and initial_value != "":
                try:
                    actual_quantity = float(flow_meter_value) - float(initial_value)
                    if actual_quantity < 0:
                        actual_quantity = 0
                    self.update_actual_quantity_label(port_name, actual_quantity)
                    self.actual_quantities[port_name] = actual_quantity  # Update the actual quantity in the dictionary
                    self.update_progress_bar(port_name, actual_quantity)
                except ValueError:
                    print(f"Error parsing flow meter value for port {port_name}: {flow_meter_value}")

if __name__ == "__main__":
    import sys
    try:
        create_table()
    except Exception as e:
        print(f"Error creating database table: {e}")
    app = QtWidgets.QApplication(sys.argv)
    operator_interface = OperatorInterface("abdo")
    operator_interface.show()
    sys.exit(app.exec())