from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "clave_super_secreta"


# ---------------- CONEXIÓN DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------- LOGIN ----------------
@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        session["user"] = user["username"]
        return redirect("/dashboard")
    else:
        return "Usuario o contraseña incorrectos"


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Usuario ya existe"

    conn.close()
    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        products=products,
        user=session["user"]
    )


# ---------------- AGREGAR PRODUCTO ----------------
@app.route("/add_product", methods=["POST"])
def add_product():
    if "user" not in session:
        return redirect("/")

    name = request.form.get("name")
    quantity = request.form.get("quantity")

    try:
        quantity = int(quantity)
    except:
        return "Cantidad inválida"

    conn = get_db()
    conn.execute(
        "INSERT INTO products (name, quantity) VALUES (?, ?)",
        (name, quantity)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- EDITAR PRODUCTO ----------------
@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    if "user" not in session:
        return redirect("/")

    quantity = request.form.get("quantity")

    try:
        quantity = int(quantity)
    except:
        return "Cantidad inválida"

    conn = get_db()
    conn.execute(
        "UPDATE products SET quantity=? WHERE id=?",
        (quantity, id)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- ELIMINAR PRODUCTO ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- CHATBOT BACKEND ----------------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"response": "No autorizado"})

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"response": "Mensaje inválido"})

    message = data["message"].lower()

    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    if "total productos" in message:
        return jsonify({"response": f"Tenés {len(products)} productos registrados."})

    if "stock bajo" in message:
        bajos = [p["name"] for p in products if p["quantity"] < 5]
        if bajos:
            return jsonify({"response": "Productos con stock bajo: " + ", ".join(bajos)})
        else:
            return jsonify({"response": "No hay productos con stock bajo."})

    if "total unidades" in message:
        total = sum(p["quantity"] for p in products)
        return jsonify({"response": f"Tenés {total} unidades en total."})

    return jsonify({
        "response": "Podés preguntarme: total productos, stock bajo, total unidades."
    })


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
