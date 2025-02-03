from PyQt6.QtWidgets import QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PyQt6 import QtGui, QtCore

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 300, 200)
        self.center()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        # Add the logo image
        logo_label = QLabel(self)
        logo_pixmap = QtGui.QPixmap("src/logo.png")
        logo_pixmap = logo_pixmap.scaled(250, 250, QtCore.Qt.AspectRatioMode.KeepAspectRatio)  # Resize the logo
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

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
        from authenticate import authenticate  # Import authenticate function here to avoid circular import
        password = self.password_entry.text()
        authenticate(password, self)
