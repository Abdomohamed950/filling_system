from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from admin_interface import AdminInterface
from operator_interface import OperatorInterface
from database import get_operator_name_by_password

ADMIN_PASSWORD = "admin"

def authenticate(password, window):
    if password == ADMIN_PASSWORD:
        print("Admin password entered correctly.")
        window.close()  # إغلاق نافذة تسجيل الدخول
        print("Creating AdminInterface instance.")
        window.admin_interface = AdminInterface()  # إنشاء واجهة المدير وتخزينها في النافذة
        print("Showing AdminInterface.")
        window.admin_interface.show()  # عرض واجهة المدير
    else:
        operator_name = get_operator_name_by_password(password)
        if operator_name:
            print(f"Operator {operator_name} authenticated successfully.")
            window.close()  # إغلاق نافذة تسجيل الدخول
            window.operator_interface = OperatorInterface(operator_name)  # إنشاء واجهة المشغل وتخزينها في النافذة
            window.operator_interface.show()  # عرض واجهة المشغل
        else:
            print("Invalid password entered.")
            QMessageBox.critical(window, "Error", "Invalid password. Please try again.")

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 200)
        self.center()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.label = QLabel("Enter Password:")
        layout.addWidget(self.label)

        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_entry)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.central_widget.setLayout(layout)

        self.password_entry.returnPressed.connect(self.login)

    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def login(self):
        password = self.password_entry.text()
        authenticate(password, self)

if __name__ == "__main__":
    app = QApplication([])
    login_window = LoginWindow()
    login_window.show()
    app.exec()
