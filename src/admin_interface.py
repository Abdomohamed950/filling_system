from PyQt6 import QtCore, QtWidgets
from database import create_table, add_operator, remove_operator, list_operators, is_password_unique, add_port, remove_port, get_ports, get_logs, update_port, is_port_name_unique, update_operator, get_channel_entries, update_channel_entry, get_channel_entry
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

        scroll_area_operators = QtWidgets.QScrollArea()
        scroll_area_operators.setWidgetResizable(True)
        scroll_content_operators = QtWidgets.QWidget()
        self.operator_cards_layout = QtWidgets.QGridLayout(scroll_content_operators)
        self.operator_cards_layout.setSpacing(30)  # Add padding between cards
        scroll_area_operators.setWidget(scroll_content_operators)
        operator_layout.addWidget(scroll_area_operators)

        operator_frame.setLayout(operator_layout)

        notebook.addTab(operator_frame, "Manage Operators")

        # Tab for managing ports
        port_frame = QtWidgets.QWidget()
        port_layout = QtWidgets.QVBoxLayout(port_frame)

        scroll_area_ports = QtWidgets.QScrollArea()
        scroll_area_ports.setWidgetResizable(True)
        scroll_content_ports = QtWidgets.QWidget()
        self.port_cards_layout = QtWidgets.QGridLayout(scroll_content_ports)
        self.port_cards_layout.setSpacing(30)  # Add padding between cards
        scroll_area_ports.setWidget(scroll_content_ports)
        port_layout.addWidget(scroll_area_ports)

        port_frame.setLayout(port_layout)

        notebook.addTab(port_frame, "Manage Ports")

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

        # Tab for channels
        channel_frame = QtWidgets.QWidget()
        channel_layout = QtWidgets.QVBoxLayout(channel_frame)

        scroll_area_channels = QtWidgets.QScrollArea()
        scroll_area_channels.setWidgetResizable(True)
        scroll_content_channels = QtWidgets.QWidget()
        self.channel_cards_layout = QtWidgets.QGridLayout(scroll_content_channels)
        self.channel_cards_layout.setSpacing(30)  # Add padding between cards
        scroll_area_channels.setWidget(scroll_content_channels)
        channel_layout.addWidget(scroll_area_channels)

        channel_frame.setLayout(channel_layout)

        notebook.addTab(channel_frame, "Channels")

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
            self.frame_list.addItems(["SERIAL_8N1", "SERIAL_8N2", "SERIAL_8E1", "SERIAL_8E2", "SERIAL_8O1", "SERIAL_8O2"])
            self.endian_list = QtWidgets.QComboBox()
            self.endian_list.addItems(["AABBCCDD", "DDCCBBAA"])

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
        # Ensure these fields are initialized before clearing
        if hasattr(self, 'add_operator_name_entry'):
            self.add_operator_name_entry.clear()
        if hasattr(self, 'add_operator_ID_entry'):
            self.add_operator_ID_entry.clear()
        if hasattr(self, 'add_operator_password_entry'):
            self.add_operator_password_entry.clear()
        if hasattr(self, 'add_port_name_entry'):
            self.add_port_name_entry.clear()
        if hasattr(self, 'add_port_mode_entry'):
            self.add_port_mode_entry.setCurrentIndex(0)

    def add_operator_action(self, dialog, operator_name, operator_id, operator_password):
        if operator_name and operator_password and operator_id:
            result = add_operator(operator_name, operator_password, operator_id)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_operators_action()
            dialog.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")

    def remove_operator_action(self, operator_name):
        result = remove_operator(operator_name)
        QtWidgets.QMessageBox.information(self, "Result", result)
        self.list_operators_action()
        self.clear_fields()

    def list_operators_action(self):
        operators = list_operators()
        for i in reversed(range(self.operator_cards_layout.count())):
            self.operator_cards_layout.itemAt(i).widget().deleteLater()

        for idx, operator in enumerate(operators):
            operator_name, operator_id = operator[0], operator[2]
            card = QtWidgets.QGroupBox(operator_name)
            card.setFixedSize(300, 300)  # Set fixed size for each card
            card_layout = QtWidgets.QVBoxLayout()

            id_label = QtWidgets.QLabel(f"ID: {operator_id}")

            edit_button = QtWidgets.QPushButton("Edit")
            edit_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView))
            edit_button.clicked.connect(lambda _, on=operator_name, oid=operator_id: self.edit_operator_action(on, oid))

            remove_button = QtWidgets.QPushButton("Remove")
            remove_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
            remove_button.clicked.connect(lambda _, on=operator_name: self.remove_operator_action(on))

            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addWidget(edit_button)
            button_layout.addWidget(remove_button)

            card_layout.addWidget(id_label)
            card_layout.addLayout(button_layout)

            card.setLayout(card_layout)
            self.operator_cards_layout.addWidget(card, idx // 5, idx % 5)  # Arrange cards in a grid with 5 cards per row

        # Add a card for adding a new operator
        add_card = QtWidgets.QGroupBox("Add New Operator")
        add_card.setFixedSize(300, 300)  # Set fixed size for the add card
        add_card_layout = QtWidgets.QVBoxLayout()
        add_button = QtWidgets.QPushButton("Add Operator")
        add_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogNewFolder))
        add_button.clicked.connect(self.show_add_operator_dialog)
        add_card_layout.addWidget(add_button)
        add_card.setLayout(add_card_layout)
        self.operator_cards_layout.addWidget(add_card, len(operators) // 5, len(operators) % 5)  # Place the add card in the next available slot

    def show_add_operator_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Operator")

        layout = QtWidgets.QVBoxLayout(dialog)

        operator_name_label = QtWidgets.QLabel("Operator Name:")
        operator_name_entry = QtWidgets.QLineEdit()

        operator_id_label = QtWidgets.QLabel("Operator ID:")
        operator_id_entry = QtWidgets.QLineEdit()

        operator_password_label = QtWidgets.QLabel("Operator Password:")
        operator_password_entry = QtWidgets.QLineEdit()
        operator_password_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(lambda: self.add_operator_action(dialog, operator_name_entry.text(), operator_id_entry.text(), operator_password_entry.text()))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        layout.addWidget(operator_name_label)
        layout.addWidget(operator_name_entry)
        layout.addWidget(operator_id_label)
        layout.addWidget(operator_id_entry)
        layout.addWidget(operator_password_label)
        layout.addWidget(operator_password_entry)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        dialog.exec()

    def edit_operator_action(self, operator_name, operator_id):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Edit Operator: {operator_name}")

        layout = QtWidgets.QVBoxLayout(dialog)

        operator_name_label = QtWidgets.QLabel("Operator Name:")
        operator_name_entry = QtWidgets.QLineEdit(operator_name)

        operator_id_label = QtWidgets.QLabel("Operator ID:")
        operator_id_entry = QtWidgets.QLineEdit(operator_id)

        operator_password_label = QtWidgets.QLabel("Operator Password:")
        operator_password_entry = QtWidgets.QLineEdit()
        operator_password_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(lambda: self.update_operator_action(dialog, operator_name, operator_id, operator_name_entry.text(), operator_id_entry.text(), operator_password_entry.text()))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        layout.addWidget(operator_name_label)
        layout.addWidget(operator_name_entry)
        layout.addWidget(operator_id_label)
        layout.addWidget(operator_id_entry)
        layout.addWidget(operator_password_label)
        layout.addWidget(operator_password_entry)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        dialog.exec()

    def update_operator_action(self, dialog, old_name, old_id, new_name, new_id, new_password):
        if new_name and new_id and new_password:
            result = update_operator(old_name, old_id, new_name, new_id, new_password)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_operators_action()
            dialog.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")

    def add_port_action(self, dialog, port_name, mode, config):
        if mode == "modbus":
            baudrate, frame, endian, slave_address, register_address = config.split(',')
            if port_name and baudrate and frame and endian and slave_address and register_address:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode, config)
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Port '{port_name}' already exists.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        elif mode == "milli ampere":
            min_value, max_value, resistor_value = config.split(',')
            if port_name and min_value and max_value and resistor_value:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode, config)
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    dialog.accept()
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Port '{port_name}' already exists.")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        elif mode == "pulse":
            liter_per_pulse = config
            if port_name and liter_per_pulse:
                if is_port_name_unique(port_name):
                    result = add_port(port_name, mode, config)
                    QtWidgets.QMessageBox.information(self, "Result", result)
                    self.list_ports_action()
                    dialog.accept()
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

    def list_ports_action(self):
        ports = get_ports()
        for i in reversed(range(self.port_cards_layout.count())):
            self.port_cards_layout.itemAt(i).widget().deleteLater()

        for idx, port in enumerate(ports):
            port_name, mode, config = port
            card = QtWidgets.QGroupBox(port_name)
            card.setFixedSize(300, 300)  # Set fixed size for each card
            card_layout = QtWidgets.QVBoxLayout()

            mode_label = QtWidgets.QLabel(f"Mode: {mode}")
            config_label = QtWidgets.QLabel(f"Configuration: {config}")

            edit_button = QtWidgets.QPushButton("Edit")
            edit_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView))
            edit_button.clicked.connect(lambda _, pn=port_name, m=mode, c=config: self.edit_port_action(pn, m, c))

            remove_button = QtWidgets.QPushButton("Remove")
            remove_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
            remove_button.clicked.connect(lambda _, pn=port_name: self.remove_port_action(pn))

            button_layout = QtWidgets.QHBoxLayout()
            button_layout.addWidget(edit_button)
            button_layout.addWidget(remove_button)

            card_layout.addWidget(mode_label)
            card_layout.addWidget(config_label)
            card_layout.addLayout(button_layout)

            card.setLayout(card_layout)
            self.port_cards_layout.addWidget(card, idx // 5, idx % 5)  # Arrange cards in a grid with 5 cards per row

        # Add a card for adding a new port
        add_card = QtWidgets.QGroupBox("Add New Port")
        add_card.setFixedSize(300, 300)  # Set fixed size for the add card
        add_card_layout = QtWidgets.QVBoxLayout()
        add_button = QtWidgets.QPushButton("Add Port")
        add_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogNewFolder))
        add_button.clicked.connect(self.show_add_port_dialog)
        add_card_layout.addWidget(add_button)
        add_card.setLayout(add_card_layout)
        self.port_cards_layout.addWidget(add_card, len(ports) // 5, len(ports) % 5)  # Place the add card in the next available slot

    def show_add_port_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add New Port")

        layout = QtWidgets.QVBoxLayout(dialog)

        port_name_label = QtWidgets.QLabel("Port Name:")
        port_name_entry = QtWidgets.QLineEdit()

        mode_label = QtWidgets.QLabel("Mode:")
        mode_entry = QtWidgets.QComboBox()
        mode_entry.addItems(["modbus", "milli ampere", "pulse"])
        mode_entry.currentIndexChanged.connect(lambda: self.update_dialog_settings(dialog, mode_entry.currentText(), ""))

        self.dialog_dynamic_settings_layout = QtWidgets.QVBoxLayout()

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(lambda: self.add_port_action(dialog, port_name_entry.text(), mode_entry.currentText(), self.get_dialog_config()))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        layout.addWidget(port_name_label)
        layout.addWidget(port_name_entry)
        layout.addWidget(mode_label)
        layout.addWidget(mode_entry)
        layout.addLayout(self.dialog_dynamic_settings_layout)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        self.update_dialog_settings(dialog, mode_entry.currentText(), "")
        dialog.exec()

    def edit_port_action(self, port_name, mode, config):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Edit Port: {port_name}")

        layout = QtWidgets.QVBoxLayout(dialog)

        port_name_label = QtWidgets.QLabel("Port Name:")
        port_name_entry = QtWidgets.QLineEdit(port_name)
        port_name_entry.setReadOnly(True)

        mode_label = QtWidgets.QLabel("Mode:")
        mode_entry = QtWidgets.QComboBox()
        mode_entry.addItems(["modbus", "milli ampere", "pulse"])
        mode_entry.setCurrentText(mode)
        mode_entry.currentIndexChanged.connect(lambda: self.update_dialog_settings(dialog, mode_entry.currentText(), ""))

        self.dialog_dynamic_settings_layout = QtWidgets.QVBoxLayout()

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_port_changes(dialog, port_name, mode_entry.currentText(), self.get_dialog_config()))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        layout.addWidget(port_name_label)
        layout.addWidget(port_name_entry)
        layout.addWidget(mode_label)
        layout.addWidget(mode_entry)
        layout.addLayout(self.dialog_dynamic_settings_layout)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        self.update_dialog_settings(dialog, mode, config)
        dialog.exec()

    def update_dialog_settings(self, dialog, mode, config):
        for i in reversed(range(self.dialog_dynamic_settings_layout.count())):
            self.dialog_dynamic_settings_layout.itemAt(i).widget().deleteLater()

        config_values = config.split(',') if config else []

        if mode == "modbus":
            baudrate_list = QtWidgets.QComboBox()
            baudrate_list.addItems(["9600", "19200", "38400", "57600", "115200"])
            baudrate_list.setCurrentText(config_values[0] if config_values else "")

            frame_list = QtWidgets.QComboBox()
            frame_list.addItems(["SERIAL_8N1", "SERIAL_8N2", "SERIAL_8E1", "SERIAL_8E2", "SERIAL_8O1", "SERIAL_8O2"])
            frame_list.setCurrentText(config_values[1] if config_values else "")

            endian_list = QtWidgets.QComboBox()
            endian_list.addItems(["AABBCCDD", "DDCCBBAA"])
            endian_list.setCurrentText(config_values[2] if config_values else "")

            slave_address_entry = QtWidgets.QLineEdit(config_values[3] if len(config_values) > 3 else "")
            slave_address_entry.setPlaceholderText("Slave Address")

            register_address_entry = QtWidgets.QLineEdit(config_values[4] if len(config_values) > 4 else "")
            register_address_entry.setPlaceholderText("Register Address")

            self.dialog_dynamic_settings_layout.addWidget(QtWidgets.QLabel("Baudrate:"))
            self.dialog_dynamic_settings_layout.addWidget(baudrate_list)
            self.dialog_dynamic_settings_layout.addWidget(QtWidgets.QLabel("Frame:"))
            self.dialog_dynamic_settings_layout.addWidget(frame_list)
            self.dialog_dynamic_settings_layout.addWidget(QtWidgets.QLabel("Endian:"))
            self.dialog_dynamic_settings_layout.addWidget(endian_list)
            self.dialog_dynamic_settings_layout.addWidget(slave_address_entry)
            self.dialog_dynamic_settings_layout.addWidget(register_address_entry)

        elif mode == "milli ampere":
            min_entry = QtWidgets.QLineEdit(config_values[0] if len(config_values) > 0 else "")
            min_entry.setPlaceholderText("Min Value")

            max_entry = QtWidgets.QLineEdit(config_values[1] if len(config_values) > 1 else "")
            max_entry.setPlaceholderText("Max Value")

            resistor_value_entry = QtWidgets.QLineEdit(config_values[2] if len(config_values) > 2 else "")
            resistor_value_entry.setPlaceholderText("Resistor Value")

            self.dialog_dynamic_settings_layout.addWidget(min_entry)
            self.dialog_dynamic_settings_layout.addWidget(max_entry)
            self.dialog_dynamic_settings_layout.addWidget(resistor_value_entry)

        elif mode == "pulse":
            liter_per_pulse_entry = QtWidgets.QLineEdit(config_values[0] if len(config_values) > 0 else "")
            liter_per_pulse_entry.setPlaceholderText("Liter per Pulse")

            self.dialog_dynamic_settings_layout.addWidget(liter_per_pulse_entry)

    def get_dialog_config(self):
        config = []
        for i in range(self.dialog_dynamic_settings_layout.count()):
            widget = self.dialog_dynamic_settings_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QLineEdit):
                config.append(widget.text())
            elif isinstance(widget, QtWidgets.QComboBox):
                config.append(widget.currentText())
        return ','.join(config)

    def save_port_changes(self, dialog, port_name, mode, config):
        result = update_port(port_name, mode, config)
        QtWidgets.QMessageBox.information(self, "Result", result)
        self.list_ports_action()
        dialog.accept()

    def remove_port_action(self, port_name):
        result = remove_port(port_name)
        QtWidgets.QMessageBox.information(self, "Result", result)
        self.list_ports_action()
        self.clear_fields()

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
        self.list_channels_action() 
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

    def list_channels_action(self):
        ports = get_ports()
        channel_entries = get_channel_entries()
        for i in reversed(range(self.channel_cards_layout.count())):
            self.channel_cards_layout.itemAt(i).widget().deleteLater()

        for idx, port in enumerate(ports):
            port_name, mode, config = port
            card = QtWidgets.QGroupBox(port_name)
            card.setFixedSize(300, 300)  # Set fixed size for each card
            card_layout = QtWidgets.QVBoxLayout()
            
            lis = get_channel_entry(port_name)
            if lis:
                truck_number_label = QtWidgets.QLabel(f"Truck Number: {lis[0]}")
                operator_id_label = QtWidgets.QLabel(f"Operator Id: {lis[1]}")
                receipt_number_label = QtWidgets.QLabel(f"Receipt Number: {lis[2]}")
                required_quantity_label = QtWidgets.QLabel(f"Required Quantity: {lis[3]}")
                actual_quantity_label = QtWidgets.QLabel(f"Actual Quantity: {lis[4]}")
                flowmeter_label = QtWidgets.QLabel(f"Flowmeter: {lis[5]}")
            else:
                truck_number_label = QtWidgets.QLabel("Truck Number: N/A")
                operator_id_label = QtWidgets.QLabel("Operator Id: N/A")
                receipt_number_label = QtWidgets.QLabel("Receipt Number: N/A")
                required_quantity_label = QtWidgets.QLabel("Required Quantity: N/A")
                actual_quantity_label = QtWidgets.QLabel("Actual Quantity: N/A")
                flowmeter_label = QtWidgets.QLabel("Flowmeter: N/A")

            edit_button = QtWidgets.QPushButton("Edit")
            edit_button.clicked.connect(lambda _, pn=port_name: self.show_edit_channel_dialog(pn))

            card_layout.addWidget(truck_number_label)
            card_layout.addWidget(operator_id_label)
            card_layout.addWidget(receipt_number_label)
            card_layout.addWidget(required_quantity_label)
            card_layout.addWidget(actual_quantity_label)
            card_layout.addWidget(flowmeter_label)
            card_layout.addWidget(edit_button)

            card.setLayout(card_layout)
            self.channel_cards_layout.addWidget(card, idx // 5, idx % 5)  # Arrange cards in a grid with 5 cards per row

    def show_edit_channel_dialog(self, port_name):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Edit Channel: {port_name}")

        layout = QtWidgets.QVBoxLayout(dialog)

        channel_entry = get_channel_entry(port_name)

        truck_number_label = QtWidgets.QLabel("Truck Number:")
        truck_number_entry = QtWidgets.QLineEdit(channel_entry[0] if channel_entry else "")

        operator_id_label = QtWidgets.QLabel("Operator ID:")
        operator_id_entry = QtWidgets.QLineEdit(channel_entry[1] if channel_entry else "")

        receipt_number_label = QtWidgets.QLabel("Receipt Number:")
        receipt_number_entry = QtWidgets.QLineEdit(channel_entry[2] if channel_entry else "")

        required_quantity_label = QtWidgets.QLabel("Required Quantity:")
        required_quantity_entry = QtWidgets.QLineEdit(channel_entry[3] if channel_entry else "")

        actual_quantity_label = QtWidgets.QLabel("Actual Quantity:")
        actual_quantity_entry = QtWidgets.QLineEdit(channel_entry[4] if channel_entry else "")

        flowmeter_label = QtWidgets.QLabel("Flowmeter:")
        flowmeter_entry = QtWidgets.QLineEdit(channel_entry[5] if channel_entry else "")

        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_channel_changes(dialog, port_name, truck_number_entry.text(), operator_id_entry.text(), receipt_number_entry.text(), required_quantity_entry.text(), actual_quantity_entry.text(), flowmeter_entry.text()))

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)

        layout.addWidget(truck_number_label)
        layout.addWidget(truck_number_entry)
        layout.addWidget(operator_id_label)
        layout.addWidget(operator_id_entry)
        layout.addWidget(receipt_number_label)
        layout.addWidget(receipt_number_entry)
        layout.addWidget(required_quantity_label)
        layout.addWidget(required_quantity_entry)
        layout.addWidget(actual_quantity_label)
        layout.addWidget(actual_quantity_entry)
        layout.addWidget(flowmeter_label)
        layout.addWidget(flowmeter_entry)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        dialog.setLayout(layout)
        dialog.exec()

    def save_channel_changes(self, dialog, port_name,  truck_number, operator_id, receipt_number, required_quantity, actual_quantity, flowmeter):
        update_channel_entry(port_name, flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity)
        QtWidgets.QMessageBox.information(self, "Result", "Channel entry updated successfully.")
        self.list_channels_action()
        dialog.accept()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    admin_interface = AdminInterface()
    admin_interface.show()
    sys.exit(app.exec())
