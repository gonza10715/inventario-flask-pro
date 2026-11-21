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

    # Los productos heredados no tenían propietario. Permanecen sin asignar,
    # para impedir acceso accidental entre cuentas. Respaldar antes de migrar.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(products)")}
    if "owner_id" not in columns:
        conn.execute(
            "ALTER TABLE products ADD COLUMN owner_id INTEGER REFERENCES users(id)"
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_owner ON products(owner_id)"
    )

    # Retirar la cuenta demo creada con credenciales públicas en versiones anteriores.
    conn.execute("DELETE FROM users WHERE username = ? AND password = ?", ("admin", "1234"))

    for user_id, password in conn.execute("SELECT id, password FROM users").fetchall():
        if not password.startswith(("scrypt:", "pbkdf2:")):
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (generate_password_hash(password), user_id),
            )

print("Base de datos lista. Registrá un usuario desde la pantalla de acceso.")
