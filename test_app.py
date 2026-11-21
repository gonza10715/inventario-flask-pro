"""Pruebas de integración de la demo Flask, sin tocar la base de datos real."""
import importlib.util
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
APP_FILE = ROOT / "inventario web" / "app.py"


@pytest.fixture
def client(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("inventario_app", APP_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "BASE_DIR", tmp_path)
    with sqlite3.connect(tmp_path / "database.db") as connection:
        connection.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
            CREATE TABLE products (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, quantity INTEGER NOT NULL,\n                owner_id INTEGER REFERENCES users(id));
        """)
    module.app.config.update(TESTING=True, SECRET_KEY="testing-only-secret")
    return module.app.test_client()


def csrf(client):
    # El login rota la sesión y descarta el token CSRF anterior.
    # Visitar el panel genera uno nuevo en la plantilla para formularios.
    with client.session_transaction() as session:
        token = session.get("_csrf_token")
    if token is None:
        response = client.get("/dashboard")
        assert response.status_code == 200
        with client.session_transaction() as session:
            token = session.get("_csrf_token")
    assert token is not None
    return token


def test_public_pages_and_protected_routes(client):
    assert client.get("/").status_code == 200
    assert client.get("/register").status_code == 200
    assert client.get("/dashboard").status_code == 302
    assert client.post("/add_product", data={"name": "Test", "quantity": "2"}).status_code == 400
    assert client.post("/chat", json={"message": "total productos"}).status_code == 400


def test_registration_login_inventory_and_csrf(client):
    assert client.get("/").status_code == 200
    token = csrf(client)
    assert client.post("/register_user", data={
        "username": "xx", "password": "corta", "csrf_token": token
    }).status_code == 400
    assert client.post("/register_user", data={
        "username": "persona1", "password": "una-clave-segura", "csrf_token": token
    }).status_code == 302
    assert client.post("/register_user", data={
        "username": "persona1", "password": "una-clave-segura", "csrf_token": token
    }).status_code == 409
    assert client.post("/login", data={
        "username": "persona1", "password": "incorrecta", "csrf_token": token
    }).status_code == 401
    assert client.post("/login", data={
        "username": "persona1", "password": "una-clave-segura", "csrf_token": token
    }).status_code == 302
    assert client.get("/dashboard").status_code == 200
    token = csrf(client)
    assert client.post("/add_product", data={
        "name": "Cuaderno", "quantity": "-1", "csrf_token": token
    }).status_code == 400
    assert client.post("/add_product", data={
        "name": "Cuaderno", "quantity": "7", "csrf_token": token
    }).status_code == 302
    assert b"Cuaderno" in client.get("/dashboard").data
    assert client.post("/edit/1", data={
        "quantity": "3", "csrf_token": token
    }).status_code == 302
    response = client.post("/chat", json={"message": "total unidades"},
                           headers={"X-CSRF-Token": token})
    assert response.status_code == 200
    assert "3" in response.json["response"]
    response = client.post("/chat", json={"message": "stock bajo"},
                           headers={"X-CSRF-Token": token})
    assert "Cuaderno" in response.json["response"]
    assert client.post("/delete/1", data={"csrf_token": token}).status_code == 302
    assert b"Cuaderno" not in client.get("/dashboard").data


def test_login_required_even_with_valid_csrf(client):
    client.get("/")
    token = csrf(client)
    assert client.post("/add_product", data={
        "name": "No autorizado", "quantity": "4", "csrf_token": token
    }).status_code == 302
    response = client.post("/chat", json={"message": "total productos"},
                           headers={"X-CSRF-Token": token})
    assert response.status_code == 401


def test_users_cannot_read_or_change_each_others_products(client):
    """Integración con dos sesiones independientes y una sola base de datos."""
    second = client.application.test_client()

    for current, username in ((client, "ana"), (second, "beto")):
        assert current.get("/").status_code == 200
        token = csrf(current)
        assert current.post("/register_user", data={
            "username": username,
            "password": "clave-de-prueba-123",
            "csrf_token": token,
        }).status_code == 302
        assert current.post("/login", data={
            "username": username,
            "password": "clave-de-prueba-123",
            "csrf_token": token,
        }).status_code == 302

    ana_token = csrf(client)
    beto_token = csrf(second)
    assert client.post("/add_product", data={
        "name": "Privado de Ana",
        "quantity": "7",
        "csrf_token": ana_token,
    }).status_code == 302
    assert b"Privado de Ana" in client.get("/dashboard").data
    assert b"Privado de Ana" not in second.get("/dashboard").data

    # Un ID conocido no autoriza a un segundo usuario.
    assert second.post("/edit/1", data={
        "quantity": "100", "csrf_token": beto_token,
    }).status_code == 404
    assert second.post("/delete/1", data={
        "csrf_token": beto_token,
    }).status_code == 404
    assert b"Privado de Ana" in client.get("/dashboard").data
    with sqlite3.connect(
        client.application.view_functions["dashboard"].__globals__["BASE_DIR"] / "database.db"
    ) as connection:
        current_quantity = connection.execute(
            "SELECT quantity FROM products WHERE id = 1"
        ).fetchone()[0]
    assert current_quantity == 7

    response = second.post("/chat", json={"message": "total productos"},
                           headers={"X-CSRF-Token": beto_token})
    assert "0 productos" in response.json["response"]
    response = client.post("/chat", json={"message": "total unidades"},
                           headers={"X-CSRF-Token": ana_token})
    assert "7 unidades" in response.json["response"]


def test_legacy_unowned_product_is_hidden(client):
    client.get("/")
    token = csrf(client)
    client.post("/register_user", data={
        "username": "user1", "password": "password-123",
        "csrf_token": token,
    })
    client.post("/login", data={
        "username": "user1", "password": "password-123",
        "csrf_token": token,
    })
    with sqlite3.connect(client.application.view_functions["dashboard"].__globals__["BASE_DIR"] / "database.db") as connection:
        connection.execute(
            "INSERT INTO products(name, quantity, owner_id) VALUES (?, ?, NULL)",
            ("Producto anterior", 55),
        )
    assert b"Producto anterior" not in client.get("/dashboard").data


def test_legacy_migration_keeps_products_unassigned_and_is_idempotent(tmp_path):
    """Probar crear_db.py en una copia temporal, nunca sobre datos personales."""
    migration = tmp_path / "crear_db.py"
    shutil.copy2(ROOT / "inventario web" / "crear_db.py", migration)
    database = tmp_path / "database.db"
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL
            );
            INSERT INTO products(name, quantity) VALUES ('Stock heredado', 8);
        """)
    for _ in range(2):
        subprocess.run([sys.executable, str(migration)], check=True, capture_output=True,
                       text=True)
    with sqlite3.connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(products)")}
        products = connection.execute(
            "SELECT name, quantity, owner_id FROM products"
        ).fetchall()
    assert "owner_id" in columns
    assert products == [("Stock heredado", 8, None)]
