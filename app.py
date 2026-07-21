import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_NAME = 'my_first_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            quantity INTEGER,
            price REAL
        )
    ''')
    conn.commit()
    conn.close()

# Auto-create database on startup
init_db()

@app.route('/')
def index():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        raw_items = cursor.fetchall()
        conn.close()

        # Format items safely in Python to prevent HTML/Jinja format errors
        formatted_items = []
        for item in raw_items:
            item_id = item[0]
            name = item[1] or "Unknown Item"
            qty = item[2] if item[2] is not None else 0
            
            try:
                price = f"₦{float(item[3]):,.2f}"
            except (ValueError, TypeError):
                price = "₦0.00"

            formatted_items.append((item_id, name, qty, price))

        return render_template('dashboard.html', items=formatted_items)
    except Exception as e:
        return f"Database error: {e}", 500

@app.route('/login')
def login():
    login_template_path = os.path.join(app.template_folder or 'templates', 'login.html')
    if os.path.exists(login_template_path):
        return render_template('login.html')
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_item():
    item_name = request.form.get('item_name') or request.form.get('name')
    quantity = request.form.get('quantity')
    price = request.form.get('price')
    
    if item_name and quantity and price:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO inventory (item_name, quantity, price) VALUES (?, ?, ?)',
                       (item_name, int(quantity), float(price)))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)