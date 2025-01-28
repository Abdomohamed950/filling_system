import sqlite3
import pyodbc

def create_server_connection():    
    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=197.134.251.84\\HYPERSCADA,1433;"  
        "DATABASE=HyperScada;"      
        "UID=khaled;"        
        "PWD=Khaleho@123;"        
    )
    return connection

def server_log(channel_number, actual_value):
    connection = create_server_connection()
    cur = connection.cursor()
    cur.execute("EXEC [dbo].[InsertReadings] ?, ?", channel_number, actual_value)
    connection.commit()
    cur.close()
    connection.close()

def create_connection():
    conn = sqlite3.connect('water_filling_system.db')
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS operators (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL UNIQUE,
                        op_id TEXT NOT NULL UNIQUE
                      )''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            mode TEXT,
            config TEXT
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 station_name TEXT,
                 port_number INTEGER,
                 operator_name TEXT,
                 truck_number TEXT,
                 receipt_number TEXT,
                 required_quantity INTEGER,
                 actual_quantity INTEGER,
                 flow_meter_reading REAL,
                 entry_time DATETIME,
                 logout_time DATETIME)''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS port_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port_name TEXT NOT NULL,
            current_flowmeter TEXT NOT NULL,
            state TEXT NOT NULL )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port TEXT,
            flowmeter TEXT,
            operator_id TEXT,
            truck_number TEXT,
            receipt_number TEXT,
            required_quantity TEXT,
            actual_quantity TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_operator(operator_name, operator_password, opertator_ID):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO operators (name, password, op_id) VALUES (?, ?, ?)", (operator_name, operator_password, opertator_ID))
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
    cursor.execute("SELECT name, password, op_id FROM operators")
    operators = cursor.fetchall()
    conn.close()
    return operators  # Return full operator details

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

def get_operator_id(operator_name):
    conn = create_connection()
    cursor = conn.cursor()    
    cursor.execute("SELECT op_id FROM operators WHERE name = ?", (operator_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return None    


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

def add_port(port_name, mode, config):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ports (name, mode, config) VALUES (?, ?, ?)", (port_name, mode, config))
    conn.commit()
    conn.close()
    return "port added successfully."

def remove_port(port_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ports WHERE name=?", (port_name,))
    conn.commit()
    conn.close()
    return "port removed successfully."

def list_ports():
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM ports")
        ports = cursor.fetchall()
        conn.close()
        return [port[0] for port in ports]

def get_ports():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, mode, config FROM ports')
    ports = cursor.fetchall()
    conn.close()
    return ports

def get_config(port_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mode, config FROM ports WHERE name = ?", (port_name,))
    result = cursor.fetchone()
    conn.close()
    return result    

def update_port(port_name, mode, config):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ports SET mode = ?, config = ? WHERE name = ?", (mode, config, port_name))
    conn.commit()
    conn.close()
    return "port updated successfully."

def is_port_name_unique(port_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ports WHERE name=?", (port_name,))
    result = cursor.fetchone()
    conn.close()
    return result is None

def log_action(station_name, port_number, operator_name, truck_number, receipt_number, required_quantity, actual_quantity, flow_meter_reading, entry_time, logout_time):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO logs (station_name, port_number, operator_name, truck_number, receipt_number, required_quantity, actual_quantity, flow_meter_reading, entry_time, logout_time)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (station_name, port_number, operator_name, truck_number, receipt_number, required_quantity, actual_quantity, flow_meter_reading, entry_time, logout_time))
    conn.commit()
    conn.close()

def get_logs():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT station_name, port_number, operator_name, truck_number, receipt_number, required_quantity, actual_quantity, flow_meter_reading, entry_time, logout_time FROM logs')
    logs = cursor.fetchall()
    conn.close()
    return logs

def store_port_data_from_mqtt(port_name, flow_meter_value, state):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM port_data WHERE port_name = ?", (port_name,))
    result = cursor.fetchone()
    if result:
        if flow_meter_value is not None:
            cursor.execute("UPDATE port_data SET current_flowmeter = ? WHERE port_name = ?", (flow_meter_value, port_name))
        if state is not None:
            cursor.execute("UPDATE port_data SET state = ? WHERE port_name = ?", (state, port_name))
    else:
        cursor.execute("INSERT INTO port_data (port_name, current_flowmeter, state) VALUES (?, ?, ?)", 
                       (port_name, flow_meter_value if flow_meter_value is not None else "", 
                        state if state is not None else ""))
    conn.commit()
    conn.close()

def get_flowmeter_value(port_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_flowmeter FROM port_data WHERE port_name = ?", (port_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_log_on_stop(port_name, actual_quantity, flow_meter_reading, logout_time):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE logs
        SET actual_quantity = ?, flow_meter_reading = ?, logout_time = ?
        WHERE port_number = ? AND actual_quantity IS NULL
    ''', (actual_quantity, flow_meter_reading, logout_time, port_name))
    conn.commit()
    conn.close()

def update_operator(old_name, old_id, new_name, new_id, new_password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE operators
            SET name = ?, op_id = ?, password = ?
            WHERE name = ? AND op_id = ?
        ''', (new_name, new_id, new_password, old_name, old_id))
        conn.commit()
        return "Operator updated successfully."
    except sqlite3.IntegrityError:
        return f"Operator '{new_name}' already exists."
    finally:
        conn.close()

def get_channel_entries():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT port, flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity FROM channel_entry")
    results = cursor.fetchall()
    conn.close()
    return results

def update_channel_entry(port_name, flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channel_entry WHERE port = ?", (port_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute('''
            UPDATE channel_entry
            SET flowmeter = ?, operator_id = ?, truck_number = ?, receipt_number = ?, required_quantity = ?, actual_quantity = ?
            WHERE port = ?
        ''', (flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity, port_name))
    else:
        cursor.execute('''
            INSERT INTO channel_entry (port, flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (port_name, flowmeter, operator_id, truck_number, receipt_number, required_quantity, actual_quantity))
    conn.commit()
    conn.close()

def get_channel_entry(port_name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT truck_number, operator_id, receipt_number, required_quantity, actual_quantity, flowmeter
        FROM channel_entry
        WHERE port = ?
    ''', (port_name,))
    result = cursor.fetchone()
    conn.close()
    return result
