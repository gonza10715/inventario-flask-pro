# Inventario Flask Pro — sistema de stock (demo)

Proyecto de aprendizaje y portfolio de **Gonzalo Martínez**, desarrollado con Python, Flask y SQLite.

## Funcionalidades
- Registro e inicio de sesión.
- Panel para consultar productos.
- Alta, edición de cantidad y eliminación de productos.
- Chatbot basado en reglas: cantidad de productos, unidades totales y stock bajo.

## Ejecución local
1. Requiere Python 3 y un entorno virtual recomendado.
2. Entrá en la carpeta `inventario web`.
3. Instalá las dependencias: `pip install -r requirements.txt`.
4. Inicializá la base de datos con `python crear_db.py`.
5. Ejecutá `python app.py` y abrí la dirección local indicada por Flask.

## Advertencia de seguridad
**Este proyecto es una demo educativa y no es apto para producción.** El código actual guarda contraseñas sin hash, define una clave de sesión fija y ejecuta Flask en modo debug. Antes de desplegarlo públicamente deben corregirse estos puntos, agregar protección CSRF y revisar la autorización y las operaciones de borrado.

## Tecnologías
Python · Flask · SQLite · HTML/CSS/JavaScript.

## Autor
[Gonzalo Martínez](https://github.com/gonza10715)
