import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'perfume_secret_key_123'
DB_NAME = 'my_first_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost REAL DEFAULT 0,
            price REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            split REAL DEFAULT 50.0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if search_query:
        cursor.execute('SELECT id, name, cost, price, quantity, split FROM inventory WHERE name LIKE ?', (f'%{search_query}%',))
    else:
        cursor.execute('SELECT id, name, cost, price, quantity, split FROM inventory')
        
    rows = cursor.fetchall()
    conn.close()

    perfumes = []
    total_val = 0.0
    total_profit = 0.0

    for row in rows:
        item_id, name, cost, price, qty, split = row
        
        cost = float(cost or 0)
        price = float(price or 0)
        qty = int(qty or 0)
        split = float(split or 50.0)

        unit_profit = price - cost
        total_unit_profit = unit_profit * qty
        your_share = total_unit_profit * (split / 100.0)

        total_val += (price * qty)
        total_profit += total_unit_profit

        perfumes.append({
            'id': item_id,
            'name': name,
            'cost': cost,
            'price': price,
            'quantity': qty,
            'split': split,
            'unit_profit': unit_profit,
            'your_share': your_share
        })

    username = session.get('username', 'Admin')

    return render_template(
        'dashboard.html',
        perfumes=perfumes,
        total_val=total_val,
        total_profit=total_profit,
        username=username,
        search_query=search_query
    )

@app.route('/add', methods=['POST'])
def add_item():
    name = request.form.get('name')
    cost = request.form.get('cost', 0)
    price = request.form.get('price', 0)
    quantity = request.form.get('quantity', 0)
    split = request.form.get('split', 50.0)

    if name:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO inventory (name, cost, price, quantity, split) VALUES (?, ?, ?, ?, ?)',
            (name, float(cost or 0), float(price or 0), int(quantity or 0), float(split or 50.0))
        )
        conn.commit()
        conn.close()
        flash('Fragrance added successfully!', 'success')

    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    flash('Item deleted.', 'warning')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)