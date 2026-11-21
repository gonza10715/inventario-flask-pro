# Decisión técnica: aislamiento de productos por cuenta

**Proyecto:** Inventario Flask Pro (prototipo educativo).  
**Estado:** integración realizada desde el [PR #2](https://github.com/gonza10715/inventario-flask-pro/pull/2); seis pruebas de integración aprobadas en CI. Sigue sin estar listo para producción.

## El problema

Inicialmente el sistema autenticaba usuarios, pero todas las operaciones sobre la tabla `products` eran globales. Un usuario podía listar, actualizar o eliminar productos creados por otro.

Autenticar responde **quién sos**; autorizar responde **qué recurso podés consultar o modificar**. Son problemas distintos.

## Modelo de datos

```text
users
  id (PK)
  username (UNIQUE)
  password (hash)

products
  id (PK)
  name
  quantity
  owner_id (FK -> users.id, NULL para productos antiguos)
```

Cada producto nuevo recibe el ID de cuenta desde la sesión **validada por el servidor**, nunca desde un campo manipulable del formulario.

## Regla de autorización

Para mostrar, editar o eliminar productos se filtra por `owner_id`:

```sql
SELECT id, name, quantity
FROM products
WHERE owner_id = ?;

UPDATE products
SET quantity = ?
WHERE id = ? AND owner_id = ?;

DELETE FROM products
WHERE id = ? AND owner_id = ?;
```

Las operaciones sobre productos ajenos o inexistentes devuelven 404, sin revelar si existe un producto de otra cuenta.

## Migración de datos

La migración agrega una columna a bases anteriores y un índice sobre `owner_id`. Deja los registros antiguos sin propietario (`NULL`). Esto es **fail closed**: evita asignar información antigua a una cuenta equivocada.

Para recuperar productos heredados, un responsable debe verificar su propiedad y hacer una reasignación explícita desde una copia de respaldo. Esta herramienta de reasignación **aún no existe**.

## Pruebas clave

- Dos sesiones distintas se registran, inician sesión y acceden a la misma base de prueba.
- La cuenta B no puede listar ni modificar un producto creado por A.
- El asistente muestra los totales propios de cada cuenta.
- Un producto heredado sin dueño no aparece en el dashboard.
- La migración se ejecuta dos veces sobre una copia de base anterior y conserva datos.

## Límites pendientes

No hay roles, organizaciones, historial de movimientos, recuperación de contraseñas, controles contra intentos repetidos de login ni despliegue endurecido. SQLite funciona bien para este prototipo local, pero requiere evaluación de concurrencia para un sistema comercial.

