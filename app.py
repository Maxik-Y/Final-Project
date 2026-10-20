from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "1234567890"

def get_db_connection():
    db = sqlite3.connect('shop.db')
    db.row_factory = sqlite3.Row
    return db

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hash_pass = generate_password_hash(password)
        
        db = get_db_connection()
        try:
            db.execute("INSERT INTO users (user_name, hash) VALUES (?, ?)", (username, hash_pass))
            db.commit()
        except sqlite3.IntegrityError:
            return "Користувач з таким ім'ям вже існує"
        finally:
            db.close()
        return redirect("/login")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        db = get_db_connection()
        user = db.execute("SELECT * FROM users WHERE user_name = ?", (username,)).fetchone()
        db.close()
        
        if user is None or not check_password_hash(user["hash"], password):
            return "Неправильне ім'я користивача чи пароль"
            
        session["user_id"] = user["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
        
    db = get_db_connection()
    products = db.execute("SELECT * FROM products").fetchall()
    db.close()
    return render_template("index.html", products=products)

@app.route("/buy", methods=["POST"])
def buy():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"})
        
    data = request.json
    purchases = data.get("cart", [])
    
    db = get_db_connection()
    user_id = session["user_id"]
    
    for item in purchases:
        product_id = item["product_id"]
        quantity = int(item["quantity"])
        if quantity > 0:
            db.execute("INSERT INTO purchases (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
    db.commit()
    db.close()
    
    return jsonify({"status": "success"})

@app.route("/history")
def history():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"})
        
    db = get_db_connection()
    history = db.execute("""
        SELECT prd.product_name, pur.quantity, pur.time_stamp FROM purchases pur
        JOIN products prd ON pur.product_id = prd.id
        WHERE pur.user_id = ? ORDER BY pur.time_stamp DESC
    """, (session["user_id"],)).fetchall()
    db.close()
    
    return render_template("history.html", history=history)

if __name__ == "__main__":
    app.run(debug=True)