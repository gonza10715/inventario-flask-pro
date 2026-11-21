# Inventario Flask Pro — sistema de stock (demo)

Proyecto de aprendizaje y portfolio de **Gonzalo Martínez**, desarrollado con Python, Flask y SQLite.

## Funcionalidades

- Registro e inicio de sesión con contraseñas protegidas mediante hash.
- Panel con tabla, búsqueda y gráfico de stock.
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

Volvé a ejecutar `python crear_db.py`. El script transforma las contraseñas antiguas en hashes y retira la cuenta de prueba `admin / 1234` si conserva esa contraseña. No borra los demás usuarios ni productos.

## Seguridad y alcance

Esta es una **demo educativa local, no una aplicación lista para producción**. Incluye contraseñas con hash, protección CSRF, cookies de sesión HTTP-only, borrado solo por POST y depuración desactivada por defecto. Antes de ofrecerla como servicio público faltan, entre otras cosas, HTTPS, control de intentos de acceso, gestión de permisos por usuario, configuración de despliegue y pruebas automatizadas.

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

La configuración `.github/workflows/tests.yml` ejecuta las pruebas en GitHub Actions con cada push a `main` y pull request. **La presencia de tests no implica que hayan pasado: verificá la última ejecución de Actions.**

### Decisiones y límites a discutir en una entrevista

- **SQLite** facilita practicar SQL y consultas parametrizadas sin servidor externo; para varias personas escribiendo simultáneamente se debe evaluar otra arquitectura.
- **Sesión de Flask y CSRF**: protegen las operaciones del prototipo, pero no sustituyen controles de despliegue, autorización por recurso ni auditoría.
- **Modelo de datos pendiente:** actualmente todos los usuarios autenticados ven y pueden modificar el mismo inventario. **No existe separación por propietario, roles ni empresas**. No debe ofrecerse como producto multiusuario hasta resolverlo.
- **Asistente basado en reglas:** no usa un modelo de lenguaje ni una API de IA.
- **Próxima mejora técnica:** vincular productos a usuarios/organizaciones, crear migración de datos y agregar pruebas de aislamiento.
