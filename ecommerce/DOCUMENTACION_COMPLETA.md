# Documentacion Completa - E-commerce API

## Que es esta aplicacion?

Es un **backend** (servidor) para una tienda online construido con **Django** (framework de Python) y **Django REST Framework** (para crear APIs). No tiene interfaz visual para el cliente, solo expone **endpoints** (URLs) que reciben y devuelven datos en formato **JSON**.

---

## Como esta organizada la aplicacion?

```
ecommerce/
├── config/              ← Configuracion general del proyecto
│   ├── settings.py      ← Todas las configuraciones (DB, JWT, Celery, etc.)
│   ├── urls.py          ← Rutas principales (conecta todas las apps)
│   ├── celery.py        ← Configuracion de tareas asincronas
│   └── wsgi.py          ← Punto de entrada del servidor
│
├── apps/                ← Cada carpeta es un "modulo" de la tienda
│   ├── users/           ← Registro, login, perfil de usuario
│   ├── products/        ← Catalogo de productos
│   ├── orders/          ← Pedidos (ordenes de compra)
│   ├── payments/        ← Pagos
│   ├── shipments/       ← Envios
│   └── chatbot/         ← Asistente IA con Claude
│
├── core/                ← Utilidades compartidas
│   ├── permissions.py   ← Reglas de acceso (quien puede hacer que)
│   ├── pagination.py    ← Paginacion de resultados
│   └── repositories.py  ← Patron base para acceso a datos
│
├── Dockerfile           ← Instrucciones para construir el contenedor Docker
├── docker-compose.yml   ← Orquesta todos los servicios (web, redis, celery)
└── requirements.txt     ← Lista de librerias de Python necesarias
```

---

## Servicios Docker

Cuando ejecutas `docker-compose up`, se levantan **4 contenedores**:

| Servicio      | Que hace                                              | Puerto |
|---------------|-------------------------------------------------------|--------|
| **web**       | Servidor Django + Gunicorn (atiende peticiones HTTP)  | 8000   |
| **celery**    | Worker que ejecuta tareas en segundo plano            | -      |
| **celery-beat** | Programador de tareas periodicas                    | -      |
| **redis**     | Base de datos en memoria, sirve como mensajero entre Django y Celery | 6379 |

---

## Como funciona la autenticacion (JWT)

La app usa **JWT** (JSON Web Tokens). Es como un "pase temporal" que el servidor te da cuando inicias sesion:

1. **Te registras o inicias sesion** → el servidor te da 2 tokens:
   - **Access Token**: dura **1 hora**, lo usas en cada peticion
   - **Refresh Token**: dura **7 dias**, lo usas para obtener un nuevo access token cuando expire
2. **En cada peticion** envias el access token en el header:
   ```
   Authorization: Bearer eyJ0eXAiOiJKV1Qi...
   ```
3. **Cuando el access token expira** → usas el refresh token para obtener uno nuevo
4. **Cuando cierras sesion** → el refresh token se "blacklistea" (se invalida)

---

## Base de datos - Modelos (tablas)

### User (Usuario)
| Campo      | Tipo           | Descripcion                        |
|------------|----------------|------------------------------------|
| id         | Numero auto    | Identificador unico                |
| email      | Email unico    | Se usa como nombre de usuario      |
| password   | Texto cifrado  | Contraseña (nunca se guarda en texto plano) |
| first_name | Texto (max 150)| Nombre                             |
| last_name  | Texto (max 150)| Apellido                           |
| is_active  | Si/No          | Si la cuenta esta activa           |
| is_staff   | Si/No          | Si es administrador                |
| created_at | Fecha/Hora     | Cuando se creo la cuenta           |

### Product (Producto)
| Campo       | Tipo              | Descripcion                      |
|-------------|-------------------|----------------------------------|
| id          | Numero auto       | Identificador unico              |
| name        | Texto (max 255)   | Nombre del producto              |
| description | Texto largo       | Descripcion                      |
| price       | Decimal (10,2)    | Precio (minimo 0.01)             |
| stock       | Numero positivo   | Cantidad disponible              |
| is_active   | Si/No             | Si esta disponible para venta    |
| created_at  | Fecha/Hora        | Cuando se creo                   |
| updated_at  | Fecha/Hora        | Ultima modificacion              |

### Order (Pedido)
| Campo      | Tipo           | Descripcion                           |
|------------|----------------|---------------------------------------|
| id         | Numero auto    | Identificador unico                   |
| user       | FK → User      | Quien hizo el pedido                  |
| status     | Texto          | Estado: pending/paid/shipped/delivered/cancelled |
| total      | Decimal (10,2) | Total del pedido (se calcula automaticamente) |
| created_at | Fecha/Hora     | Cuando se creo                        |
| updated_at | Fecha/Hora     | Ultima modificacion                   |

### OrderItem (Item del pedido)
| Campo      | Tipo           | Descripcion                           |
|------------|----------------|---------------------------------------|
| id         | Numero auto    | Identificador unico                   |
| order      | FK → Order     | A que pedido pertenece                |
| product    | FK → Product   | Que producto es                       |
| quantity   | Numero positivo| Cantidad pedida                       |
| unit_price | Decimal (10,2) | Precio al momento de comprar          |

> **Nota**: No puede haber el mismo producto dos veces en un pedido. Si quieres 3 del mismo, pones quantity=3.

### Payment (Pago)
| Campo      | Tipo           | Descripcion                           |
|------------|----------------|---------------------------------------|
| id         | Numero auto    | Identificador unico                   |
| amount     | Decimal (10,2) | Monto del pago (minimo 0.01)          |
| method     | Texto          | Metodo: card/transfer/cash            |
| status     | Texto          | Estado: pending/completed/failed      |
| created_at | Fecha/Hora     | Cuando se creo                        |

### OrderPayment (Relacion Pago-Pedido)
| Campo          | Tipo           | Descripcion                       |
|----------------|----------------|-----------------------------------|
| id             | Numero auto    | Identificador unico               |
| order          | FK → Order     | Pedido al que se aplica           |
| payment        | FK → Payment   | Pago que se aplica                |
| amount_applied | Decimal (10,2) | Cuanto se aplico a este pedido    |

> **Nota**: Un pago puede aplicarse a varios pedidos, y un pedido puede tener varios pagos.

### Shipment (Envio)
| Campo           | Tipo           | Descripcion                      |
|-----------------|----------------|----------------------------------|
| id              | Numero auto    | Identificador unico              |
| order           | FK → Order     | Pedido que se envia              |
| status          | Texto          | Estado: pending/shipped/delivered|
| tracking_number | Texto          | Numero de rastreo (TRK-XXXX)    |
| shipped_at      | Fecha/Hora     | Cuando se envio                  |
| delivered_at    | Fecha/Hora     | Cuando se entrego                |

### Relaciones entre tablas
```
User (Usuario)
 └── Order (Pedido) ← un usuario tiene muchos pedidos
      ├── OrderItem (Items) ← un pedido tiene muchos items
      │    └── Product (Producto) ← cada item es un producto
      ├── Shipment (Envio) ← un pedido puede tener envios
      └── OrderPayment (Pago aplicado) ← un pedido puede tener varios pagos
           └── Payment (Pago) ← un pago puede aplicarse a varios pedidos
```

---

## Flujo completo de una compra

```
1. REGISTRO/LOGIN
   Usuario se registra o inicia sesion → recibe tokens JWT

2. VER PRODUCTOS
   Consulta el catalogo (no necesita estar logueado)

3. CREAR PEDIDO (status: PENDING)
   Envia lista de productos y cantidades
   → Se descuenta el stock de cada producto
   → Se calcula el total automaticamente

4. CREAR PAGO (status: PENDING)
   Crea un pago con monto y metodo

5. APLICAR PAGO AL PEDIDO
   Asocia el pago con el pedido
   → Si el pedido queda totalmente pagado → status cambia a PAID

6. CREAR ENVIO (solo admin, pedido debe estar PAID)
   Admin crea el envio → status: PENDING

7. MARCAR COMO ENVIADO (solo admin)
   → Se genera numero de rastreo (TRK-XXXX)
   → Pedido cambia a SHIPPED
   → Se envia notificacion asincrona (Celery)

8. MARCAR COMO ENTREGADO (solo admin)
   → Pedido cambia a DELIVERED
   → Se envia notificacion asincrona (Celery)
```

---

## Todos los endpoints con ejemplos

### Autenticacion base
En todos los endpoints que dicen "Requiere Auth", debes enviar este header:
```
Authorization: Bearer TU_ACCESS_TOKEN_AQUI
```

---

### 1. USUARIOS (`/api/users/`)

#### POST `/api/users/register/` - Registrar usuario
**No requiere autenticacion**

Envias:
```json
{
    "email": "juan@ejemplo.com",
    "password": "MiPassword123!",
    "password_confirm": "MiPassword123!",
    "first_name": "Juan",
    "last_name": "Perez"
}
```

Respuesta exitosa (201 Created):
```json
{
    "user": {
        "id": 1,
        "email": "juan@ejemplo.com",
        "first_name": "Juan",
        "last_name": "Perez",
        "created_at": "2024-02-09T10:30:00Z"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

Posibles errores:
```json
// 400 - Email ya existe
{"email": ["user with this email already exists."]}

// 400 - Passwords no coinciden
{"non_field_errors": ["Passwords do not match."]}

// 400 - Password muy debil
{"password": ["This password is too common.", "This password is too short."]}
```

---

#### POST `/api/users/login/` - Iniciar sesion
**No requiere autenticacion**

Envias:
```json
{
    "email": "juan@ejemplo.com",
    "password": "MiPassword123!"
}
```

Respuesta exitosa (200 OK):
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Posibles errores:
```json
// 401 - Credenciales incorrectas
{"detail": "No active account found with the given credentials"}
```

---

#### POST `/api/users/logout/` - Cerrar sesion
**Requiere Auth**

Envias:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Respuesta exitosa (200 OK):
```json
{
    "message": "Successfully logged out"
}
```

Posibles errores:
```json
// 400 - Token invalido o ya blacklisteado
{"error": "Invalid or expired token"}
```

---

#### POST `/api/users/token/refresh/` - Renovar token
**No requiere autenticacion** (pero necesitas el refresh token)

Envias:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Respuesta exitosa (200 OK):
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

> **Nota**: Te da un NUEVO refresh token. El anterior queda invalidado.

---

#### GET `/api/users/profile/` - Ver perfil
**Requiere Auth**

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "email": "juan@ejemplo.com",
    "first_name": "Juan",
    "last_name": "Perez",
    "full_name": "Juan Perez",
    "is_active": true,
    "created_at": "2024-02-09T10:30:00Z"
}
```

---

#### PATCH `/api/users/profile/` - Actualizar perfil
**Requiere Auth**

Envias (solo los campos que quieras cambiar):
```json
{
    "first_name": "Juan Carlos",
    "last_name": "Perez Lopez"
}
```

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "email": "juan@ejemplo.com",
    "first_name": "Juan Carlos",
    "last_name": "Perez Lopez",
    "full_name": "Juan Carlos Perez Lopez",
    "is_active": true,
    "created_at": "2024-02-09T10:30:00Z"
}
```

> **Nota**: No puedes cambiar el email ni el created_at (son de solo lectura).

---

### 2. PRODUCTOS (`/api/products/`)

#### GET `/api/products/` - Listar productos
**No requiere autenticacion**

Respuesta exitosa (200 OK):
```json
{
    "count": 25,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Laptop HP",
            "price": "899.99",
            "stock": 50,
            "is_active": true
        },
        {
            "id": 2,
            "name": "Mouse Logitech",
            "price": "29.99",
            "stock": 200,
            "is_active": true
        }
    ]
}
```

**Filtros disponibles** (se agregan como parametros en la URL):
```
?search=laptop              ← Buscar por nombre o descripcion
?ordering=price             ← Ordenar por precio (ascendente)
?ordering=-price            ← Ordenar por precio (descendente)
?ordering=name              ← Ordenar por nombre
?min_price=100              ← Precio minimo
?max_price=500              ← Precio maximo
?in_stock=true              ← Solo productos con stock
?is_active=true             ← Solo productos activos
?page=2                     ← Pagina 2
?page_size=20               ← 20 resultados por pagina (max 100)
```

Ejemplo combinado:
```
GET /api/products/?search=laptop&min_price=500&ordering=-price&page_size=5
```

---

#### GET `/api/products/{id}/` - Ver detalle de producto
**No requiere autenticacion**

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "name": "Laptop HP",
    "description": "Laptop HP Pavilion 15, 16GB RAM, 512GB SSD",
    "price": "899.99",
    "stock": 50,
    "is_active": true,
    "is_in_stock": true,
    "created_at": "2024-02-01T10:00:00Z",
    "updated_at": "2024-02-09T15:30:00Z"
}
```

Posibles errores:
```json
// 404 - Producto no existe
{"detail": "No encontrado."}
```

---

#### POST `/api/products/` - Crear producto
**Requiere Auth + Ser Admin (is_staff=true)**

Envias:
```json
{
    "name": "Teclado Mecanico",
    "description": "Teclado mecanico RGB switches blue",
    "price": "79.99",
    "stock": 100,
    "is_active": true
}
```

Respuesta exitosa (201 Created):
```json
{
    "id": 3,
    "name": "Teclado Mecanico",
    "description": "Teclado mecanico RGB switches blue",
    "price": "79.99",
    "stock": 100,
    "is_active": true,
    "is_in_stock": true,
    "created_at": "2024-02-09T16:00:00Z",
    "updated_at": "2024-02-09T16:00:00Z"
}
```

Posibles errores:
```json
// 403 - No eres admin
{"detail": "You do not have permission to perform this action."}

// 400 - Precio invalido
{"price": ["Price must be greater than zero."]}

// 400 - Stock negativo
{"stock": ["Stock cannot be negative."]}
```

---

#### PUT/PATCH `/api/products/{id}/` - Actualizar producto
**Requiere Auth + Ser Admin**

Envias (PATCH = solo los campos que cambias):
```json
{
    "price": "89.99",
    "stock": 150
}
```

Respuesta: Igual que el detalle del producto con los valores actualizados.

---

#### DELETE `/api/products/{id}/` - Eliminar producto
**Requiere Auth + Ser Admin**

Respuesta exitosa: **204 No Content** (sin cuerpo de respuesta)

---

### 3. PEDIDOS (`/api/orders/`)

#### POST `/api/orders/` - Crear pedido
**Requiere Auth**

Envias:
```json
{
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1}
    ]
}
```

Respuesta exitosa (201 Created):
```json
{
    "id": 1,
    "status": "pending",
    "total": "1879.97",
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Laptop HP",
                "price": "899.99"
            },
            "quantity": 2,
            "unit_price": "899.99",
            "subtotal": "1799.98"
        },
        {
            "id": 2,
            "product": {
                "id": 3,
                "name": "Teclado Mecanico",
                "price": "79.99"
            },
            "quantity": 1,
            "unit_price": "79.99",
            "subtotal": "79.99"
        }
    ],
    "created_at": "2024-02-09T16:30:00Z"
}
```

**Que pasa internamente:**
1. Verifica que los productos existan y esten activos
2. Verifica que haya stock suficiente
3. Crea el pedido con status "pending"
4. Crea los items con el precio actual del producto
5. Resta el stock de cada producto
6. Calcula el total automaticamente

Posibles errores:
```json
// 400 - Sin items
{"items": ["This list may not be empty."]}

// 400 - Producto no existe
{"items": ["Product with id 999 does not exist."]}

// 400 - Producto inactivo
{"items": ["Product 'Laptop HP' is not active."]}

// 400 - Sin stock
{"items": ["Not enough stock for 'Laptop HP'. Available: 5, Requested: 10"]}

// 400 - Producto duplicado
{"items": ["Duplicate products are not allowed."]}
```

---

#### GET `/api/orders/` - Listar pedidos
**Requiere Auth**

- Si eres **usuario normal**: solo ves TUS pedidos
- Si eres **admin** (is_staff): ves TODOS los pedidos

Respuesta exitosa (200 OK):
```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "status": "pending",
            "total": "1879.97",
            "items_count": 2,
            "created_at": "2024-02-09T16:30:00Z"
        },
        {
            "id": 2,
            "status": "paid",
            "total": "29.99",
            "items_count": 1,
            "created_at": "2024-02-09T17:00:00Z"
        }
    ]
}
```

---

#### GET `/api/orders/{id}/` - Ver detalle de pedido
**Requiere Auth**

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "user": 1,
    "user_email": "juan@ejemplo.com",
    "status": "pending",
    "total": "1879.97",
    "total_paid": "0.00",
    "is_fully_paid": false,
    "items": [
        {
            "id": 1,
            "product": {
                "id": 1,
                "name": "Laptop HP",
                "price": "899.99"
            },
            "quantity": 2,
            "unit_price": "899.99",
            "subtotal": "1799.98"
        }
    ],
    "created_at": "2024-02-09T16:30:00Z",
    "updated_at": "2024-02-09T16:30:00Z"
}
```

---

#### PATCH `/api/orders/{id}/status/` - Cambiar estado del pedido
**Requiere Auth + Ser dueño del pedido o admin**

Envias:
```json
{
    "status": "cancelled"
}
```

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "status": "cancelled",
    "total": "1879.97",
    ...
}
```

**Transiciones de estado validas:**
```
pending  → paid, cancelled
paid     → shipped, cancelled
shipped  → delivered
```
No puedes ir hacia atras (ej: de delivered a shipped).

---

#### GET `/api/orders/my-orders/` - Mis pedidos
**Requiere Auth**

Igual que listar pero siempre muestra solo los del usuario logueado, incluso si eres admin.

---

#### DELETE `/api/orders/{id}/` - Eliminar pedido
**Requiere Auth + Ser dueño o admin**

Respuesta exitosa: **204 No Content**

---

### 4. PAGOS (`/api/payments/`)

#### POST `/api/payments/` - Crear pago
**Requiere Auth**

Envias:
```json
{
    "amount": "1879.97",
    "method": "card"
}
```

Metodos disponibles: `"card"`, `"transfer"`, `"cash"`

Respuesta exitosa (201 Created):
```json
{
    "id": 1,
    "amount": "1879.97",
    "method": "card",
    "status": "pending",
    "created_at": "2024-02-09T17:00:00Z"
}
```

---

#### POST `/api/payments/{id}/apply/` - Aplicar pago a pedidos
**Requiere Auth**

Este es el endpoint mas importante de pagos. Conecta un pago con uno o varios pedidos.

**Opcion 1 - Sin montos especificos** (se distribuye automaticamente):
```json
{
    "order_ids": [1, 2]
}
```

**Opcion 2 - Con montos especificos:**
```json
{
    "order_ids": [1, 2],
    "amounts": ["1000.00", "879.97"]
}
```

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "amount": "1879.97",
    "method": "card",
    "status": "pending",
    "amount_applied": "1879.97",
    "remaining_amount": "0.00",
    "order_payments": [
        {
            "id": 1,
            "order_id": 1,
            "order_total": "1879.97",
            "amount_applied": "1879.97",
            "created_at": "2024-02-09T17:05:00Z"
        }
    ],
    "created_at": "2024-02-09T17:00:00Z"
}
```

**Que pasa internamente:**
1. Verifica que los pedidos existan y sean del usuario
2. Verifica que los pedidos esten en status "pending"
3. Verifica que el monto restante del pago alcance
4. Crea registros OrderPayment (liga pago con pedido)
5. Si un pedido queda totalmente pagado → cambia a status "paid"

Posibles errores:
```json
// 400 - Pedido no existe
{"order_ids": ["Order with id 999 does not exist."]}

// 400 - Pedido no es tuyo
{"order_ids": ["Order 5 does not belong to you."]}

// 400 - Pedido no esta pendiente
{"order_ids": ["Order 1 is not in pending status."]}

// 400 - Monto insuficiente
{"amounts": ["Total amount to apply exceeds remaining payment amount."]}
```

---

#### POST `/api/payments/{id}/complete/` - Marcar pago como completado
**Requiere Auth**

No necesitas enviar body.

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "amount": "1879.97",
    "method": "card",
    "status": "completed",
    ...
}
```

---

#### POST `/api/payments/{id}/fail/` - Marcar pago como fallido
**Requiere Auth**

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "amount": "1879.97",
    "method": "card",
    "status": "failed",
    ...
}
```

---

#### GET `/api/payments/` - Listar pagos
**Requiere Auth**

- Usuario normal: ve pagos asociados a SUS pedidos
- Admin: ve todos los pagos

Respuesta exitosa (200 OK):
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "amount": "1879.97",
            "method": "card",
            "status": "completed",
            "created_at": "2024-02-09T17:00:00Z"
        }
    ]
}
```

---

### 5. ENVIOS (`/api/shipments/`)

#### POST `/api/shipments/` - Crear envio
**Requiere Auth + Ser Admin**

Envias:
```json
{
    "order_id": 1
}
```

> El pedido debe estar en status "paid" o "shipped".

Respuesta exitosa (201 Created):
```json
{
    "id": 1,
    "order_id": 1,
    "status": "pending",
    "tracking_number": "",
    "created_at": "2024-02-09T18:00:00Z"
}
```

Posibles errores:
```json
// 400 - Pedido no pagado
{"order_id": ["Order must be in 'paid' or 'shipped' status."]}

// 403 - No eres admin
{"detail": "You do not have permission to perform this action."}
```

---

#### POST `/api/shipments/{id}/ship/` - Marcar como enviado
**Requiere Auth + Ser Admin**

No necesitas enviar body.

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "order_id": 1,
    "user_email": "juan@ejemplo.com",
    "status": "shipped",
    "tracking_number": "TRK-A3F5B7C9D2E1",
    "shipped_at": "2024-02-09T18:30:00Z",
    "delivered_at": null,
    "created_at": "2024-02-09T18:00:00Z",
    "updated_at": "2024-02-09T18:30:00Z"
}
```

**Que pasa internamente:**
1. Genera numero de rastreo automatico (TRK-XXXXXXXXXXXX)
2. Registra la fecha/hora de envio
3. Cambia el status del pedido a "shipped"
4. Dispara una tarea asincrona en Celery para enviar notificacion

---

#### POST `/api/shipments/{id}/deliver/` - Marcar como entregado
**Requiere Auth + Ser Admin**

Respuesta exitosa (200 OK):
```json
{
    "id": 1,
    "order_id": 1,
    "user_email": "juan@ejemplo.com",
    "status": "delivered",
    "tracking_number": "TRK-A3F5B7C9D2E1",
    "shipped_at": "2024-02-09T18:30:00Z",
    "delivered_at": "2024-02-10T14:00:00Z",
    "created_at": "2024-02-09T18:00:00Z",
    "updated_at": "2024-02-10T14:00:00Z"
}
```

---

#### GET `/api/shipments/` - Listar envios
**Requiere Auth**

- Usuario normal: ve envios de SUS pedidos
- Admin: ve todos

Respuesta (200 OK):
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "order_id": 1,
            "status": "shipped",
            "tracking_number": "TRK-A3F5B7C9D2E1",
            "created_at": "2024-02-09T18:00:00Z"
        }
    ]
}
```

---

#### GET `/api/shipments/by-order/{order_id}/` - Envios de un pedido
**Requiere Auth**

Devuelve lista de envios asociados a un pedido especifico.

---

#### GET `/api/shipments/track/{tracking_number}/` - Rastrear envio
**Requiere Auth**

```
GET /api/shipments/track/TRK-A3F5B7C9D2E1/
```

Devuelve el detalle completo del envio.

---

### 6. CHATBOT IA (`/api/chat/`)

#### POST `/api/chat/` - Enviar mensaje al asistente
**Requiere Auth**

Envias:
```json
{
    "message": "Cual es el estado de mi pedido #1?"
}
```

Respuesta exitosa (200 OK):
```json
{
    "response": "Tu pedido #1 esta en estado 'pending' (pendiente de pago). El total es de $1,879.97 y aun no se ha realizado ningun pago. Los items de tu pedido son: 2x Laptop HP ($899.99 c/u) y 1x Teclado Mecanico ($79.99).",
    "user_message": "Cual es el estado de mi pedido #1?"
}
```

**Como funciona el chatbot:**
1. Recibe tu mensaje
2. Lo envia a **Claude** (IA de Anthropic) junto con herramientas
3. Claude decide que herramientas usar para responder:
   - `get_order_status` → consulta estado de un pedido
   - `get_shipment_info` → consulta info de envio
   - `get_payment_info` → consulta info de pagos
   - `list_user_orders` → lista los ultimos 10 pedidos
4. Claude consulta la base de datos a traves de las herramientas
5. Genera una respuesta en lenguaje natural

> **Nota**: Necesitas la variable de entorno `ANTHROPIC_API_KEY` configurada para que funcione.

---

### 7. DOCUMENTACION API

#### GET `/api/docs/` - Swagger UI
**No requiere autenticacion**

Interfaz visual interactiva donde puedes ver y probar todos los endpoints.

#### GET `/api/schema/` - Esquema OpenAPI
**No requiere autenticacion**

Devuelve el esquema OpenAPI en formato YAML/JSON.

---

### 8. ADMIN DE DJANGO

#### GET `/admin/` - Panel de administracion
**Requiere login de admin (is_staff=true)**

Panel visual donde puedes ver y gestionar todos los datos de la aplicacion directamente.

---

## Permisos - Quien puede hacer que?

| Accion | Usuario normal | Admin (is_staff) |
|--------|---------------|-------------------|
| Registrarse / Login | Si | Si |
| Ver productos | Si | Si |
| Crear/editar/borrar productos | No | Si |
| Crear pedidos | Si (propios) | Si |
| Ver pedidos | Solo los suyos | Todos |
| Borrar pedidos | Solo los suyos | Todos |
| Crear pagos | Si | Si |
| Aplicar pagos | Solo a sus pedidos | A todos |
| Crear/gestionar envios | No | Si |
| Ver envios | Solo de sus pedidos | Todos |
| Usar chatbot | Si | Si |
| Panel admin (/admin/) | No | Si |

---

## Paginacion

Todos los endpoints de listar (GET) devuelven resultados paginados:

```json
{
    "count": 50,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [ ... ]
}
```

- `count`: Total de resultados
- `next`: URL de la siguiente pagina (null si es la ultima)
- `previous`: URL de la pagina anterior (null si es la primera)
- `results`: Array con los datos (por defecto 10 items por pagina)

Puedes cambiar el tamaño: `?page_size=20` (maximo 100)

---

## Errores comunes

### 401 Unauthorized
```json
{"detail": "Authentication credentials were not provided."}
```
> No enviaste el token o el token expiro. Haz login de nuevo o usa token/refresh.

### 403 Forbidden
```json
{"detail": "You do not have permission to perform this action."}
```
> No tienes permisos. Probablemente necesitas ser admin.

### 404 Not Found
```json
{"detail": "No encontrado."}
```
> El recurso (producto, pedido, etc.) no existe o no tienes acceso.

### 400 Bad Request
```json
{"campo": ["Mensaje de error especifico"]}
```
> Los datos que enviaste son invalidos. Lee el mensaje para saber que corregir.

---

## Tareas asincronas (Celery)

La app tiene 2 tareas que se ejecutan en segundo plano (no bloquean la respuesta HTTP):

1. **send_shipment_notification**: Se ejecuta automaticamente cuando un envio cambia a "shipped" o "delivered". En produccion enviaria emails o SMS.

2. **check_delayed_shipments**: Tarea programada que revisa envios pendientes con mas de 3 dias. Registra alertas para que el admin los revise.

---

## Variables de entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| SECRET_KEY | Clave secreta de Django (seguridad) | dev-key (cambiar en produccion!) |
| DEBUG | Modo debug (True=desarrollo, False=produccion) | True |
| ALLOWED_HOSTS | Dominios permitidos | localhost,127.0.0.1 |
| CELERY_BROKER_URL | URL de Redis para Celery | redis://localhost:6379/0 |
| CELERY_RESULT_BACKEND | URL de Redis para resultados | redis://localhost:6379/0 |
| ANTHROPIC_API_KEY | API key de Claude para el chatbot | (vacio) |
| CORS_ALLOWED_ORIGINS | Origenes permitidos para CORS | http://localhost:3000 |

---

## Tecnologias usadas

| Tecnologia | Version | Para que se usa |
|------------|---------|-----------------|
| Python | 3.12 | Lenguaje de programacion |
| Django | 5.0.1 | Framework web |
| Django REST Framework | 3.14.0 | Crear APIs REST |
| SimpleJWT | 5.3.1 | Autenticacion con tokens JWT |
| Celery | 5.3.4 | Tareas asincronas en segundo plano |
| Redis | 7 | Broker de mensajes para Celery |
| Gunicorn | 21.2.0 | Servidor HTTP para produccion |
| WhiteNoise | 6.6.0 | Servir archivos estaticos en produccion |
| SQLite | 3 | Base de datos |
| Anthropic SDK | 0.39+ | Conexion con Claude IA |
| drf-spectacular | 0.27.0 | Documentacion API automatica (Swagger) |
| Docker | - | Contenedores para despliegue |
