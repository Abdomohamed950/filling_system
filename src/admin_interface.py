from PyQt6 import QtCore, QtWidgets
from database import create_table, add_operator, remove_operator, list_operators, is_password_unique, add_port, remove_port, get_ports, get_logs, update_port, is_port_name_unique, update_operator
from login_window import LoginWindow  # Import LoginWindow from the new file

class AdminInterface(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        create_table()  
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Admin Interface")
        self.showMaximized()  # Make the window fullscreen
        self.center()

        notebook = QtWidgets.QTabWidget(self)

        # Tab for managing operators
        operator_frame = QtWidgets.QWidget()
        operator_layout = QtWidgets.QVBoxLayout(operator_frame)

        add_operator_name_label = QtWidgets.QLabel("Operator Name:", self)
        self.add_operator_name_entry = QtWidgets.QLineEdit(self)

        add_operator_ID_label = QtWidgets.QLabel("Operator ID:", self)
        self.add_operator_ID_entry = QtWidgets.QLineEdit(self)

        add_operator_password_label = QtWidgets.QLabel("Operator Password:", self)
        self.add_operator_password_entry = QtWidgets.QLineEdit(self)
        self.add_operator_password_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        add_operator_button = QtWidgets.QPushButton("Add Operator", self)
        add_operator_button.clicked.connect(self.add_operator_action)

        self.operators_table = QtWidgets.QListWidget(self)

        remove_operator_button = QtWidgets.QPushButton("Remove Selected Operator", self)
        remove_operator_button.clicked.connect(self.remove_selected_operator_action)

        update_operator_button = QtWidgets.QPushButton("Update Selected Operator", self)
        update_operator_button.clicked.connect(self.update_selected_operator_action)

        operator_layout.addWidget(add_operator_name_label)
        operator_layout.addWidget(self.add_operator_name_entry)
        operator_layout.addWidget(add_operator_ID_label)
        operator_layout.addWidget(self.add_operator_ID_entry)
        operator_layout.addWidget(add_operator_password_label)
        operator_layout.addWidget(self.add_operator_password_entry)
        operator_layout.addWidget(add_operator_button)
        self.operator_table = QtWidgets.QTableWidget()
        self.operator_table.setColumnCount(2)
        self.operator_table.setHorizontalHeaderLabels(["Name", "ID"])
        operator_layout.addWidget(self.operator_table)
        operator_layout.addWidget(update_operator_button)
        operator_layout.addWidget(remove_operator_button)
        operator_frame.setLayout(operator_layout)

        notebook.addTab(operator_frame, "Manage Operators")

        # Tab for managing ports

        port_frame = QtWidgets.QWidget()
        port_layout = QtWidgets.QVBoxLayout(port_frame)

        add_port_name_label = QtWidgets.QLabel("Port Name:")
        self.add_port_name_entry = QtWidgets.QLineEdit()

        add_port_mode_label = QtWidgets.QLabel("Mode:")
        self.add_port_mode_entry = QtWidgets.QComboBox()
        self.add_port_mode_entry.addItems(["modbus", "milli ampere", "pulse"])
        self.add_port_mode_entry.currentIndexChanged.connect(self.update_port_settings)

        # Dynamic settings layout
        self.dynamic_settings_layout = QtWidgets.QVBoxLayout()

        self.add_port_button = QtWidgets.QPushButton("Add Port")
        self.add_port_button.clicked.connect(self.add_port_action)

        self.ports_table = QtWidgets.QTableWidget()
        self.ports_table.setColumnCount(3)
        self.ports_table.setHorizontalHeaderLabels(["Port Name", "Mode", "Configuration"])
        self.ports_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        port_layout.addWidget(add_port_name_label)
        port_layout.addWidget(self.add_port_name_entry)
        port_layout.addWidget(add_port_mode_label)
        port_layout.addWidget(self.add_port_mode_entry)
        port_layout.addLayout(self.dynamic_settings_layout)
        port_layout.addWidget(self.add_port_button)
        port_layout.addWidget(self.ports_table)

        port_frame.setLayout(port_layout)        

        self.update_port_settings()
        remove_port_button = QtWidgets.QPushButton("Remove Selected Port", self)
        remove_port_button.clicked.connect(self.remove_selected_port_action)
        port_layout.addWidget(remove_port_button)
        # Tab for history
        history_frame = QtWidgets.QWidget()
        history_layout = QtWidgets.QVBoxLayout(history_frame)

        self.history_table = QtWidgets.QTableWidget()
        self.history_table.setColumnCount(10)
        self.history_table.setHorizontalHeaderLabels(["Station Name", "Port Number", "Operator Name", "Truck Number", "Receipt Number", "Required Quantity", "Actual Quantity", "Flow Meter Reading", "Entry Time", "Logout Time"])
        self.history_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)  # Adjust column widths
        history_layout.addWidget(self.history_table)

        history_frame.setLayout(history_layout)
        notebook.addTab(history_frame, "History")

        self.load_history()

        notebook.addTab(operator_frame, "Manage Operators")
        notebook.addTab(port_frame, "Manage ports")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(notebook)
        self.setLayout(main_layout)

        logout_button = QtWidgets.QPushButton("Logout", self)
        logout_button.clicked.connect(self.logout_action)
        main_layout.addWidget(logout_button)

        self.auto_refresh()


    def update_port_settings(self):
        # Clear previous settings
        for i in reversed(range(self.dynamic_settings_layout.count())):
            self.dynamic_settings_layout.itemAt(i).widget().deleteLater()

        mode = self.add_port_mode_entry.currentText()

        if mode == "modbus":
            # Add modbus-specific fields
            self.baudrate_list = QtWidgets.QComboBox()
            self.baudrate_list.addItems(["9600", "19200", "38400", "57600", "115200"])
            self.frame_list = QtWidgets.QComboBox()
            self.frame_list.addItems(["SERIAL_8N1", "SERIAL_8N2", "SERIAL_8E1", "SERIAL_8O1"])
            self.endian_list = QtWidgets.QComboBox()
            self.endian_list.addItems(["Big Endian", "Little Endian"])

            self.slave_address_entry = QtWidgets.QLineEdit()
            self.slave_address_entry.setPlaceholderText("Slave Address")
            self.register_address_entry = QtWidgets.QLineEdit()
            self.register_address_entry.setPlaceholderText("Register Address")

            self.dynamic_settings_layout.addWidget(QtWidgets.QLabel("Baudrate:"))
            self.dynamic_settings_layout.addWidget(self.baudrate_list)
            self.dynamic_settings_layout.addWidget(QtWidgets.QLabel("Frame:"))
            self.dynamic_settings_layout.addWidget(self.frame_list)
            self.dynamic_settings_layout.addWidget(QtWidgets.QLabel("Endian:"))
            self.dynamic_settings_layout.addWidget(self.endian_list)
            self.dynamic_settings_layout.addWidget(self.slave_address_entry)
            self.dynamic_settings_layout.addWidget(self.register_address_entry)

        elif mode == "milli ampere":
            # Add milli ampere-specific fields
            self.min_entry = QtWidgets.QLineEdit()
            self.min_entry.setPlaceholderText("Min Value")
            self.max_entry = QtWidgets.QLineEdit()
            self.max_entry.setPlaceholderText("Max Value")
            self.resistor_value_entry = QtWidgets.QLineEdit()
            self.resistor_value_entry.setPlaceholderText("Resistor Value")

            self.dynamic_settings_layout.addWidget(self.min_entry)
            self.dynamic_settings_layout.addWidget(self.max_entry)
            self.dynamic_settings_layout.addWidget(self.resistor_value_entry)

        elif mode == "pulse":
            # Add pulse-specific fields
            self.liter_per_pulse_entry = QtWidgets.QLineEdit()
            self.liter_per_pulse_entry.setPlaceholderText("Liter per Pulse")

            self.dynamic_settings_layout.addWidget(self.liter_per_pulse_entry)


    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.center())
        self.showMaximized()  # Ensure the window is maximized

    def clear_fields(self):
        self.add_operator_name_entry.clear()
        self.add_operator_ID_entry.clear()
        self.add_operator_password_entry.clear()
        self.add_port_name_entry.clear()
        self.add_port_mode_entry.setCurrentIndex(0)

    def add_operator_action(self):
        operator_name = self.add_operator_name_entry.text()
        operator_ID = self.add_operator_ID_entry.text()
        operator_password = self.add_operator_password_entry.text()
        if operator_name and operator_password and operator_ID:
            result = add_operator(operator_name, operator_password, operator_ID)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_operators_action()
            self.clear_fields()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Both fields are required.")

    def remove_selected_operator_action(self):        
        selected_row = self.operator_table.currentRow()
        if selected_row != -1:
            operator_name = self.operator_table.item(selected_row, 0).text()

            result = remove_operator(operator_name)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_operators_action()
            self.clear_fields()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No operator selected.")

    def list_operators_action(self):
        operators = list_operators()
        self.operator_table.setRowCount(len(operators))
        for row_idx, operator in enumerate(operators):
            self.operator_table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(operator[0]))
            self.operator_table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(operator[2]))

    def add_port_action(self):
        port_name = self.add_port_name_entry.text()
        mode = self.add_port_mode_entry.currentText()
        if mode == "modbus":
            baudrate = self.baudrate_list.currentText()
            frame = self.frame_list.currentText()
            endian = self.endian_list.currentText()
            slave_address = self.slave_address_entry.text()
            register_address = self.register_address_entry.text()
            if port_name and baudrate and frame and endian and slave_address and register_address:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode,config=f"{baudrate},{frame},{endian},{slave_address},{register_address}")
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Port '{port_name}' already exists.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        elif mode == "milli ampere":
            min_value = self.min_entry.text()
            max_value = self.max_entry.text()
            resistor_value = self.resistor_value_entry.text()
            if port_name and min_value and max_value and resistor_value:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode, config=f"{min_value},{max_value},{resistor_value}")
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Port '{port_name}' already exists.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        elif mode == "pulse":
            liter_per_pulse = self.liter_per_pulse_entry.text()
            if port_name and liter_per_pulse:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode, config=liter_per_pulse)
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Port '{port_name}' already exists.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")

    def update_port_action(self):
        selected_row = self.ports_table.currentRow()
        if selected_row != -1:
            port_name = self.ports_table.item(selected_row, 0).text()
            mode = self.add_port_mode_entry.currentText()
            if mode == "modbus":
                baudrate = self.baudrate_list.currentText()
                frame = self.frame_list.currentText()
                endian = self.endian_list.currentText()
                slave_address = self.slave_address_entry.text()
                register_address = self.register_address_entry.text()
                if port_name and baudrate and frame and endian and slave_address and register_address:
                    result = update_port(port_name, mode, config=f"{baudrate},{frame},{endian},{slave_address},{register_address}")
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
            elif mode == "milli ampere":
                min_value = self.min_entry.text()
                max_value = self.max_entry.text()
                resistor_value = self.resistor_value_entry.text()
                if port_name and min_value and max_value and resistor_value:
                    result = update_port(port_name, mode, config=f"{min_value},{max_value},{resistor_value}")
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
            elif mode == "pulse":
                liter_per_pulse = self.liter_per_pulse_entry.text()
                if port_name and liter_per_pulse:
                    result = update_port(port_name, mode, config=liter_per_pulse)
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    self.clear_fields()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")

    def remove_selected_port_action(self):
        selected_row = self.ports_table.currentRow()
        if selected_row != -1:
            port_name = self.ports_table.item(selected_row, 0).text()
            result = remove_port(port_name)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_ports_action()
            self.clear_fields()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No port selected.")

    def list_ports_action(self):
        ports = get_ports()
        self.ports_table.setRowCount(len(ports))
        for row_idx, port in enumerate(ports):
            for col_idx, data in enumerate(port):
                self.ports_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(data)))
        self.ports_table.itemSelectionChanged.connect(self.fill_port_details)

    def fill_port_details(self):
        selected_row = self.ports_table.currentRow()
        if selected_row != -1:
            self.add_port_name_entry.setText(self.ports_table.item(selected_row, 0).text())
            self.add_port_mode_entry.setCurrentText(self.ports_table.item(selected_row, 1).text())
        else:
            self.clear_fields()

    def load_history(self):
        logs = get_logs()
        self.history_table.setRowCount(len(logs))
        for row_idx, log in enumerate(logs):
            for col_idx, data in enumerate(log):
                self.history_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(data)))

    def auto_refresh(self):
        self.list_operators_action()
        self.list_ports_action()
        QtCore.QTimer.singleShot(5000, self.auto_refresh)  

    def logout_action(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

    def update_selected_operator_action(self):
        selected_row = self.operator_table.currentRow()
        if selected_row != -1:
            operator_name = self.operator_table.item(selected_row, 0).text()
            operator_id = self.operator_table.item(selected_row, 1).text()
            new_name = self.add_operator_name_entry.text()
            new_id = self.add_operator_ID_entry.text()
            new_password = self.add_operator_password_entry.text()
            if new_name and new_id and new_password:
                result = update_operator(operator_name, operator_id, new_name, new_id, new_password)
                QtWidgets.QMessageBox.information(self, "Result", result)
                self.list_operators_action()
                self.clear_fields()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No operator selected.")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    admin_interface = AdminInterface()
    admin_interface.show()
    sys.exit(app.exec())


