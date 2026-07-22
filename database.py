import sqlite3

DB_NAME = 'perfume_inventory_pro.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                cost_price REAL,
                selling_price REAL,
                quantity INTEGER,
                partner_split REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                quantity_sold INTEGER,
                revenue REAL,
                net_profit REAL,
                user_share REAL,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        conn.commit()

def get_all_inventory():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, item_name, cost_price, selling_price, quantity FROM inventory")
        return cursor.fetchall()