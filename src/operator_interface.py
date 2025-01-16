from PyQt6 import QtCore, QtWidgets
from database import get_ports, store_port_data_from_mqtt, create_table, get_flowmeter_value, log_action  # Import necessary functions
import threading
import time
import paho.mqtt.client as mqtt  # Import the MQTT client

class OperatorInterface(QtWidgets.QWidget):
    value = 0
    required_quantity = 0
    initial_flowmeter_value = 0

    def __init__(self, operator_name):
        super().__init__()
        self.operator_name = operator_name
        self.init_ui()
        self.start_mqtt_thread()
        self.start_update_thread()
        self.flowmeter_values = {}  # Dictionary to store flowmeter values

    def init_ui(self):
        self.setWindowTitle(f"Water Filling System - Operator: {self.operator_name}")
        self.setGeometry(100, 100, 800, 600)  # Increase the window size

        manual_radio = QtWidgets.QRadioButton("Manual")
        manual_radio.setChecked(True)
        manual_radio.toggled.connect(lambda: self.change_mode("manual"))

        barcode_radio = QtWidgets.QRadioButton("Barcode")
        barcode_radio.toggled.connect(lambda: self.change_mode("barcode"))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(manual_radio)
        layout.addWidget(barcode_radio)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        self.port_cards_layout = QtWidgets.QGridLayout(scroll_content)
        self.port_cards_layout.setSpacing(30)  # Add padding between cards
        self.load_ports()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def load_ports(self):
        ports = get_ports()
        for idx, port in enumerate(ports):
            port_name, mode = port
            card = QtWidgets.QGroupBox(port_name)            
            card_layout = QtWidgets.QVBoxLayout()

            truck_number_entry = QtWidgets.QLineEdit()
            truck_number_entry.setPlaceholderText("Enter truck number")

            receipt_number_entry = QtWidgets.QLineEdit()
            receipt_number_entry.setPlaceholderText("Enter receipt number")

            add_quantity_entry = QtWidgets.QLineEdit()
            add_quantity_entry.setPlaceholderText("Enter quantity to add")

            required_quantity_label = QtWidgets.QLabel("Required Quantity: 0")
            required_quantity_label.setObjectName("Required Quantity")

            actual_quantity_label = QtWidgets.QLabel("Actual Quantity: 0")
            actual_quantity_label.setObjectName("Actual Quantity")

            flow_meter_reading_label = QtWidgets.QLabel("Flow Meter Reading: 0")
            flow_meter_reading_label.setObjectName("Flow Meter Reading")

            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setObjectName("progress_bar")

            start_button = QtWidgets.QPushButton("Start")
            start_button.clicked.connect(lambda _, pn=port_name, aqe=add_quantity_entry, rne=receipt_number_entry, tne=truck_number_entry, rql=required_quantity_label: self.start_filling(pn, aqe, rne, tne, rql))

            stop_button = QtWidgets.QPushButton("Stop")
            stop_button.clicked.connect(lambda _, pn=port_name: self.stop_filling(pn))

            card_layout.addWidget(QtWidgets.QLabel(f"Mode: {mode}"))
            card_layout.addWidget(truck_number_entry)
            card_layout.addWidget(receipt_number_entry)
            card_layout.addWidget(add_quantity_entry)
            card_layout.addWidget(required_quantity_label)
            card_layout.addWidget(actual_quantity_label)
            card_layout.addWidget(flow_meter_reading_label)
            card_layout.addWidget(progress_bar)
            card_layout.addWidget(start_button)
            card_layout.addWidget(stop_button)
            card.setLayout(card_layout)

            self.port_cards_layout.addWidget(card, idx // 3, idx % 3)  # Arrange cards in a grid

    def change_mode(self, mode):
        """تغيير الوضع بين يدوي وباركود"""
        self.mode = mode
        if mode == "manual":
            self.quantity_entry.setEnabled(True)
            self.barcode_entry.setEnabled(False)
        elif mode == "barcode":
            self.quantity_entry.setEnabled(False)
            self.barcode_entry.setEnabled(True)
            self.barcode_entry.setFocus()

    def start_filling(self, port_name, add_quantity_entry ,receipt_number_entry, truck_number_entry, required_quantity_label):
        quantity = add_quantity_entry.text()
        truck_number = truck_number_entry.text()
        receipt_number = receipt_number_entry.text()
        required_quantity_label.setText(f"Required Quantity: {quantity}")
        self.mqtt_client.publish(f"{port_name}/quantity", quantity)
        self.mqtt_client.publish(f"{port_name}/state", "start")
        self.flowmeter_values[port_name] = get_flowmeter_value(port_name)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_action("station_name", port_name, self.operator_name, truck_number, receipt_number, quantity, None, None, timestamp, None)

    def stop_filling(self, port_name):
        self.mqtt_client.publish(f"{port_name}/state", "stop")

    def start_mqtt_thread(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever)
        self.mqtt_thread.start()

    def start_update_thread(self):
        self.update_thread = threading.Thread(target=self.update_flowmeter_readings)
        self.update_thread.start()

    def update_flowmeter_readings(self):
        while True:
            ports = get_ports()
            for port_name, _ in ports:
                flow_meter_value = get_flowmeter_value(port_name)
                if flow_meter_value is not None:
                    self.update_flowmeter_label(port_name, flow_meter_value)
                    if port_name in self.flowmeter_values:
                        initial_value = self.flowmeter_values[port_name]
                        actual_quantity = float(flow_meter_value) - float(initial_value)
                        self.update_actual_quantity_label(port_name, actual_quantity)
            time.sleep(0.2)  # Update every 0.2 seconds

    def update_flowmeter_label(self, port_name, flow_meter_value):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                flow_meter_reading_label = card.findChild(QtWidgets.QLabel, "Flow Meter Reading")
                flow_meter_reading_label.setText(f"Flow Meter Reading: {flow_meter_value}")
                break

    def update_actual_quantity_label(self, port_name, actual_quantity):
        for i in range(self.port_cards_layout.count()):
            card = self.port_cards_layout.itemAt(i).widget()
            if card.title() == port_name:
                actual_quantity_label = card.findChild(QtWidgets.QLabel, "Actual Quantity")
                actual_quantity_label.setText(f"Actual Quantity: {actual_quantity}")
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
        elif "/state" in topic:
            port_name = topic.split('/')[0]
            state = payload
            store_port_data_from_mqtt(port_name, None, state)
            if state == "stop":
                pass
                

if __name__ == "__main__":
    import sys
    create_table()  # Ensure tables are created
    app = QtWidgets.QApplication(sys.argv)
    operator_interface = OperatorInterface("Operator 1")
    operator_interface.show()
    sys.exit(app.exec())
