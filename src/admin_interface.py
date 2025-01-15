from PyQt6 import QtCore, QtWidgets
from database import create_table, add_operator, remove_operator, list_operators, is_password_unique, add_truck, remove_truck, get_trucks, get_logs

class AdminInterface(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        create_table()  
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Admin Interface")
        self.setGeometry(100, 100, 500, 400)
        self.center()

        notebook = QtWidgets.QTabWidget(self)

        # Tab for adding operator
        add_frame = QtWidgets.QWidget()
        add_layout = QtWidgets.QVBoxLayout()

        add_operator_name_label = QtWidgets.QLabel("Operator Name:", self)
        self.add_operator_name_entry = QtWidgets.QLineEdit(self)

        add_operator_password_label = QtWidgets.QLabel("Operator Password:", self)
        self.add_operator_password_entry = QtWidgets.QLineEdit(self)
        self.add_operator_password_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        add_button = QtWidgets.QPushButton("Add", self)
        add_button.clicked.connect(self.add_operator_action)

        add_layout.addWidget(add_operator_name_label)
        add_layout.addWidget(self.add_operator_name_entry)
        add_layout.addWidget(add_operator_password_label)
        add_layout.addWidget(self.add_operator_password_entry)
        add_layout.addWidget(add_button)
        add_frame.setLayout(add_layout)

        # Tab for listing and removing operators
        list_remove_frame = QtWidgets.QWidget()
        list_remove_layout = QtWidgets.QVBoxLayout()

        self.operators_listbox = QtWidgets.QListWidget(self)

        remove_button = QtWidgets.QPushButton("Remove Selected", self)
        remove_button.clicked.connect(self.remove_selected_operator_action)

        list_remove_layout.addWidget(self.operators_listbox)
        list_remove_layout.addWidget(remove_button)
        list_remove_frame.setLayout(list_remove_layout)

        # Tab for adding and removing trucks
        truck_frame = QtWidgets.QWidget()
        truck_layout = QtWidgets.QVBoxLayout()

        add_truck_name_label = QtWidgets.QLabel("Truck Name:", self)
        self.add_truck_name_entry = QtWidgets.QLineEdit(self)

        add_truck_baudrate_label = QtWidgets.QLabel("Baudrate:", self)
        self.add_truck_baudrate_entry = QtWidgets.QLineEdit(self)

        add_truck_mode_label = QtWidgets.QLabel("Mode:", self)
        self.add_truck_mode_entry = QtWidgets.QLineEdit(self)

        add_truck_button = QtWidgets.QPushButton("Add Truck", self)
        add_truck_button.clicked.connect(self.add_truck_action)

        self.trucks_listbox = QtWidgets.QListWidget(self)

        remove_truck_button = QtWidgets.QPushButton("Remove Selected Truck", self)
        remove_truck_button.clicked.connect(self.remove_selected_truck_action)

        truck_layout.addWidget(add_truck_name_label)
        truck_layout.addWidget(self.add_truck_name_entry)
        truck_layout.addWidget(add_truck_baudrate_label)
        truck_layout.addWidget(self.add_truck_baudrate_entry)
        truck_layout.addWidget(add_truck_mode_label)
        truck_layout.addWidget(self.add_truck_mode_entry)
        truck_layout.addWidget(add_truck_button)
        self.trucks_table = QtWidgets.QTableWidget()
        self.trucks_table.setColumnCount(3)
        self.trucks_table.setHorizontalHeaderLabels(["Truck Name", "Baudrate", "Mode"])
        truck_layout.addWidget(self.trucks_table)
        truck_layout.addWidget(remove_truck_button)
        truck_frame.setLayout(truck_layout)

        # Tab for history
        history_frame = QtWidgets.QWidget()
        history_layout = QtWidgets.QVBoxLayout()

        self.history_table = QtWidgets.QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Operator Name", "Truck Name", "Quantity", "Timestamp"])
        history_layout.addWidget(self.history_table)

        history_frame.setLayout(history_layout)
        notebook.addTab(history_frame, "History")

        self.load_history()

        notebook.addTab(add_frame, "Add Operator")
        notebook.addTab(list_remove_frame, "List/Remove Operators")
        notebook.addTab(truck_frame, "Manage Trucks")

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(notebook)
        self.setLayout(main_layout)

        self.auto_refresh()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.center())


    def add_operator_action(self):
        operator_name = self.add_operator_name_entry.text()
        operator_password = self.add_operator_password_entry.text()
        if operator_name and operator_password:
            result = add_operator(operator_name, operator_password)
            QtWidgets.QMessageBox.information(self, "Result", result)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Both fields are required.")

    def remove_selected_operator_action(self):
        selected_operator = self.operators_listbox.currentItem()
        if selected_operator:
            result = remove_operator(selected_operator.text())
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_operators_action()
           

    def list_operators_action(self):
        operators = list_operators()
        self.operators_listbox.clear()
        if isinstance(operators, str):
            self.operators_listbox.addItem(operators)
        else:
            for operator in operators:
                self.operators_listbox.addItem(operator)

    def add_truck_action(self):
        truck_name = self.add_truck_name_entry.text()
        baudrate = self.add_truck_baudrate_entry.text()
        mode = self.add_truck_mode_entry.text()
        if truck_name and baudrate and mode:
            result = add_truck(truck_name, baudrate, mode)
            QtWidgets.QMessageBox.information(self, "Result", result)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "All fields are required.")
        self.list_trucks_action()

    def remove_selected_truck_action(self):
        selected_row = self.trucks_table.currentRow()
        if selected_row != -1:
            truck_name = self.trucks_table.item(selected_row, 0).text()
            result = remove_truck(truck_name)
            QtWidgets.QMessageBox.information(self, "Result", result)
            self.list_trucks_action()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No truck selected.")

    def list_trucks_action(self):
        trucks = get_trucks()
        self.trucks_table.setRowCount(len(trucks))
        for row_idx, truck in enumerate(trucks):
            for col_idx, data in enumerate(truck):
                self.trucks_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(data)))

    def load_history(self):
        logs = get_logs()
        self.history_table.setRowCount(len(logs))
        for row_idx, log in enumerate(logs):
            for col_idx, data in enumerate(log):
                self.history_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(data)))

    def auto_refresh(self):
        self.list_operators_action()
        self.list_trucks_action()
        QtCore.QTimer.singleShot(5000, self.auto_refresh)  

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    admin_interface = AdminInterface()
    admin_interface.show()
    sys.exit(app.exec())
