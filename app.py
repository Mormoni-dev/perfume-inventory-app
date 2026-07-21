from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_NAME = 'my_first_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Using item_name to prevent schema conflicts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Auto-create table when app launches
init_db()

@app.route('/')
def index():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM inventory')
        items = cursor.fetchall()
        conn.close()
        return render_template('dashboard.html', items=items)
    except Exception as e:
        # Prints exact error in Render logs instead of failing silently
        print(f"Error fetching inventory: {e}")
        return f"Database error: {e}", 500

@app.route('/add', methods=['POST'])
def add_item():
    # Handles both 'name' and 'item_name' from HTML form
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