import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session
import sqlite3
from urllib.parse import quote
DB_PATH = "database.db"

if os.environ.get("RENDER"):
    DB_PATH = "/tmp/database.db"

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/images"   # 🔥 CHANGE
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# ✅ DB INIT
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔥 PRODUCTS TABLE (always create)
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            image TEXT,
            file TEXT,
            bestseller INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# ✅ HOME
@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔥 Bestseller auto logic
    c.execute("""
        SELECT p.*, COUNT(o.id) as order_count
        FROM products p
        LEFT JOIN orders o
        ON o.details LIKE '%' || p.id || '%'
        WHERE p.deleted=0
        GROUP BY p.id
        ORDER BY order_count DESC
    """)

    products = c.fetchall()

    conn.close()
    return render_template("index.html", products=products)

# ✅ PRODUCT PAGE
@app.route("/product/<int:id>")
def product(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # ✅ PRODUCT FETCH
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    p = c.fetchone()

    # ✅ REVIEWS FETCH
    c.execute("SELECT * FROM reviews WHERE product_id=?", (id,))
    reviews = c.fetchall()

    conn.close()

    # 🔥 IMPORTANT CHANGE
    return render_template("product.html", p=p, reviews=reviews)

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

        qty = int(cart[pid])
        price = int(p[2])

        subtotal = price * qty
        total += subtotal

        items.append({
            "id": p[0],
            "name": p[1],
            "price": price,
            "file": p[3],
            "qty": qty,
            "subtotal": subtotal
        })

    conn.close()
    return render_template("cart.html", items=items, total=total)

# ✅ QTY
@app.route("/inc/<int:id>")
def inc(id):
    cart = session.get("cart", {})
    if str(id) in cart:
        cart[str(id)] += 1
    session["cart"] = cart
    return redirect("/cart")

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
            return redirect("/secret-admin-98765")
    return render_template("login.html")

# ✅ ADMIN (UPLOAD SYSTEM)
@app.route("/admin-VAIBHAV-PRIVATE-ACCESS-2026", methods=["GET", "POST"])
def admin():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]

        # ✅ MANUAL PRICE
        price = request.form["price"]

        bestseller = 1 if request.form.get("bestseller") else 0

        file = request.files.get("file")
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)

            # save in static/images
            file.save(os.path.join("static/images", filename))

        c.execute("""
            INSERT INTO products (name, price, image, file, bestseller)
            VALUES (?, ?, ?, ?, ?)
        """, (name, price, filename, filename, bestseller))

        conn.commit()

    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()

    conn.close()

    return render_template("admin.html", products=products)

# ✅ EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]

        bestseller = 1 if request.form.get("bestseller") else 0

        file = request.files.get("file")

        # image upload hua
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join("static/images", filename))

            c.execute("""
                UPDATE products
                SET name=?, price=?, image=?, file=?, bestseller=?
                WHERE id=?
            """, (name, price, filename, filename, bestseller, id))

        else:
            c.execute("""
                UPDATE products
                SET name=?, price=?, bestseller=?
                WHERE id=?
            """, (name, price, bestseller, id))

        conn.commit()
        conn.close()

        return redirect("/admin-VAIBHAV-PRIVATE-ACCESS-2026")

    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()

    conn.close()

    return render_template("edit.html", product=product)

# ✅ DELETE
@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE products SET deleted=1 WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin-VAIBHAV-PRIVATE-ACCESS-2026")

# ✅ ADD REVIEW
@app.route("/add_review/<int:id>", methods=["POST"])
def add_review(id):
    name = request.form["name"]
    rating = int(request.form["rating"])
    comment = request.form["comment"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews (product_id, name, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (id, name, rating, comment))

    conn.commit()
    conn.close()

    return redirect(f"/product/{id}")

# ✅ WHATSAPP
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

    return redirect(f"https://wa.me/916266500048?text={quote(msg)}")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # TOTAL PRODUCTS
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]

    # TOTAL ORDERS
    c.execute("SELECT COUNT(*) FROM orders")
    total_orders = c.fetchone()[0]

    # TOTAL REVENUE
    c.execute("SELECT details FROM orders")
    orders = c.fetchall()

    total_revenue = 0

    for order in orders:
        try:
            data = eval(order[0])   # cart dict
            for pid in data:
                qty = data[pid]

                c.execute("SELECT price FROM products WHERE id=?", (pid,))
                p = c.fetchone()

                if p:
                    total_revenue += int(p[0]) * int(qty)
        except:
            pass

    # RECENT ORDERS
    c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
    recent_orders = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           total_products=total_products,
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           recent_orders=recent_orders)

@app.route("/checkout")
def checkout():
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

        qty = int(cart[pid])
        price = int(p[2])

        subtotal = price * qty
        total += subtotal

        items.append({
            "name": p[1],
            "qty": qty,
            "subtotal": subtotal
        })

    conn.close()

    return render_template("checkout.html", items=items, total=total)

@app.route("/place_order", methods=["POST"])
def place_order():
    cart = session.get("cart", {})

    name = request.form.get("name")
    phone = request.form.get("phone")
    address = request.form.get("address")
    city = request.form.get("city")
    pincode = request.form.get("pincode")
    payment = request.form.get("payment")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # ✅ TABLE CREATE (SAFE)
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
    ''')

    # ✅ AUTO ADD COLUMNS (VERY IMPORTANT)
    columns = [col[1] for col in c.execute("PRAGMA table_info(orders)")]

    if "name" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN name TEXT")
    if "phone" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN phone TEXT")
    if "address" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN address TEXT")
    if "city" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN city TEXT")
    if "pincode" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN pincode TEXT")
    if "payment" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN payment TEXT")
    if "details" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN details TEXT")

    # ✅ CREATE PROPER ORDER TEXT
    order_text = ""
    total = 0

    for pid in cart:
        c.execute("SELECT name, price FROM products WHERE id=?", (pid,))
        p = c.fetchone()

        if not p:
            continue

        qty = int(cart[pid])
        price = int(p[1])
        subtotal = price * qty
        total += subtotal

        order_text += f"💎 {p[0]} x {qty} = ₹{subtotal}\n"

    # ✅ SAVE RAW CART ALSO
    details = str(cart)

    c.execute("""
        INSERT INTO orders (name, phone, address, city, pincode, payment, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, phone, address, city, pincode, payment, details))

    conn.commit()
    conn.close()

    session["cart"] = {}

    # ✅ WHATSAPP MESSAGE (CLEAN FORMAT)
    msg = f"""
New Order 🚀

Name: {name}
Phone: {phone}
Address: {address}
City: {city} - {pincode}

Order Details:
{order_text}

Total: ₹{total}
"""

    encoded_msg = quote(msg)

    # 👉 IMPORTANT: apna number daal
    return redirect(f"https://wa.me/916266500048?text={encoded_msg}")


# ✅ SUCCESS PAGE
@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/orders")
def orders():
    if not session.get("admin"):
        return redirect("/login")   # 🔐 PROTECTION

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("orders.html", data=data)

def init_review_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            name TEXT,
            rating INTEGER,
            comment TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_review_db()



# ❤️ ADD TO WISHLIST
@app.route("/wishlist_add/<int:id>")
def wishlist_add(id):
    wishlist = session.get("wishlist", [])

    if id not in wishlist:
        wishlist.append(id)

    session["wishlist"] = wishlist
    return redirect("/")


# ❤️ VIEW WISHLIST
@app.route("/wishlist")
def wishlist():
    wishlist = session.get("wishlist", [])
    items = []

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    for pid in wishlist:
        c.execute("SELECT * FROM products WHERE id=?", (pid,))
        p = c.fetchone()

        if p:
            items.append(p)

    conn.close()
    return render_template("wishlist.html", items=items)


# ❌ REMOVE FROM WISHLIST
@app.route("/wishlist_remove/<int:id>")
def wishlist_remove(id):
    wishlist = session.get("wishlist", [])

    if id in wishlist:
        wishlist.remove(id)

    session["wishlist"] = wishlist
    return redirect("/wishlist")

@app.route("/trash")
def trash():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM products WHERE deleted=1 ORDER BY id DESC")
    products = c.fetchall()

    conn.close()

    return render_template("trash.html", products=products)

@app.route("/restore/<int:id>")
def restore(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE products SET deleted=0 WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/trash")

@app.route("/permanent_delete/<int:id>")
def permanent_delete(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM products WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/trash")

def fix_products_table():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    columns = [col[1] for col in c.execute("PRAGMA table_info(products)")]

    # deleted column
    if "deleted" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN deleted INTEGER DEFAULT 0")

    # bestseller column
    if "bestseller" not in columns:
        c.execute("ALTER TABLE products ADD COLUMN bestseller INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

fix_products_table()

@app.route("/toggle_bestseller/<int:id>")
def toggle_bestseller(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT bestseller FROM products WHERE id=?", (id,))
    row = c.fetchone()

    if row:
        current = row[0] if row[0] is not None else 0
        new_value = 0 if current == 1 else 1

        c.execute(
            "UPDATE products SET bestseller=? WHERE id=?",
            (new_value, id)
        )

    conn.commit()
    conn.close()

    return redirect("/admin-VAIBHAV-PRIVATE-ACCESS-2026")

# 🚀 RUN
if __name__ == "__main__":
    app.run()