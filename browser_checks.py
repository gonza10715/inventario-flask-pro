"""Browser checks for account, inventory and logout flows with isolated data."""

import importlib.util
import sqlite3
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parent
APP_FILE = ROOT / "inventario web" / "app.py"


def load_application(database_dir):
    spec = importlib.util.spec_from_file_location("inventory_browser_app", APP_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.root_path = str(APP_FILE.parent)
    module.BASE_DIR = database_dir
    module.app.config.update(TESTING=True, SECRET_KEY="browser-test-secret")

    with sqlite3.connect(database_dir / "database.db") as conn:
        conn.executescript("""
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                owner_id INTEGER REFERENCES users(id)
            );
        """)
    return module.app


def check_flow(browser, base_url, width, height):
    page = browser.new_page(viewport={"width": width, "height": height})
    failures = []
    page.on("pageerror", lambda error: failures.append(str(error)))
    username = f"test_{width}"
    product = f"Cuaderno {width}"
    try:
        page.goto(base_url, wait_until="domcontentloaded")
        assert page.get_by_role("heading", name="Iniciar sesión").is_visible()
        page.get_by_role("link", name="Registrate").click()
        page.get_by_label("Usuario").fill(username)
        page.get_by_label("Contraseña").fill("clave-segura-123")
        page.get_by_role("button", name="Crear cuenta").click()
        assert page.get_by_role("heading", name="Iniciar sesión").is_visible()
        page.get_by_label("Usuario").fill(username)
        page.get_by_label("Contraseña").fill("clave-segura-123")
        page.get_by_role("button", name="Ingresar").click()
        assert page.get_by_role("heading", name="Panel de Control").is_visible()

        page.get_by_label("Nombre del producto").fill(product)
        page.get_by_label("Cantidad inicial").fill("3")
        page.get_by_role("button", name="Agregar", exact=True).click()
        assert page.locator("#productTable").get_by_text(product).is_visible()
        assert page.get_by_role("heading", name="Resumen de stock").is_visible()
        assert product in page.locator(".stock-bars").inner_text()

        page.get_by_label("Buscar producto").fill("no-existe-xyz")
        matching_row = page.locator("#productTable tr").filter(has_text=product)
        assert not matching_row.is_visible()
        page.get_by_label("Buscar producto").fill("")
        assert matching_row.is_visible()

        page.get_by_label("Cantidad de " + product).fill("2")
        page.get_by_role("button", name="Actualizar").click()
        assert page.get_by_label("Cantidad de " + product).input_value() == "2"

        page.get_by_label("Consulta al asistente").fill("total unidades")
        page.get_by_role("button", name="Consultar").click()
        page.locator("#chat-box .bot").last.wait_for()
        assert "2 unidades" in page.locator("#chat-box .bot").last.inner_text()

        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="Eliminar").click()
        assert not page.locator("#productTable").get_by_text(product).count()

        # Search should ignore accents and explain when nothing matches.
        page.get_by_label("Nombre del producto").fill("Café molido")
        page.get_by_label("Cantidad inicial").fill("1")
        page.get_by_role("button", name="Agregar", exact=True).click()
        page.get_by_label("Buscar producto").fill("cafe")
        assert page.locator("#productTable").get_by_text("Café molido").is_visible()
        assert not page.locator("#searchEmpty").is_visible()
        page.get_by_label("Buscar producto").fill("ninguno-987")
        assert page.locator("#searchEmpty").is_visible()
        page.get_by_label("Buscar producto").fill("")
        assert not page.locator("#searchEmpty").is_visible()

        document_width = page.evaluate("document.documentElement.scrollWidth")
        assert document_width <= width + 3, (
            f"Horizontal overflow at {width}px: content width={document_width}"
        )
        page.get_by_role("button", name="Cerrar sesión").click()
        assert page.get_by_role("heading", name="Iniciar sesión").is_visible()
        assert not failures, f"JavaScript errors: {failures}"
        print(f"Flask browser flow passed at {width}x{height}", flush=True)
    finally:
        page.close()


def main():
    with tempfile.TemporaryDirectory(prefix="inventory-qa-") as directory:
        app = load_application(Path(directory))
        server = make_server("127.0.0.1", 0, app, threaded=True)
        runner = threading.Thread(target=server.serve_forever, daemon=True)
        runner.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    url = f"http://127.0.0.1:{server.server_port}/"
                    check_flow(browser, url, 1365, 900)
                    check_flow(browser, url, 390, 844)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            runner.join(timeout=5)


if __name__ == "__main__":
    main()
