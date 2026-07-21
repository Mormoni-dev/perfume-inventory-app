import sqlite3
from flask import Flask, request, redirect, url_for, render_template, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_inventory_key_change_in_production"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect("my_first_database.db")
    cursor = conn.cursor()
    cursor.execute(query, args)
    if commit:
        conn.commit()
        conn.close()
        return
    rv = cursor.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    query_db("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            cost_price REAL NOT NULL DEFAULT 0.0,
            selling_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            partner_split REAL NOT NULL DEFAULT 50.0
        )
    """, commit=True)

    query_db("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """, commit=True)

    existing_user = query_db("SELECT * FROM users WHERE username = ?", ("admin",), one=True)
    if not existing_user:
        hashed_pw = generate_password_hash("adminpassword")
        query_db("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", hashed_pw), commit=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = query_db("SELECT id, username, password FROM users WHERE username = ?", (username,), one=True)
        
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Welcome back! Successfully logged in.", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").strip()
    if search_query:
        raw_inventory = query_db(
            "SELECT id, item_name, cost_price, selling_price, quantity, partner_split FROM inventory WHERE item_name LIKE ?", 
            (f"%{search_query}%",)
        )
    else:
        raw_inventory = query_db("SELECT id, item_name, cost_price, selling_price, quantity, partner_split FROM inventory")

    inventory = []
    total_val = 0
    total_expected_profit = 0

    if raw_inventory:
        for item in raw_inventory:
            item_id, name, cost, price, qty, split = item
            item_total_val = price * qty
            unit_profit = price - cost
            total_profit = unit_profit * qty
            partner_share = total_profit * (split / 100.0)
            your_share = total_profit - partner_share

            total_val += item_total_val
            total_expected_profit += total_profit

            inventory.append({
                "id": item_id,
                "name": name,
                "cost": cost,
                "price": price,
                "quantity": qty,
                "split": split,
                "total_val": item_total_val,
                "unit_profit": unit_profit,
                "partner_share": partner_share,
                "your_share": your_share
            })

    return render_template(
        "dashboard.html", 
        perfumes=inventory, 
        search_query=search_query, 
        total_val=total_val, 
        total_profit=total_expected_profit,
        username=session.get("username")
    )

@app.route("/add", methods=["POST"])
def add_item():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    name = request.form.get("name", "").strip()
    cost = request.form.get("cost", "0")
    price = request.form.get("price", "0")
    quantity = request.form.get("quantity", "0")
    split = request.form.get("split", "50")

    try:
        cost = float(cost)
        price = float(price)
        quantity = int(quantity)
        split = float(split)

        if not name or price < 0 or quantity < 0 or cost < 0 or not (0 <= split <= 100):
            flash("Invalid input values provided. Please double-check prices and quantity.", "danger")
            return redirect(url_for("home"))

        query_db(
            "INSERT INTO inventory (item_name, cost_price, selling_price, quantity, partner_split) VALUES (?, ?, ?, ?, ?)", 
            (name, cost, price, quantity, split), commit=True
        )
        flash(f"Successfully added '{name}' to inventory!", "success")
    except ValueError:
        flash("Please enter valid numeric values for prices and quantities.", "danger")

    return redirect(url_for("home"))

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    query_db("DELETE FROM inventory WHERE id = ?", (item_id,), commit=True)
    flash("Item deleted from inventory.", "warning")
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)