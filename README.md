# Water Filling System

This project is a water filling system that provides interfaces for operators and administrators. The operator interface is used to perform specific tasks such as filling trucks with water, while the admin interface is used to manage operator accounts and trucks.

## Project Structure

```
water-filling-system-v2/
├── esp_code/
│   ├── file1.ino
│   ├── file2.ino
│   └── ...
├── src/
│   ├── admin_interface.py
│   ├── database.py
│   ├── main.py
│   ├── operator_interface.py
│   └── utils.py
├── requirements.txt
├── setup_environment.bat
└── README.md
```

## Features

- Operator interface for performing water filling tasks
- Admin interface for managing operators and trucks
- MQTT communication for real-time updates
- Barcode scanning for quick truck selection
- ESP code for hardware integration

## Requirements

- Python 3.x
- PyQt6
- paho-mqtt
- pyodbc

## Installation

### Setting Up the Project on a PC

1. **Clone the repository:**

   ```sh
   git clone https://github.com/Abdomohamed950/filling_system.git
   cd filling_system
   ```

2. **Install the required dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Set up the server database:**

   - Ensure you have the ODBC Driver 17 for SQL Server installed. You can download it from [Microsoft's official website](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).
   - Configure the database connection in `src/database.py` with the correct server, database, username, and password.

4. **Run the application:**

   ```sh
   python src/main.py
   ```

### Server Database Requirements

1. **Install the ODBC Driver 17 for SQL Server:**

   - Download and install the driver from [Microsoft's official website](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

2. **Configure the database connection:**

   - Open `src/database.py` and update the `create_server_connection` function with the correct server, database, username, and password.

   ```python
   def create_server_connection():    
       connection = pyodbc.connect(
           "DRIVER={ODBC Driver 17 for SQL Server};"
           "SERVER=your_server_name;"  
           "DATABASE=your_database_name;"      
           "UID=your_username;"        
           "PWD=your_password;"        
       )
       return connection
   ```

## Usage

1. **Run the application:**

   ```sh
   python src/main.py
   ```

2. **Enter the admin password to access the admin interface or the operator password to access the operator interface.**

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you'd like to add.