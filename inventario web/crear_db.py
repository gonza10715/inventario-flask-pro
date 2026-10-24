"""Inicializa tablas y migra contraseñas heredadas a hashes seguros."""
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

db_path = Path(__file__).resolve().parent / "database.db"
with sqlite3.connect(db_path) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)

    # Retirar la cuenta demo creada con credenciales públicas en versiones anteriores.
    conn.execute("DELETE FROM users WHERE username = ? AND password = ?", ("admin", "1234"))

    for user_id, password in conn.execute("SELECT id, password FROM users").fetchall():
        if not password.startswith(("scrypt:", "pbkdf2:")):
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(password), user_id),
            )

print("Base de datos lista. Registrá un usuario desde la pantalla de acceso.")
