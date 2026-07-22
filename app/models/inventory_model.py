import sqlite3
from datetime import datetime

DB_PATH = 'perfume_inventory_pro.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class InventoryModel:
    @staticmethod
    def get_all_items():
        conn = get_db_connection()
        items = conn.execute('SELECT * FROM inventory ORDER BY id DESC').fetchall()
        conn.close()
        return items

    @staticmethod
    def get_item_by_id(item_id):
        conn = get_db_connection()
        item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
        conn.close()
        return item

    @staticmethod
    def add_or_update_stock(name, brand, size_ml, cost_price, selling_price, quantity, partner_split):
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

    @staticmethod
    def record_sale(item_id, customer_name='Walk-in Customer', payment_status='Paid'):
        conn = get_db_connection()
        item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
        
        if item and item['quantity'] > 0:
            cost = item['cost_price'] or 0.0
            price = item['selling_price'] or 0.0
            net_profit = price - cost
            split_pct = (item['partner_split'] if item['partner_split'] is not None else 50.0) / 100.0
            user_share = net_profit * split_pct
            time_now = datetime.now().strftime("%b %d, %Y - %I:%M %p")
            
            # 1. Deduct quantity
            conn.execute('UPDATE inventory SET quantity = quantity - 1 WHERE id = ?', (item_id,))
            
            # 2. Record sales entry
            conn.execute(
                '''INSERT INTO sales_history 
                   (item_name, quantity_sold, revenue, net_profit, user_share, timestamp, customer_name, payment_status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (item['item_name'], 1, price, net_profit, user_share, time_now, customer_name, payment_status)
            )
            conn.commit()
            conn.close()
            return True
            
        conn.close()
        return False

    @staticmethod
    def get_all_sales():
        conn = get_db_connection()
        try:
            sales = conn.execute('SELECT * FROM sales_history ORDER BY id DESC').fetchall()
        except sqlite3.OperationalError:
            sales = []
        conn.close()
        return sales