from PyQt6.QtWidgets import QMessageBox
from admin_interface import AdminInterface
from operator_interface import OperatorInterface
from database import get_operator_name_by_password

ADMIN_PASSWORD = "admin"

def authenticate(password, window):
    if password == ADMIN_PASSWORD:
        print("Admin password entered correctly.")
        window.close() 
        print("Creating AdminInterface instance.")
        window.admin_interface = AdminInterface()  
        print("Showing AdminInterface.")
        window.admin_interface.show()  
    else:
        operator_name = get_operator_name_by_password(password)
        if operator_name:
            print(f"Operator {operator_name} authenticated successfully.")
            window.close()  
            window.operator_interface = OperatorInterface(operator_name)  
            window.operator_interface.show()  
        else:
            print("Invalid password entered.")
            QMessageBox.critical(window, "Error", "Invalid password. Please try again.")
