from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
from datetime import datetime
import csv
import io

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('perfume_inventory_pro.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_advanced_db():
    conn = get_db_connection()
    # Add new column support dynamically if missing from older schemas
    cursor = conn.cursor()
    columns_inv = [col[1] for col in cursor.execute("PRAGMA table_info(inventory)").fetchall()]
    if 'brand' not in columns_inv:
        cursor.execute("ALTER TABLE inventory ADD COLUMN brand TEXT DEFAULT 'Generic'")
    if 'size_ml' not in columns_inv:
        cursor.execute("ALTER TABLE inventory ADD COLUMN size_ml INTEGER DEFAULT 100")
        
    columns_sales = [col[1] for col in cursor.execute("PRAGMA table_info(sales_history)").fetchall()]
    if 'customer_name' not in columns_sales:
        cursor.execute("ALTER TABLE sales_history ADD COLUMN customer_name TEXT DEFAULT 'Walk-in Customer'")
    if 'payment_status' not in columns_sales:
        cursor.execute("ALTER TABLE sales_history ADD COLUMN payment_status TEXT DEFAULT 'Paid'")
    conn.commit()
    conn.close()

# Run schema migrations
init_advanced_db()

@app.route('/')
def home():
    return redirect(url_for('show_inventory'))

@app.route('/inventory')
def show_inventory():
    conn = get_db_connection()
    
    items = conn.execute('SELECT * FROM inventory ORDER BY id DESC').fetchall()
    
    try:
        sales = conn.execute('SELECT * FROM sales_history ORDER BY id DESC').fetchall()
    except sqlite3.OperationalError:
        sales = []

    # Financial Calculations
    total_revenue = sum(sale['revenue'] or 0 for sale in sales)
    total_net_profit = sum(sale['net_profit'] or 0 for sale in sales)
    total_user_share = sum(sale['user_share'] or 0 for sale in sales)
    total_partner_share = total_net_profit - total_user_share
    
    # Valuation & Inventory Stats
    stock_value = sum((item['cost_price'] or 0) * (item['quantity'] or 0) for item in items)
    potential_revenue = sum((item['selling_price'] or 0) * (item['quantity'] or 0) for item in items)
    low_stock_count = sum(1 for item in items if 0 < item['quantity'] <= 2)

    # Chart Data Preparation (Last 7 sales)
    chart_labels = [sale['item_name'] for sale in reversed(sales[:7])]
    chart_revenue = [sale['revenue'] or 0 for sale in reversed(sales[:7])]
    chart_profit = [sale['net_profit'] or 0 for sale in reversed(sales[:7])]

    conn.close()
    
    return render_template(
        'inventory.html', 
        inventory_list=items, 
        sales_list=sales, 
        revenue=total_revenue, 
        profit=total_net_profit,
        user_share=total_user_share,
        partner_share=total_partner_share,
        stock_value=stock_value,
        potential_revenue=potential_revenue,
        low_stock=low_stock_count,
        chart_labels=chart_labels,
        chart_revenue=chart_revenue,
        chart_profit=chart_profit
    )

@app.route('/add_stock', methods=['POST'])
def add_stock():
    name = request.form.get('item_name')
    brand = request.form.get('brand') or 'Generic'
    size_ml = request.form.get('size_ml', type=int) or 100
    cost_price = request.form.get('cost_price', type=float) or 0.0
    selling_price = request.form.get('selling_price', type=float) or 0.0
    quantity = request.form.get('quantity', type=int) or 1
    partner_split = request.form.get('partner_split', type=float) or 50.0

    if name:
        conn = get_db_connection()
        existing = conn.execute('SELECT * FROM inventory WHERE LOWER(item_name) = LOWER(?)', (name,)).fetchone()
        
        if existing:
            conn.execute(
                '''UPDATE inventory 
                   SET quantity = quantity + ?, cost_price = ?, selling_price = ?, partner_split = ?, brand = ?, size_ml = ? 
                   WHERE id = ?''',
                (quantity, cost_price, selling_price, partner_split, brand, size_ml, existing['id'])
            )
        else:
            conn.execute(
                '''INSERT INTO inventory (item_name, brand, size_ml, cost_price, selling_price, quantity, partner_split) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (name, brand, size_ml, cost_price, selling_price, quantity, partner_split)
            )
        conn.commit()
        conn.close()

    return redirect(url_for('show_inventory'))

@app.route('/sell/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    customer = request.form.get('customer_name') or 'Walk-in Customer'
    status = request.form.get('payment_status') or 'Paid'
    
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
    
    if item and item['quantity'] > 0:
        cost = item['cost_price'] or 0.0
        price = item['selling_price'] or 0.0
        net_profit = price - cost
        split_pct = (item['partner_split'] if item['partner_split'] is not None else 50.0) / 100.0
        
        user_share = net_profit * split_pct
        time_now = datetime.now().strftime("%b %d, %Y - %I:%M %p")
        
        conn.execute('UPDATE inventory SET quantity = quantity - 1 WHERE id = ?', (item_id,))
        
        conn.execute(
            '''INSERT INTO sales_history 
               (item_name, quantity_sold, revenue, net_profit, user_share, timestamp, customer_name, payment_status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (item['item_name'], 1, price, net_profit, user_share, time_now, customer, status)
        )
        conn.commit()
        
    conn.close()
    return redirect(url_for('show_inventory'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_inventory'))

@app.route('/export_csv')
def export_csv():
    conn = get_db_connection()
    sales = conn.execute('SELECT * FROM sales_history ORDER BY id DESC').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sale ID', 'Item Name', 'Customer', 'Payment Status', 'Qty Sold', 'Revenue (NGN)', 'Net Profit (NGN)', 'Your Share (NGN)', 'Timestamp'])

    for sale in sales:
        s_dict = dict(sale)
        writer.writerow([
            s_dict.get('id'),
            s_dict.get('item_name'),
            s_dict.get('customer_name', 'Walk-in'),
            s_dict.get('payment_status', 'Paid'),
            s_dict.get('quantity_sold', 1),
            s_dict.get('revenue', 0.0),
            s_dict.get('net_profit', 0.0),
            s_dict.get('user_share', 0.0),
            s_dict.get('timestamp', '')
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=perfume_sales_report.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)