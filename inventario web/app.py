"""Demo de inventario: autenticación y operaciones sobre SQLite."""
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
# En producción configurar SECRET_KEY con un valor privado y persistente.
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db():
    conn = sqlite3.connect(BASE_DIR / "database.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_forms():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        submitted = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("_csrf_token", "")
        if not submitted or not expected or not hmac.compare_digest(submitted, expected):
            abort(400, description="Solicitud inválida. Actualizá la página y volvé a intentar.")


@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    conn = get_db()
    user = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user["password"], password):
        return "Usuario o contraseña incorrectos", 401
    session.clear()
    session["user"] = user["username"]
    session["user_id"] = user["id"]
    return redirect("/dashboard")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not 3 <= len(username) <= 50 or len(password) < 8:
        return "Usuario de 3 a 50 caracteres y contraseña de al menos 8 caracteres", 400
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return "Usuario ya existe", 409
    finally:
        conn.close()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    conn = get_db()
    products = conn.execute("SELECT id, name, quantity FROM products WHERE owner_id = ? ORDER BY id DESC",
                            (session["user_id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", products=products, user=session["user"])


def valid_quantity(raw):
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None
    return value if 0 <= value <= 1_000_000_000 else None


@app.route("/add_product", methods=["POST"])
def add_product():
    if "user_id" not in session:
        return redirect("/")
    name = request.form.get("name", "").strip()
    quantity = valid_quantity(request.form.get("quantity"))
    if not name or len(name) > 120 or quantity is None:
        return "Nombre o cantidad inválida", 400
    conn = get_db()
    try:
        conn.execute("INSERT INTO products (name, quantity, owner_id) VALUES (?, ?, ?)",
                     (name, quantity, session["user_id"]))
        conn.commit()
    finally:
        conn.close()
    return redirect("/dashboard")


@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/")
    quantity = valid_quantity(request.form.get("quantity"))
    if quantity is None:
        return "Cantidad inválida", 400
    conn = get_db()
    try:
        result = conn.execute(
            "UPDATE products SET quantity = ? WHERE id = ? AND owner_id = ?",
            (quantity, id, session["user_id"]),
        )
        if result.rowcount == 0:
            abort(404, description="Producto no encontrado.")
        conn.commit()
    finally:
        conn.close()
    return redirect("/dashboard")


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "user_id" not in session:
        return redirect("/")
    conn = get_db()
    try:
        result = conn.execute(
            "DELETE FROM products WHERE id = ? AND owner_id = ?",
            (id, session["user_id"]),
        )
        if result.rowcount == 0:
            abort(404, description="Producto no encontrado.")
        conn.commit()
    finally:
        conn.close()
    return redirect("/dashboard")


@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"response": "No autorizado"}), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("message"), str):
        return jsonify({"response": "Mensaje inválido"}), 400
    message = data["message"][:500].lower()
    conn = get_db()
    products = conn.execute("SELECT name, quantity FROM products WHERE owner_id = ?",
                            (session["user_id"],)).fetchall()
    conn.close()
    if "total productos" in message:
        response = f"Tenés {len(products)} productos registrados."
    elif "stock bajo" in message:
        bajos = [p["name"] for p in products if p["quantity"] < 5]
        response = "Productos con stock bajo: " + ", ".join(bajos) if bajos else "No hay productos con stock bajo."
    elif "total unidades" in message:
        response = f"Tenés {sum(p['quantity'] for p in products)} unidades en total."
    else:
        response = "Podés preguntarme: total productos, stock bajo, total unidades."
    return jsonify({"response": response})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
