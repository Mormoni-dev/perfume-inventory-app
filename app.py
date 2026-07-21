import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'perfume_hub_secret_key_2026'
DB_NAME = 'my_first_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            cost_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            partner_split REAL DEFAULT 50.0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT id, item_name, cost_price, selling_price, quantity, partner_split FROM inventory')
        rows = cursor.fetchall()
        conn.close()

        items = []
        total_val = 0.0
        total_profit = 0.0

        for row in rows:
            item_id = row[0]
            name = row[1] or "Unnamed Perfume"
            cost = float(row[2]) if row[2] is not None else 0.0
            sell = float(row[3]) if row[3] is not None else 0.0
            qty = int(row[4]) if row[4] is not None else 0
            split = float(row[5]) if row[5] is not None else 50.0

            item_revenue = sell * qty
            item_net_profit = (sell - cost) * qty
            your_share = item_net_profit * (split / 100.0)

            total_val += item_revenue
            total_profit += item_net_profit

            items.append({
                'id': item_id,
                'name': name,
                'item_name': name,
                'cost': cost,
                'sell': sell,
                'cost_price': cost,
                'selling_price': sell,
                'quantity': qty,
                'partner_split': split,
                'net_profit': item_net_profit,
                'your_share': your_share
            })

        return render_template(
            'dashboard.html', 
            items=items, 
            total_val=total_val, 
            total_profit=total_profit
        )
    except Exception as e:
        print(f"Error: {e}")
        return render_template('dashboard.html', items=[], total_val=0.0, total_profit=0.0)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['logged_in'] = True
        return redirect(url_for('index'))

    login_path = os.path.join(app.template_folder or 'templates', 'login.html')
    if os.path.exists(login_path):
        return render_template('login.html')
    
    session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_item():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    item_name = request.form.get('item_name') or request.form.get('name')
    cost_price = request.form.get('cost_price') or 0
    selling_price = request.form.get('selling_price') or request.form.get('price') or 0
    quantity = request.form.get('quantity') or 0
    partner_split = request.form.get('partner_split') or 50.0

    if item_name:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO inventory (item_name, cost_price, selling_price, quantity, partner_split)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_name, float(cost_price), float(selling_price), int(quantity), float(partner_split)))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/sell/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE inventory SET quantity = MAX(0, quantity - 1) WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)