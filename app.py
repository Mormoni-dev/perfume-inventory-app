import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'perfume_app_secret_key_pro_999'
DB_NAME = 'perfume_inventory_pro.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # Inventory table
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
        # Sales history ledger
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
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        conn.commit()

init_db()

AUTH_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>{{ title }} - Perfume Hub Pro</title></head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
    <div style="background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 100%; max-width: 380px; color: #f8fafc;">
        <h2 style="margin-top: 0; color: #38bdf8; text-align: center;">Fragrance Manager</h2>
        <p style="text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 25px;">{{ title }} to your business dashboard</p>
        {% if error %}<p style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 10px; border-radius: 6px; font-size: 13px; text-align: center;">{{ error }}</p>{% endif %}
        <form method="POST">
            <p><input type="text" name="username" placeholder="Username" required style="width: 100%; padding: 12px; box-sizing: border-box; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: white;"></p>
            <p><input type="password" name="password" placeholder="Password" required style="width: 100%; padding: 12px; box-sizing: border-box; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: white;"></p>
            <button type="submit" style="width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 15px; margin-top: 10px;">{{ title }}</button>
        </form>
        <p style="text-align: center; margin-top: 20px; font-size: 14px; color: #94a3b8;">
            {% if title == 'Login' %}
                Don't have an account? <a href="/register" style="color: #38bdf8; text-decoration: none;">Register</a>
            {% else %}
                Already have an account? <a href="/login" style="color: #38bdf8; text-decoration: none;">Login</a>
            {% endif %}
        </p>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Perfume Hub Pro - Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8fafc; margin: 0; padding: 0; color: #1e293b; }
        .topbar { background: #1e293b; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .topbar h2 { margin: 0; font-size: 20px; color: #38bdf8; }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border-left: 4px solid #0284c7; }
        .card.profit { border-left-color: #10b981; }
        .card.sales { border-left-color: #8b5cf6; }
        .card h3 { margin: 0 0 8px 0; font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
        .card p { margin: 0; font-size: 24px; font-weight: bold; color: #0f172a; }
        .grid-layout { display: grid; grid-template-columns: 350px 1fr; gap: 25px; }
        @media (max-width: 900px) { .grid-layout { grid-template-columns: 1fr; } }
        .panel { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .panel h3 { margin-top: 0; margin-bottom: 20px; font-size: 16px; color: #334155; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 6px; }
        input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; }
        button.btn-primary { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; transition: background 0.2s; }
        button.btn-primary:hover { background: #0369a1; }
        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #f1f5f9; font-size: 14px; }
        th { background: #f8fafc; color: #475569; font-weight: 600; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
        .badge-low { background: #fee2e2; color: #dc2626; }
        .badge-ok { background: #dcfce7; color: #16a34a; }
        .btn-sell { padding: 6px 12px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 12px; }
        .btn-sell:hover { background: #059669; }
        .history-section { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="topbar">
        <h2>✨ Perfume Hub Pro</h2>
        <div>
            <span style="color: #94a3b8;">User:</span> <strong>{{ user }}</strong> | 
            <a href="/logout" style="color: #f87171; text-decoration: none; margin-left: 15px; font-weight: 600;">Logout</a>
        </div>
    </div>

    <div class="container">
        <!-- Metrics Cards -->
        <div class="cards">
            <div class="card">
                <h3>Total Inventory Value</h3>
                <p>₦{{ "{:,.2f}".format(total_val) }}</p>
            </div>
            <div class="card profit">
                <h3>Total Realized Profit (Earned)</h3>
                <p style="color: #10b981;">₦{{ "{:,.2f}".format(total_realized_profit) }}</p>
            </div>
            <div class="card sales">
                <h3>Total Sales Recorded</h3>
                <p style="color: #8b5cf6;">{{ total_sales_count }} units</p>
            </div>
            <div class="card">
                <h3>Items in Stock</h3>
                <p style="color: #0284c7;">{{ total_items }}</p>
            </div>
        </div>

        <div class="grid-layout">
            <!-- Add Form Panel -->
            <div class="panel">
                <h3>Add New Fragrance</h3>
                <form action="/add" method="POST">
                    <label>Perfume Name</label>
                    <input type="text" name="item_name" placeholder="e.g., Creed Aventus" required>
                    
                    <label>Cost Price (₦)</label>
                    <input type="number" step="0.01" name="cost_price" placeholder="0.00" required>
                    
                    <label>Selling Price (₦)</label>
                    <input type="number" step="0.01" name="selling_price" placeholder="0.00" required>
                    
                    <label>Quantity</label>
                    <input type="number" name="quantity" placeholder="0" required>
                    
                    <label>Partner Split %</label>
                    <input type="number" step="0.1" name="partner_split" value="50.0" required>
                    
                    <button type="submit" class="btn-primary">Add to Inventory</button>
                </form>
            </div>

            <!-- Active Inventory Table -->
            <div class="panel">
                <h3>Live Inventory</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Item Name</th>
                            <th>Cost / Sell</th>
                            <th>Qty</th>
                            <th>Potential Profit</th>
                            <th>Status</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if items %}
                            {% for item in items %}
                            <tr>
                                <td><strong>{{ item.item_name }}</strong></td>
                                <td>₦{{ "{:,.2f}".format(item.cost_price) }}<br><small style="color: #64748b;">Sell: ₦{{ "{:,.2f}".format(item.selling_price) }}</small></td>
                                <td>{{ item.quantity }}</td>
                                <td style="color: #10b981; font-weight: 600;">₦{{ "{:,.2f}".format(item.potential_profit) }}</td>
                                <td>
                                    {% if item.quantity <= 2 %}
                                        <span class="badge badge-low">Low Stock</span>
                                    {% else %}
                                        <span class="badge badge-ok">In Stock</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <form action="/sell/{{ item.id }}" method="POST" style="margin:0;">
                                        <button type="submit" class="btn-sell">Sell 1</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px;">No inventory items yet. Add your stock using the form!</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Profit & Sales History Log -->
        <div class="panel history-section">
            <h3>📈 Sales & Profit History Ledger</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date & Time</th>
                        <th>Fragrance Sold</th>
                        <th>Qty Sold</th>
                        <th>Total Revenue</th>
                        <th>Net Profit</th>
                        <th>Your Partner Cut</th>
                    </tr>
                </thead>
                <tbody>
                    {% if history %}
                        {% for h in history %}
                        <tr>
                            <td>{{ h.timestamp }}</td>
                            <td><strong>{{ h.item_name }}</strong></td>
                            <td>{{ h.quantity_sold }}</td>
                            <td>₦{{ "{:,.2f}".format(h.revenue) }}</td>
                            <td style="color: #10b981; font-weight: 600;">₦{{ "{:,.2f}".format(h.net_profit) }}</td>
                            <td style="color: #0284c7; font-weight: bold;">₦{{ "{:,.2f}".format(h.user_share) }}</td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="6" style="text-align: center; color: #94a3b8; padding: 30px;">No sales recorded yet. Click "Sell 1" on an item above to log profit history!</td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inventory')
            raw_items = cursor.fetchall()

            cursor.execute('SELECT * FROM sales_history ORDER BY id DESC')
            raw_history = cursor.fetchall()

        formatted_items = []
        total_val = 0.0
        total_items = 0

        for row in raw_items:
            qty = row['quantity'] if row['quantity'] is not None else 0
            cost = float(row['cost_price']) if row['cost_price'] is not None else 0.0
            sell = float(row['selling_price']) if row['selling_price'] is not None else 0.0
            
            item_total_value = qty * sell
            item_potential_profit = qty * (sell - cost)

            total_val += item_total_value
            total_items += qty

            formatted_items.append({
                'id': row['id'],
                'item_name': row['item_name'] if row['item_name'] else "Unnamed Item",
                'cost_price': cost,
                'selling_price': sell,
                'quantity': qty,
                'potential_profit': item_potential_profit
            })

        # Calculate realized profits from sales history
        total_realized_profit = 0.0
        total_sales_count = 0
        formatted_history = []

        for h in raw_history:
            q_sold = h['quantity_sold']
            rev = h['revenue']
            profit = h['net_profit']
            share = h['user_share']
            
            total_realized_profit += profit
            total_sales_count += q_sold

            formatted_history.append({
                'timestamp': h['timestamp'],
                'item_name': h['item_name'],
                'quantity_sold': q_sold,
                'revenue': rev,
                'net_profit': profit,
                'user_share': share
            })

        return render_template_string(
            DASHBOARD_TEMPLATE, 
            items=formatted_items, 
            history=formatted_history,
            total_val=total_val, 
            total_realized_profit=total_realized_profit,
            total_sales_count=total_sales_count,
            total_items=total_items,
            user=session['user']
        )
    except Exception as e:
        return f"Database error: {e}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template_string(AUTH_TEMPLATE, title='Login', error="Invalid username or password")

    return render_template_string(AUTH_TEMPLATE, title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)

        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
                conn.commit()
            session['user'] = username
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template_string(AUTH_TEMPLATE, title='Register', error="Username already exists")

    return render_template_string(AUTH_TEMPLATE, title='Register')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_item():
    if 'user' not in session:
        return redirect(url_for('login'))

    item_name = request.form.get('item_name')
    cost_price = request.form.get('cost_price')
    selling_price = request.form.get('selling_price')
    quantity = request.form.get('quantity')
    partner_split = request.form.get('partner_split')
    
    if item_name and cost_price and selling_price and quantity:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inventory (item_name, cost_price, selling_price, quantity, partner_split) 
                VALUES (?, ?, ?, ?, ?)
            ''', (item_name, float(cost_price), float(selling_price), int(quantity), float(partner_split)))
            conn.commit()
        
    return redirect(url_for('index'))

@app.route('/sell/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    with get_db() as conn:
        cursor = conn.cursor()
        # Fetch the item details before updating
        cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
        item = cursor.fetchone()

        if item and item['quantity'] > 0:
            name = item['item_name']
            cost = item['cost_price']
            sell = item['selling_price']
            split = item['partner_split']
            
            # Reduce inventory quantity by 1
            cursor.execute('UPDATE inventory SET quantity = quantity - 1 WHERE id = ?', (item_id,))
            
            # Calculate financials for this single sale
            item_profit = sell - cost
            user_share_percentage = (100 - split) / 100.0
            user_share_amount = item_profit * user_share_percentage
            timestamp = datetime.now().strftime('%b %d, %Y - %I:%M %p')

            # Log into sales history
            cursor.execute('''
                INSERT INTO sales_history (item_name, quantity_sold, revenue, net_profit, user_share, timestamp)
                VALUES (?, 1, ?, ?, ?, ?)
            ''', (name, sell, item_profit, user_share_amount, timestamp))
            
            conn.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)