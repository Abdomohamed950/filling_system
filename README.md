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

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/Abdomohamed950/filling_system.git
   cd filling_system
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python src/main.py
   ```

2. Enter the admin password to access the admin interface or the operator password to access the operator interface.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you'd like to add.