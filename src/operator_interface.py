from PyQt6 import QtCore, QtWidgets, QtGui  # Add QtGui import
from database import get_ports, store_port_data_from_mqtt, create_table, get_flowmeter_value, log_action, update_log_on_stop, get_logs, server_log, get_operator_id, get_channel_entry, get_config
import threading
import time
import paho.mqtt.client as mqtt  # Import the MQTT client
from login_window import LoginWindow  # Import LoginWindow from the new file

class WaterTankWidget(QtWidgets.QWidget):
    def __init__(self, max_level=100):
        super().__init__()
        self.max_level = max_level  # الحد الأقصى لمستوى الماء
        self._water_level = 0  # المستوى الحالي
        self.setMinimumSize(200, 400)  # حجم الواجهة

    def setWaterLevel(self, level):
        self._water_level = max(0, min(level, self.max_level))
        self.update()  # إعادة رسم الواجهة

    def getWaterLevel(self):
        return self._water_level

    waterLevel = QtCore.pyqtProperty(int, getWaterLevel, setWaterLevel)

    def setMaxLevel(self, max_level):
        self.max_level = max_level
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # إعداد فرشاة الرسم
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))

        # رسم الشكل البيضاوي العلوي
        top_rect = QtCore.QRectF(50, 40, 100, 30)
        painter.drawEllipse(top_rect)

        # رسم الجدران الجانبية
        painter.drawLine(50, 55, 50, 350)
        painter.drawLine(150, 55, 150, 350)

        # رسم القاعدة البيضاوية
        bottom_rect = QtCore.QRectF(50, 340, 100, 30)
        painter.drawEllipse(bottom_rect)

        # رسم الخطوط الأفقية داخل الخزان
        for i in range(6):
            y = 100 + i * 40
            painter.drawArc(50, y, 100, 20, 0, 180 * 16)  # رسم خط منحني

        # حساب ارتفاع مستوى الماء
        water_height = int((self._water_level / self.max_level) * 290)
        water_top = 340 - water_height

        # رسم مستوى الماء
        water_path = QtGui.QPainterPath()
        water_path.addRoundedRect(50, water_top, 100, water_height, 20, 20)
        painter.fillPath(water_path, QtGui.QColor(0, 100, 255, 150))

        # رسم تموجات على سطح الماء
        wave_rect = QtCore.QRectF(50, water_top - 10, 100, 20)
        painter.drawArc(wave_rect, 0, 180 * 16)

        # عرض الكمية المتبقية والكمية التي تم ملؤها
        painter.setFont(QtGui.QFont("Arial", 10))
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0), 1))  # اللون الأخضر
        painter.drawText(50, water_top - 20, f"المملوء: {self._water_level} L")
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 1))  # اللون الأحمر
        painter.drawText(50, 360, f"المتبقي: {self.max_level - self._water_level} L")

class OperatorInterface(QtWidgets.QWidget):
    value = 0
    required_quantity = 0
    initial_flowmeter_value = 0

    # Define the signal correctly
    update_flowmeter_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, operator_name):
        super().__init__()
        self.operator_name = operator_name
        print(get_operator_id(self.operator_name))
        self.init_ui()
        self.flowmeter_values = {}  # Ensure this is initialized here
        self.start_mqtt_thread()        
        self.status = {}  # Dictionary to store the status of each port
        self.sent_logs = set()  # Set to track sent logs        

        # Connect the signal to the update_flowmeter_signal method
        self.update_flowmeter_signal.connect(self.update_flowmeter_readings)

    def init_ui(self):
        self.setWindowTitle(f"نظام تعبئة المياه - المشغل: {self.operator_name}")
        self.showFullScreen()  # Make the window full screen

        layout = QtWidgets.QVBoxLayout()

        # Add a horizontal layout for the logo, clock, and radio buttons
        top_layout = QtWidgets.QHBoxLayout()

        # Add the logo image
        logo_label = QtWidgets.QLabel(self)
        logo_pixmap = QtGui.QPixmap("src/logo.png")  # Replace with the path to your logo image
        logo_pixmap = logo_pixmap.scaled(150, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio)  # Resize the logo
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        top_layout.addWidget(logo_label)

        # Add the clock
        self.clock_label = QtWidgets.QLabel(self)
        self.clock_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("color: #3EB489; font-size: 24px;")  # Set the color to ming green and font size
        top_layout.addWidget(self.clock_label)

        # Add the radio buttons
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

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        self.port_cards_layout = QtWidgets.QGridLayout(scroll_content)
        self.port_cards_layout.setSpacing(30)  # Add padding between cards
        self.load_ports()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        logout_button = QtWidgets.QPushButton("تسجيل الخروج", self)
        logout_button.clicked.connect(self.logout_action)
        layout.addWidget(logout_button)

        self.setLayout(layout)

        # Start the timer to update the clock
        self.start_clock()

    def start_clock(self):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)  # Update the clock every second
        self.update_clock()  # Initial call to set the current time

    def update_clock(self):
        current_time = QtCore.QTime.currentTime().toString("hh:mm:ss")
        self.clock_label.setText(current_time)

    def logout_action(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def load_ports(self):
        ports = get_ports()
        for idx, port in enumerate(ports):
            port_name, mode, config = port
            card = QtWidgets.QGroupBox(port_name)            
            card_layout = QtWidgets.QVBoxLayout()

            truck_number_label = QtWidgets.QLabel("رقم الشاحنة:", self)
            truck_number_entry = QtWidgets.QLineEdit()
            truck_number_entry.setObjectName("truck_number_entry")
            truck_number_entry.setPlaceholderText("أدخل رقم الشاحنة")

            receipt_number_label = QtWidgets.QLabel("رقم الإيصال:", self)
            receipt_number_entry = QtWidgets.QLineEdit()
            receipt_number_entry.setObjectName("receipt_number_entry")
            receipt_number_entry.setPlaceholderText("أدخل رقم الإيصال")

            target_quantity_label = QtWidgets.QLabel("الكمية المطلوبة:", self)
            add_quantity_entry = QtWidgets.QLineEdit()
            add_quantity_entry.setObjectName("add_quantity_entry")
            add_quantity_entry.setPlaceholderText("أدخل الكمية المراد إضافتها")

            actual_quantity_label = QtWidgets.QLabel("الكمية الفعلية: 0")
            actual_quantity_label.setObjectName("Actual Quantity")

            flow_meter_reading_label = QtWidgets.QLabel("قراءة عداد التدفق: 0")
            flow_meter_reading_label.setObjectName("Flow Meter Reading")

            water_tank = WaterTankWidget()
            water_tank.setObjectName("water_tank")

            start_button = QtWidgets.QPushButton("ابدأ")
            start_button.clicked.connect(lambda _, pn=port_name, aqe=add_quantity_entry, rne=receipt_number_entry, tne=truck_number_entry, wt=water_tank: self.start_filling(pn, aqe, rne, tne, wt))

            stop_button = QtWidgets.QPushButton("توقف")
            stop_button.clicked.connect(lambda _, pn=port_name: self.stop_filling(pn))

            form_layout = QtWidgets.QFormLayout()
            form_layout.addRow(truck_number_label, truck_number_entry)
            form_layout.addRow(receipt_number_label, receipt_number_entry)
            form_layout.addRow(target_quantity_label, add_quantity_entry)
            form_layout.addRow(actual_quantity_label)
            form_layout.addRow(flow_meter_reading_label)
            form_layout.addRow(water_tank)
            form_layout.addRow(start_button)
            form_layout.addRow(stop_button)

            card_layout.addLayout(form_layout)
            card.setLayout(card_layout)

            self.port_cards_layout.addWidget(card, idx // 5, idx % 5)  # Arrange cards in a grid

    def change_mode(self, mode):
        self.mode = mode
        if mode == "manual":
            self.quantity_entry.setEnabled(True)
            self.barcode_entry.setEnabled(False)
        elif mode == "barcode":
            self.quantity_entry.setEnabled(False)
            self.barcode_entry.setEnabled(True)
            self.barcode_entry.setFocus()

    def start_filling(self, port_name, add_quantity_entry ,receipt_number_entry, truck_number_entry, water_tank):
        if(add_quantity_entry.text() and truck_number_entry.text() ):        
            if( not self.is_disabled(port_name)):            
                chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter= get_channel_entry(port_name)
                truck_number = truck_number_entry.text()
                server_log(int(chanel_truck_number),int(truck_number))
                operator_id = get_operator_id(self.operator_name)
                server_log(int(chanel_operator_id), operator_id)
                receipt_number = receipt_number_entry.text()
                server_log(int(chanel_receipt_number),int(receipt_number))
                quantity = add_quantity_entry.text()
                server_log(int(chanel_required_quantity),quantity)
                self.flowmeter_values[port_name] = get_flowmeter_value(port_name)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_action("station_name", port_name, self.operator_name, truck_number, receipt_number, quantity, None, None, timestamp, None)                
                self.mqtt_client.publish(f"{port_name}/logdata", operator_id + "," + truck_number + "," + receipt_number + "," + quantity + "," + timestamp)
                self.mqtt_client.publish(f"{port_name}/quantity", quantity)
                self.mqtt_client.publish(f"{port_name}/state", "start")
                water_tank.setMaxLevel(float(quantity))  # Set the max level of the tank to the required quantity
            else :
                    QtWidgets.QMessageBox.critical(self, "خطأ", "المنفذ قيد التعبئة بالفعل")
        else:
            QtWidgets.QMessageBox.critical(self, "خطأ", "يرجى ملء جميع الحقول")

    def stop_filling(self, port_name):
        chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter= get_channel_entry(port_name)
        self.mqtt_client.publish(f"{port_name}/state", "stop")
        actual_quantity = self.get_actual_quantity(port_name)
        flow_meter_value = get_flowmeter_value(port_name)
        logout_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        update_log_on_stop(port_name, actual_quantity, flow_meter_value, logout_time)
        server_log(int(chanel_actual_quantity), float(actual_quantity))
        server_log(int(chanel_flowmeter), float(flow_meter_value))

    def get_actual_quantity(self, port_name):
        card = self.get_card_by_port_name(port_name)
        if card:
            actual_quantity_label = card.findChild(QtWidgets.QLabel, "Actual Quantity")
            if actual_quantity_label:
                actual_quantity_text = actual_quantity_label.text().replace("Actual Quantity: ", "")
                try:
                    return float(actual_quantity_text)
                except ValueError:
                    return 0
        return 0

    def start_mqtt_thread(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("localhost", 1883, 60)
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
                actual_quantity_label.setText(f"الكميه الفعليه: {actual_quantity}")
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
        client.subscribe("#")  # Subscribe to all topics

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        if "/flowmeter" in topic:
            port_name = topic.split('/')[0]
            flow_meter_value = payload
            store_port_data_from_mqtt(port_name, flow_meter_value, None)
            self.update_flowmeter_signal.emit(port_name, flow_meter_value) 
        elif "/state" in topic:
            port_name = topic.split('/')[0]
            state = payload
            store_port_data_from_mqtt(port_name, None, state)
            if state == "filling":                
                self.disable_card_fields(port_name)
            elif state == "stop":
                chanel_truck_number, chanel_operator_id, chanel_receipt_number, chanel_required_quantity, chanel_actual_quantity, chanel_flowmeter= get_channel_entry(port_name)
                actual_quantity = self.get_actual_quantity(port_name)
                server_log(chanel_actual_quantity, float(actual_quantity))
                flow_meter_value = get_flowmeter_value(port_name)
                logout_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                update_log_on_stop(port_name, actual_quantity, flow_meter_value, logout_time)
                self.enable_card_fields(port_name)        
        elif "/update" in topic:
            port_name = topic.split('/')[0]
            config = ','.join(get_config(port_name))
            self.mqtt_client.publish(f"{port_name}/conf", config)
            print(config)

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
                actual_quantity = float(flow_meter_value) - float(initial_value)
                self.update_actual_quantity_label(port_name, actual_quantity)
                self.update_progress_bar(port_name, actual_quantity)


if __name__ == "__main__":
    import sys
    create_table()  # Ensure tables are created
    app = QtWidgets.QApplication(sys.argv)
    operator_interface = OperatorInterface("Operator 1")
    operator_interface.show()
    sys.exit(app.exec())