# Inventario Flask Pro — sistema de stock (demo)

Proyecto de aprendizaje y portfolio de **Gonzalo Martínez**, desarrollado con Python, Flask y SQLite.

## Funcionalidades

- Registro e inicio de sesión con contraseñas protegidas mediante hash.
- Panel con tabla, búsqueda y resumen gráfico de stock generado en HTML/CSS, sin dependencia de servicios externos.
- Alta, edición de cantidad y eliminación de productos.
- Asistente de inventario basado en reglas: productos, unidades totales y stock bajo.
- Formularios protegidos contra solicitudes CSRF y validaciones básicas de entradas.

## Ejecución local

1. Requiere Python 3 y se recomienda usar un entorno virtual.
2. Entrá en la carpeta `inventario web`.
3. Instalá las dependencias: `pip install -r requirements.txt`.
4. Ejecutá `python crear_db.py` para preparar la base de datos.
5. Ejecutá `python app.py` y abrí la dirección local indicada por Flask.
6. Usá **Registrarse** para crear tu cuenta; no hay usuario y contraseña predeterminados.

Para mantener las sesiones activas al reiniciar el servidor, configurá la variable de entorno `SECRET_KEY` con un valor largo y privado. Sin ella, el proyecto genera una clave aleatoria nueva cada vez que arranca.

### Si ya tenías una base de datos

**Primero respaldá `database.db` y detené la aplicación.** Después ejecutá `python crear_db.py`. El script transforma contraseñas antiguas en hashes y retira la cuenta de prueba `admin / 1234` si conserva esa contraseña. También agrega `owner_id` a los productos anteriores: **esos registros permanecen guardados pero quedan ocultos hasta que su propietario sea verificado y asignado de forma explícita**. No lo ejecutes sobre información real sin probar antes la migración en una copia.

## Seguridad y alcance

Esta es una **demo educativa local, no una aplicación lista para producción**. Incluye contraseñas con hash, protección CSRF, cookies de sesión HTTP-only, borrado solo por POST y depuración desactivada por defecto. Antes de ofrecerla como servicio público faltan, entre otras cosas, HTTPS, control de intentos de acceso, permisos avanzados, configuración de despliegue y revisión de seguridad.

## Tecnologías

Python · Flask · Werkzeug · SQLite · HTML/CSS/JavaScript.

## Autor

[Gonzalo Martínez](https://github.com/gonza10715)

## Calidad de código y pruebas automatizadas

La carpeta raíz contiene `test_app.py`, con pruebas de integración que crean una **base de datos SQLite temporal**, sin modificar los datos de `inventario web/database.db`. Cubren:

- Navegación pública y protección de rutas privadas.
- Registro con validaciones, usuarios duplicados e inicio de sesión.
- Rechazo de formularios sin token CSRF.
- Alta, edición y eliminación de productos.
- Respuestas del asistente basado en reglas y autorización de acceso.

Para ejecutarlas desde la raíz:

```bash
python -m pip install -r "inventario web/requirements.txt" pytest
python -m pytest -q test_app.py
```

La configuración `.github/workflows/tests.yml` ejecuta las pruebas en GitHub Actions con cada push a `main` y pull request. También verifica en Chromium el registro, el inicio de sesión, las operaciones de inventario y el cierre de sesión en tamaños de PC y celular, utilizando una base de datos temporal. **La presencia de tests no implica que hayan pasado: verificá la última ejecución de Actions.**

### Arquitectura y limitaciones

- **SQLite** facilita practicar SQL y consultas parametrizadas sin servidor externo; para varias personas escribiendo simultáneamente se debe evaluar otra arquitectura.
- **Sesión de Flask y CSRF**: protegen las operaciones del prototipo, pero no sustituyen controles de despliegue, autorización por recurso ni auditoría.
- **Aislamiento por cuenta:** desde el [PR #2](https://github.com/gonza10715/inventario-flask-pro/pull/2) se usa `owner_id` para filtrar lectura, edición, eliminación y consultas del asistente por usuario. **No implementa roles, organizaciones ni permisos empresariales.**
- **Asistente basado en reglas:** no usa un modelo de lenguaje ni una API de IA.
- **Próxima mejora técnica:** elaborar un procedimiento de reasignación auditada de productos heredados, reforzar el manejo de errores y ampliar permisos.

### Productos privados por cuenta

La implementación incorporada mediante el PR #2 agrega una columna `products.owner_id` y limita todas las consultas y modificaciones de productos al identificador del usuario autenticado. Las pruebas de integración incluyen dos sesiones que intentan consultar y modificar el mismo producto.

**Migración de bases existentes (importante):**

1. Detené la aplicación y respaldá `inventario web/database.db` antes de ejecutar cualquier migración.
2. En la versión principal, ejecutá `python "inventario web/crear_db.py"` desde la raíz del repositorio.
3. El script agrega `owner_id` si falta. Los productos que existían antes quedan con `owner_id = NULL`, **sin acceso para ningún usuario**.
4. No reasignamos esos datos automáticamente a la primera cuenta: eso podría mostrar información privada a la persona equivocada. Es necesario identificar su propietario legítimo y preparar una reasignación explícita.
5. La migración pasó una prueba automatizada con datos ficticios. **El producto sigue sin ser apto para uso comercial.** No importes una base real sin respaldo ni verificación manual.

Para revisar el razonamiento, consultá el [PR #2](https://github.com/gonza10715/inventario-flask-pro/pull/2) y [las decisiones técnicas](docs/decisiones-autorizacion.md). En GitHub Actions se verificaron 6 pruebas exitosas en la ejecución #13 previa a la integración.
