import os
import secrets
import sqlite3
from functools import wraps

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
secret = os.environ.get("FLASK_SECRET_KEY")
if not secret:
    # A fresh development-only key; sessions expire on restart.
    secret = secrets.token_hex(32)
app.config.update(
    SECRET_KEY=secret,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        submitted = request.form.get("_csrf_token") or request.headers.get("X-CSRF-Token")
        if not submitted or not secrets.compare_digest(submitted, session.get("_csrf_token", "")):
            abort(400, description="Token de formulario inválido. Actualizá la página.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("home"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user:
            return "Usuario o contraseña incorrectos", 401
        stored = user["password"]
        valid = check_password_hash(stored, password) if stored.startswith(("scrypt:", "pbkdf2:")) else secrets.compare_digest(stored, password)
        if not valid:
            return "Usuario o contraseña incorrectos", 401
        # One-time migration for existing local demo users with plaintext passwords.
        if not stored.startswith(("scrypt:", "pbkdf2:")):
            conn.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(password), user["id"]))
    session.clear()
    session["user"] = username
    return redirect(url_for("dashboard"))


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_user", methods=["POST"])
def register_user():
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    if not (3 <= len(username) <= 50) or len(password) < 12:
        return "Usuario de 3 a 50 caracteres y contraseña de al menos 12 caracteres", 400
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                         (username, generate_password_hash(password)))
    except sqlite3.IntegrityError:
        return "Usuario ya existe", 409
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("dashboard.html", products=products, user=session["user"])


def validated_quantity():
    try:
        quantity = int(request.form.get("quantity", ""))
        if 0 <= quantity <= 1_000_000:
            return quantity
    except (ValueError, TypeError):
        pass
    abort(400, description="Cantidad inválida")


@app.route("/add_product", methods=["POST"])
@login_required
def add_product():
    name = (request.form.get("name") or "").strip()
    if not name or len(name) > 100:
        abort(400, description="Nombre inválido")
    with get_db() as conn:
        conn.execute("INSERT INTO products (name, quantity) VALUES (?, ?)", (name, validated_quantity()))
    return redirect(url_for("dashboard"))


@app.route("/edit/<int:id>", methods=["POST"])
@login_required
def edit(id):
    with get_db() as conn:
        conn.execute("UPDATE products SET quantity=? WHERE id=?", (validated_quantity(), id))
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    with get_db() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (id,))
    return redirect(url_for("dashboard"))


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not isinstance(message, str) or len(message) > 500:
        return jsonify(response="Mensaje inválido"), 400
    with get_db() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    message = message.lower()
    if "total productos" in message:
        reply = f"Tenés {len(products)} productos registrados."
    elif "stock bajo" in message:
        low = [p["name"] for p in products if p["quantity"] < 5]
        reply = "Productos con stock bajo: " + ", ".join(low) if low else "No hay productos con stock bajo."
    elif "total unidades" in message:
        reply = f"Tenés {sum(p['quantity'] for p in products)} unidades en total."
    else:
        reply = "Podés preguntar: total productos, stock bajo, total unidades."
    return jsonify(response=reply)


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=False)
