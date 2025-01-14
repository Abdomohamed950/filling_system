# Water Fillin System

This project is a water filling system that provides an admin interface for managing operators and an operator interface for performing specific tasks. The application prompts for a password upon startup, allowing access to either the admin or operator functionalities based on the credentials provided.

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

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd water-fillin-system
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

## Features

- Admin Interface:
  - Add or remove operators.
  - Manage operator accounts.

- Operator Interface:
  - Perform tasks specific to operators.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or features you'd like to add.