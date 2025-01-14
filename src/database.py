import sqlite3

def create_connection():
    conn = sqlite3.connect('water_filling_system.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS operators (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL UNIQUE
                      )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 operator_name TEXT,
                 truck_name TEXT,
                 quantity INTEGER,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_operator(operator_name, operator_password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO operators (name, password) VALUES (?, ?)", (operator_name, operator_password))
        conn.commit()
        return "Operator added successfully."
    except sqlite3.IntegrityError:
        return f"Operator '{operator_name}' already exists."
    finally:
        conn.close()

def remove_operator(operator_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operators WHERE name=?", (operator_name,))
    conn.commit()
    conn.close()
    return "Operator removed successfully."

def list_operators():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM operators")
    operators = cursor.fetchall()
    conn.close()
    return [operator[0] for operator in operators]

def get_operator_password(name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM operators WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_operator_name_by_password(password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM operators WHERE password = ?", (password,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def is_operator_unique(operator_name, operator_password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operators WHERE name=? OR password=?", (operator_name, operator_password))
    result = cursor.fetchone()
    conn.close()
    return result is None

def is_password_unique(operator_password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operators WHERE password=?", (operator_password,))
    result = cursor.fetchone()
    conn.close()
    return result is None

def add_truck(truck_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trucks (name) VALUES (?)", (truck_name,))
    conn.commit()
    conn.close()
    return "Truck added successfully."

def remove_truck(truck_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trucks WHERE name=?", (truck_name,))
    conn.commit()
    conn.close()
    return "Truck removed successfully."

def list_trucks():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM trucks")
    trucks = cursor.fetchall()
    conn.close()
    return [truck[0] for truck in trucks]

def log_action(operator_name, truck_name, quantity):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO logs (operator_name, truck_name, quantity)
                 VALUES (?, ?, ?)''', (operator_name, truck_name, quantity))
    conn.commit()
    conn.close()

def get_logs():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT operator_name, truck_name, quantity, timestamp FROM logs')
    logs = cursor.fetchall()
    conn.close()
    return logs