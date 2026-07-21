import sqlite3
import os
from werkzeug.security import generate_password_hash

# Delete existing DB file if it exists
if os.path.exists("my_first_database.db"):
    os.remove("my_first_database.db")
    print("Old database deleted.")

conn = sqlite3.connect("my_first_database.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")

# Insert Admin
hashed_pw = generate_password_hash("adminpassword")
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_pw))

conn.commit()
conn.close()

print("Fresh database created successfully with user: 'admin' and password: 'adminpassword'")