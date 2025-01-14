# Water Filling System

This project is a water filling system that provides interfaces for operators and administrators. The operator interface is used to perform specific tasks such as filling trucks with water, while the admin interface is used to manage operator accounts and trucks.

## Project Structure

```
water-fillin-system
├── src
│   ├── admin_interface.py      # Contains AdminInterface class for admin functionalities
│   ├── operator_interface.py    # Contains OperatorInterface class for operator functionalities
│   ├── main.py                  # Entry point of the application
│   └── utils.py                 # Utility functions for password validation and operator management
├── requirements.txt             # Lists dependencies required for the project
└── README.md                    # Documentation for the project
```

## Features

- Operator interface for performing water filling tasks
- Admin interface for managing operators and trucks
- MQTT communication for real-time updates
- Barcode scanning for quick truck selection

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