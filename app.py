from flask import Flask, render_template, request, redirect, session
import sqlite3
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# ✅ DB INIT
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            image TEXT,
            file TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ✅ HOME
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)

# ✅ PRODUCT PAGE
@app.route("/product/<int:id>")
def product(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    p = c.fetchone()
    conn.close()
    return render_template("product.html", p=p)

# ✅ ADD TO CART
@app.route("/add/<int:id>")
def add(id):
    cart = session.get("cart", {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session["cart"] = cart
    return redirect("/")

# ✅ CART
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    items = []
    total = 0

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    for pid in cart:
        c.execute("SELECT * FROM products WHERE id=?", (pid,))
        p = c.fetchone()

        if not p:
            continue

        qty = cart[pid]
        price = int(p[2])

        subtotal = price * qty
        total += subtotal

        items.append({
            "id": p[0],
            "name": p[1],
            "price": price,
            "image": p[3],
            "file": p[4],
            "qty": qty,
            "subtotal": subtotal
        })

    conn.close()
    return render_template("cart.html", items=items, total=total)

# ✅ INCREASE QTY
@app.route("/inc/<int:id>")
def inc(id):
    cart = session.get("cart", {})

    if str(id) in cart:
        cart[str(id)] += 1

    session["cart"] = cart
    return redirect("/cart")

# ✅ DECREASE QTY
@app.route("/dec/<int:id>")
def dec(id):
    cart = session.get("cart", {})

    if str(id) in cart:
        cart[str(id)] -= 1

        if cart[str(id)] <= 0:
            cart.pop(str(id))

    session["cart"] = cart
    return redirect("/cart")

# ✅ REMOVE
@app.route("/remove/<int:id>")
def remove(id):
    cart = session.get("cart", {})
    cart.pop(str(id), None)
    session["cart"] = cart
    return redirect("/cart")

# ✅ LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

# ✅ ADMIN PANEL
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        image = request.form.get("image")
        file = request.form.get("file")

        image = image if image else None
        file = file if file else None

        c.execute("INSERT INTO products (name, price, image, file) VALUES (?, ?, ?, ?)",
                  (name, price, image, file))
        conn.commit()

    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()

    return render_template("admin.html", products=products)

# ✅ DELETE
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ✅ EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        price = int(request.form["price"])
        image = request.form.get("image")
        file = request.form.get("file")

        c.execute("UPDATE products SET name=?, price=?, image=?, file=? WHERE id=?",
                  (name, price, image, file, id))
        conn.commit()
        return redirect("/admin")

    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()

    return render_template("edit.html", product=product)

# ✅ WHATSAPP ORDER
@app.route("/whatsapp")
def whatsapp():
    cart = session.get("cart", {})
    msg = "Hello, I want to order:\n"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    total = 0

    for pid in cart:
        c.execute("SELECT * FROM products WHERE id=?", (pid,))
        p = c.fetchone()

        if not p:
            continue

        qty = cart[pid]
        price = int(p[2])
        subtotal = price * qty
        total += subtotal

        msg += f"{p[1]} x {qty} = ₹{subtotal}\n"

    msg += f"Total: ₹{total}"

    conn.close()

    # 🔥 IMPORTANT FIX (encode message)
    encoded_msg = quote(msg)

    return redirect(f"https://wa.me/916266500048?text={encoded_msg}")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

if __name__ == "__main__":
    app.run(debug=True)