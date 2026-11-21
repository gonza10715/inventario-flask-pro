# Guía para explicar este cambio en una entrevista

Este documento es una ayuda para estudiar el código, **no un guion para memorizar**.

## 1. Qué problema resolvemos

El sistema ya pedía usuario y contraseña, pero cualquier cuenta podía modificar el stock de otra. Había autenticación, pero faltaba autorización sobre los recursos.

## 2. Cómo lo resolvemos

- Guardamos `user_id` en la sesión tras iniciar sesión.
- Cada producto nuevo se guarda con `owner_id`.
- La consulta del listado usa `WHERE owner_id = ?`.
- Las modificaciones y eliminaciones exigen **ID de producto y propietario** en la misma sentencia SQL.
- Para un ID inexistente o ajeno devolvemos un 404, sin revelar si pertenece a otra cuenta.

## 3. Qué significa cada tecnología

**Flask** recibe las solicitudes HTTP y decide qué función ejecutar.  
**SQLite** guarda los datos en un archivo local.  
**SQL** consulta y modifica los registros.  
**pytest** automatiza escenarios repetibles de prueba.  
**GitHub Actions** puede ejecutar los tests en cada cambio.

## 4. Cómo demostrar que entendés el cambio

1. Buscá el login en `inventario web/app.py` y explicá por qué guardamos el ID del usuario.
2. Buscá las operaciones `SELECT`, `UPDATE` y `DELETE`: señalá la condición que evita el acceso cruzado.
3. Abrí `test_app.py` y explicá qué pasa cuando B intenta borrar el producto de A.
4. Contá por qué una migración de una base antigua requiere hacer un respaldo.
5. Ejecutá localmente los tests y explicá cualquier fallo antes de publicar el cambio.

## 5. Un ejercicio para hacer por tu cuenta

Agregá una prueba que demuestre que **B sí puede crear y editar su propio producto**, sin afectar al producto de A. Primero escribí el caso; después ejecutalo. No alcanza con copiar el resultado: tratá de explicar cada línea.

## 6. Limitaciones que no hay que ocultar

La app sigue siendo un prototipo local, sin roles administrativos ni aislamiento por empresa. Los productos anteriores a la migración quedan sin propietario; todavía falta un mecanismo supervisado para reasignarlos. No se debe presentar como un sistema terminado ni conectado a un cliente real.
