from PyQt6.QtWidgets import QApplication
from login_window import LoginWindow  # Import LoginWindow from the new file

if __name__ == "__main__":
    app = QApplication([])
    login_window = LoginWindow()
    login_window.show()
    app.exec()
