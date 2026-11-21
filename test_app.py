"""Pruebas de integración de la demo Flask, sin tocar la base de datos real."""
import importlib.util
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
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
                name TEXT NOT NULL, quantity INTEGER NOT NULL);
        """)
    module.app.config.update(TESTING=True, SECRET_KEY="testing-only-secret")
    return module.app.test_client()


def csrf(client):
    with client.session_transaction() as session:
        return session["_csrf_token"]


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
