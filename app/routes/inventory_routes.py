from flask import Blueprint, render_template, request, redirect, url_for, Response
from app.models.inventory_model import InventoryModel
import csv
import io

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def home():
    return redirect(url_for('inventory.show_inventory'))

@inventory_bp.route('/inventory')
def show_inventory():
    items = InventoryModel.get_all_items()
    sales = InventoryModel.get_all_sales()

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

@inventory_bp.route('/add_stock', methods=['POST'])
def add_stock():
    name = request.form.get('item_name')
    brand = request.form.get('brand', '')
    size_ml = request.form.get('size_ml', type=int) or 100
    cost_price = request.form.get('cost_price', type=float) or 0.0
    selling_price = request.form.get('selling_price', type=float) or 0.0
    quantity = request.form.get('quantity', type=int) or 1
    partner_split = request.form.get('partner_split', type=float) or 50.0

    if name:
        InventoryModel.add_or_update_stock(
            name, brand, size_ml, cost_price, selling_price, quantity, partner_split
        )

    return redirect(url_for('inventory.show_inventory'))

@inventory_bp.route('/sell/<int:item_id>', methods=['POST'])
def sell_item(item_id):
    customer_name = request.form.get('customer_name', 'Walk-in Customer')
    payment_status = request.form.get('payment_status', 'Paid')
    
    InventoryModel.record_sale(item_id, customer_name, payment_status)
    return redirect(url_for('inventory.show_inventory'))

@inventory_bp.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    InventoryModel.delete_item(item_id)
    return redirect(url_for('inventory.show_inventory'))

@inventory_bp.route('/export_csv')
def export_csv():
    sales = InventoryModel.get_all_sales()

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