from PyQt6 import QtCore, QtWidgets
import paho.mqtt.client as mqtt
from database import log_action 
from database import list_trucks 

class OperatorInterface(QtWidgets.QWidget):
    value = 0

    def __init__(self, operator_name):
        super().__init__()
        self.operator_name = operator_name
        self.broker_address = "localhost"
        self.port = 1883
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.port)
        self.client.subscribe("#")
        self.client.loop_start()

        self.mode = "manual"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Water Filling System - Operator: {self.operator_name}")
        self.setGeometry(100, 100, 400, 400)

        manual_radio = QtWidgets.QRadioButton("Manual")
        manual_radio.setChecked(True)
        manual_radio.toggled.connect(lambda: self.change_mode("manual"))

        barcode_radio = QtWidgets.QRadioButton("Barcode")
        barcode_radio.toggled.connect(lambda: self.change_mode("barcode"))

        self.truck_combo = QtWidgets.QComboBox()
        self.truck_combo.addItems(list_trucks()) 
        self.truck_combo.currentIndexChanged.connect(self.on_truck_change)

        self.flow_meter_label = QtWidgets.QLabel(f"Current Flow Meter: {self.value} L")

        self.quantity_entry = QtWidgets.QLineEdit()
        self.quantity_entry.setPlaceholderText("Enter quantity:")

        self.barcode_entry = QtWidgets.QLineEdit()
        self.barcode_entry.setPlaceholderText("Scan barcode here:")
        self.barcode_entry.setEnabled(False)
        self.barcode_entry.returnPressed.connect(self.process_barcode)

        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_action)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_action)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setRange(0, 100)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(manual_radio)
        layout.addWidget(barcode_radio)
        layout.addWidget(self.truck_combo)
        layout.addWidget(self.flow_meter_label)
        layout.addWidget(self.quantity_entry)
        layout.addWidget(self.barcode_entry)        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

    def change_mode(self, mode):
        """تغيير الوضع بين يدوي وباركود"""
        self.mode = mode
        if mode == "manual":
            self.quantity_entry.setEnabled(True)
            self.truck_combo.setEnabled(True)
            self.barcode_entry.setEnabled(False)
        elif mode == "barcode":
            self.quantity_entry.setEnabled(False)
            self.truck_combo.setEnabled(False)
            self.barcode_entry.setEnabled(True)
            self.barcode_entry.setFocus()

    def on_truck_change(self):        
        self.client.publish(f"{self.truck_combo.currentText()}/refresh", "refresh")        

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode()
        truck = topic.split('/')
        if topic.endswith("/flowmeter"):
            try:
                if truck[0] == self.truck_combo.currentText():
                    self.value = int(message)                                
                    self.progress_bar.setValue(self.value) 
            except ValueError:
                print("Invalid flowmeter value received:", message)

        elif topic.endswith("/state"):
            try:
                if message == 'stop':                    
                    log_action(self.operator_name, truck[0], self.value)
                    print(f"Logged action: Operator: {self.operator_name}, Truck: {self.truck_combo.currentText()}, Quantity: {self.value}")
                    self.client.publish(f"{self.truck_combo.currentText()}/refresh", "refresh")
            except ValueError:
                print("Invalid flowmeter value received:", message)

        elif topic.endswith("/refresh"):
            if truck[0] == self.truck_combo.currentText():
                if message != "refresh":
                    self.value = int(message)
                    self.flow_meter_label.setText(f"Current Flow Meter: {message} L")                                                  
                    self.progress_bar.setValue(self.value)

    def start_action(self):
        """بدء عملية التعبئة"""
        truck_id = self.truck_combo.currentText()
        quantity = self.quantity_entry.text()

        if quantity:
            self.client.publish(f"{truck_id}/quantity", quantity)
            print(f"Quantity {quantity} sent to {truck_id}")
            self.progress_bar.setMaximum(int(quantity)) 
            self.progress_bar.setValue(0) 
            self.client.publish(f"{truck_id}/state", "start")
        else:
            print("Please enter a valid quantity")

    def stop_action(self):
        """إيقاف عملية التعبئة"""
        truck_id = self.truck_combo.currentText()
        self.client.publish(f"{truck_id}/state", "stop")

    def process_barcode(self):
        """معالجة الباركود المدخل"""        
        barcode = self.barcode_entry.text()
        if barcode:
            print(f"Barcode scanned: {barcode}")
            truck_id, quantity = barcode.split("-") 
            self.truck_combo.setCurrentText(truck_id)
            self.quantity_entry.setText(quantity)
            self.send_quantity()
            self.barcode_entry.clear()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    operator_interface = OperatorInterface("Operator 1")
    operator_interface.show()
    sys.exit(app.exec())
