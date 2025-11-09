# 📦 API de Ventas - Documentación de Endpoints

## 🔐 Autenticación

Todos los endpoints (excepto el webhook) requieren autenticación JWT:

```
Authorization: Bearer {tu_token_jwt}
```

---

## 1. 🛒 Crear Checkout con Stripe

Crea una sesión de pago en Stripe y genera la URL para que el usuario complete el pago.

### Endpoint

```
POST /sales/checkout/create/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Body - Request

```json
{
  "items": [
    {
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "producto_id": 3,
      "cantidad": 1
    }
  ]
}
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "session_id": "cs_test_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0",
  "url": "https://checkout.stripe.com/c/pay/cs_test_a1B2c3D4e5F6g7H8i9J0...",
  "nota_venta_id": 15,
  "total": 299.98
}
```

**Uso:** Redirige al usuario a la `url` para que complete el pago en Stripe.

### Response - Error (400)

```json
{
  "ok": false,
  "error": "Se requiere al menos un item en la compra"
}
```

### Response - Error (400) - Stock insuficiente

```json
{
  "ok": false,
  "error": "Stock insuficiente para 'Refrigeradora LG'. Disponible: 5, Solicitado: 10"
}
```

### Response - Error (401) - Sin autenticación

```json
{
  "ok": false,
  "error": "Se requiere Authorization header"
}
```

### Response - Error (500)

```json
{
  "ok": false,
  "error": "Error al procesar la solicitud: [detalle del error]"
}
```

---

## 2. 📱 Crear Payment Intent (Apps Móviles)

Crea un Payment Intent para pagos nativos en aplicaciones móviles (Flutter, React Native, etc.). Este endpoint es específico para integrar Stripe directamente en la app móvil.

### Endpoint

```
POST /sales/create-payment/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Body - Request

```json
{
  "items": [
    {
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "producto_id": 3,
      "cantidad": 1
    }
  ]
}
```

**Nota:** El formato es idéntico al de `/checkout/create/`.

### Response - Éxito (200)

```json
{
  "ok": true,
  "clientSecret": "pi_3ABC123DEF456GHI_secret_xyz789ABC",
  "nota_venta_id": 15,
  "total": 299.98,
  "payment_intent_id": "pi_3ABC123DEF456GHI"
}
```

**Uso en Flutter:**

```dart
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// 1. Crear Payment Intent en tu backend
final response = await http.post(
  Uri.parse('$baseUrl/sales/create-payment/'),
  headers: {
    'Authorization': 'Bearer $token',
    'Content-Type': 'application/json'
  },
  body: jsonEncode({
    'items': [
      {'producto_id': 1, 'cantidad': 2},
      {'producto_id': 3, 'cantidad': 1}
    ]
  }),
);

final data = jsonDecode(response.body);
String clientSecret = data['clientSecret'];

// 2. Inicializar Payment Sheet
await Stripe.instance.initPaymentSheet(
  paymentSheetParameters: SetupPaymentSheetParameters(
    paymentIntentClientSecret: clientSecret,
    merchantDisplayName: 'Tu Tienda',
  ),
);

// 3. Presentar al usuario
await Stripe.instance.presentPaymentSheet();
```

### Response - Error (400) - Body inválido

```json
{
  "ok": false,
  "error": "Se requiere al menos un item en la compra"
}
```

### Response - Error (400) - Stock insuficiente

```json
{
  "ok": false,
  "error": "Stock insuficiente para 'Refrigeradora LG'. Disponible: 5, Solicitado: 10"
}
```

### Response - Error (401) - Sin autenticación

```json
{
  "ok": false,
  "error": "Se requiere Authorization header"
}
```

### Response - Error (500)

```json
{
  "ok": false,
  "error": "Error al procesar la solicitud: [detalle del error]"
}
```

### Diferencias con Checkout Web

| Característica   | Checkout Web (`/checkout/create/`) | Payment Intent (`/create-payment/`) |
| ---------------- | ---------------------------------- | ----------------------------------- |
| **Uso**          | Redirecciona a Stripe Checkout     | Pago nativo en la app               |
| **Body**         | `{"items": [...]}`                 | `{"items": [...]}` (mismo formato)  |
| **Response**     | URL de checkout                    | `clientSecret`                      |
| **Confirmación** | Automática por Stripe              | Manejada por la app                 |
| **UI**           | Stripe hosted page                 | UI personalizada en tu app          |

---

## 3. ✅ Verificar Sesión de Pago

Verifica el estado de una sesión de Stripe después de que el usuario complete (o cancele) el pago.

### Endpoint

```
GET /sales/checkout/verify/{session_id}/
```

### Ejemplo

```
GET /sales/checkout/verify/cs_test_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "session": {
    "id": "cs_test_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6",
    "status": "complete",
    "payment_status": "paid",
    "amount_total": 299.98
  },
  "nota_venta": {
    "id": 15,
    "estado": "pagada",
    "total": 299.98
  }
}
```

### Response - Error (404)

```json
{
  "ok": false,
  "error": "Nota de venta no encontrada"
}
```

### Response - Error (403)

```json
{
  "ok": false,
  "error": "No autorizado"
}
```

---

## 3. 🔔 Webhook de Stripe

**⚠️ Este endpoint NO requiere autenticación JWT.** Es llamado directamente por Stripe.

### Endpoint

```
POST /sales/webhook/stripe/
```

### Headers (enviados por Stripe)

```http
Stripe-Signature: t=1234567890,v1=abc123def456...
Content-Type: application/json
```

### Body - Request (ejemplo de checkout completado)

```json
{
  "id": "evt_1ABC2DEF3GHI4JKL",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_a1B2c3D4e5F6g7H8i9J0",
      "payment_intent": "pi_1ABC2DEF3GHI4JKL",
      "payment_status": "paid",
      "metadata": {
        "nota_venta_id": "15",
        "usuario_id": "42"
      }
    }
  }
}
```

### Response - Éxito (200)

```
(Sin body - HTTP 200)
```

### Response - Error (400)

```
(Sin body - HTTP 400)
```

**Eventos manejados:**

- `checkout.session.completed` → Confirma el pago (checkout web) y reduce stock
- `payment_intent.created` → Registra la creación de un payment intent (apps móviles)
- `payment_intent.succeeded` → Confirma el pago (apps móviles) y reduce stock
- `payment_intent.payment_failed` → Marca la venta como fallida
- `charge.refunded` → Procesa el reembolso y restaura stock

**Notificaciones push:** Se envían automáticamente al usuario cuando:

- ✅ Pago confirmado (`payment_intent.succeeded`)
- ❌ Pago fallido (`payment_intent.payment_failed`)

---

## 4. 📋 Listar Mis Compras

Obtiene todas las compras del usuario autenticado con estadísticas.

### Endpoint

```
GET /sales/mis-compras/
```

### Query Parameters (opcionales)

```
?estado=pagada
```

**Valores permitidos para `estado`:**

- `pendiente`
- `pagada`
- `fallida`
- `cancelada`
- `reembolsada`

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "compras": [
    {
      "id": 15,
      "total": 299.98,
      "estado": "pagada",
      "metodo_pago": "Tarjeta",
      "created_at": "2025-11-06T18:30:00Z",
      "detalles": [
        {
          "producto": {
            "id": 1,
            "nombre": "Refrigeradora LG 420L",
            "imagen_url": "https://res.cloudinary.com/..."
          },
          "cantidad": 2,
          "precio_unitario": 149.99,
          "subtotal": 299.98
        }
      ]
    },
    {
      "id": 14,
      "total": 89.99,
      "estado": "pendiente",
      "metodo_pago": "Tarjeta",
      "created_at": "2025-11-05T14:20:00Z",
      "detalles": [...]
    }
  ],
  "estadisticas": {
    "total_compras": 12,
    "compras_pagadas": 10,
    "compras_pendientes": 1,
    "total_gastado": 2450.85
  }
}
```

### Response - Error (401)

```json
{
  "ok": false,
  "error": "Se requiere Authorization header"
}
```

### Response - Error (500)

```json
{
  "ok": false,
  "error": "Error al obtener compras: [detalle del error]"
}
```

---

## 5. 📄 Detalle de Compra

Obtiene el detalle completo de una compra específica.

### Endpoint

```
GET /sales/mis-compras/{venta_id}/
```

### Ejemplo

```
GET /sales/mis-compras/15/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "compra": {
    "id": 15,
    "total": 299.98,
    "estado": "pagada",
    "metodo_pago": {
      "nombre": "Tarjeta",
      "descripcion": "Pago con tarjeta de crédito/débito a través de Stripe"
    },
    "created_at": "2025-11-06T18:30:00.123456Z",
    "updated_at": "2025-11-06T18:31:15.654321Z",
    "usuario": {
      "email": "usuario@example.com"
    },
    "detalles": [
      {
        "producto": {
          "id": 1,
          "nombre": "Refrigeradora LG 420L",
          "descripcion": "Refrigeradora de dos puertas con tecnología Inverter",
          "imagen_url": "https://res.cloudinary.com/...",
          "categoria": "Refrigeración",
          "marca": "LG",
          "garantia": {
            "cobertura_meses": 24,
            "marca": "LG"
          }
        },
        "cantidad": 2,
        "precio_unitario": 149.99,
        "subtotal": 299.98
      }
    ]
  }
}
```

### Response - Error (404)

```json
{
  "ok": false,
  "error": "Compra no encontrada"
}
```

### Response - Error (403)

```json
{
  "ok": false,
  "error": "No tienes permiso para ver esta compra"
}
```

---

## 6. 💸 Solicitar Reembolso

Solicita un reembolso para una compra pagada.

### Endpoint

```
POST /sales/reembolso/{venta_id}/
```

### Ejemplo

```
POST /sales/reembolso/15/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Body - Request

```
(Sin body requerido)
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "message": "Reembolso procesado exitosamente"
}
```

**Nota:** El webhook de Stripe actualizará el estado de la venta a `reembolsada` y restaurará el stock automáticamente.

### Response - Error (404)

```json
{
  "ok": false,
  "error": "Compra no encontrada"
}
```

### Response - Error (403)

```json
{
  "ok": false,
  "error": "No tienes permiso para solicitar reembolso de esta compra"
}
```

### Response - Error (400)

```json
{
  "ok": false,
  "error": "Solo se pueden reembolsar ventas pagadas. Estado actual: pendiente"
}
```

---

## 7. 📋 Listar Todas las Ventas (con Paginación)

Obtiene todas las notas de venta del sistema con paginación y filtros opcionales.

### Endpoint

```
GET /sales/ventas/
```

### Query Parameters (opcionales)

```
?page=1&page_size=10&estado=pagada&usuario_id=5
```

**Parámetros:**

- `page`: Número de página (default: 1)
- `page_size`: Tamaño de página (default: 10, max: 100)
- `estado`: Filtrar por estado (`pendiente`, `pagada`, `fallida`, `cancelada`, `reembolsada`)
- `usuario_id`: Filtrar por ID de usuario

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "ventas": [
    {
      "id": 15,
      "usuario": {
        "id": 5,
        "nombre": "Juan Pérez",
        "correo": "juan@example.com"
      },
      "estado": "pagada",
      "metodo_pago": "Tarjeta",
      "total": 299.98,
      "created_at": "2025-11-08T18:30:00.123456",
      "updated_at": "2025-11-08T18:31:15.654321",
      "cantidad_items": 3
    },
    {
      "id": 14,
      "usuario": {
        "id": 3,
        "nombre": "María López",
        "correo": "maria@example.com"
      },
      "estado": "pendiente",
      "metodo_pago": "Tarjeta",
      "total": 149.99,
      "created_at": "2025-11-07T14:20:00.123456",
      "updated_at": "2025-11-07T14:20:00.123456",
      "cantidad_items": 1
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 150,
    "total_pages": 15,
    "has_next": true,
    "has_previous": false
  }
}
```

### Response - Error (400)

```json
{
  "ok": false,
  "error": "Parámetros inválidos: invalid literal for int() with base 10: 'abc'"
}
```

### Response - Error (401)

```json
{
  "ok": false,
  "error": "Se requiere Authorization header"
}
```

---

## 8. 🔍 Detalle de Venta

Obtiene el detalle completo de una nota de venta específica, incluyendo todos los productos con cantidades y subtotales.

### Endpoint

```
GET /sales/ventas/{venta_id}/
```

### Ejemplo

```
GET /sales/ventas/15/
```

### Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response - Éxito (200)

```json
{
  "ok": true,
  "venta": {
    "id": 15,
    "usuario": {
      "id": 5,
      "nombre": "Juan Pérez",
      "correo": "juan@example.com"
    },
    "estado": "pagada",
    "metodo_pago": {
      "nombre": "Tarjeta",
      "descripcion": "Pago con tarjeta de crédito/débito a través de Stripe"
    },
    "total": 299.98,
    "stripe_session_id": "cs_test_a1B2c3D4e5F6g7H8i9J0",
    "stripe_payment_intent": "pi_1ABC2DEF3GHI4JKL",
    "created_at": "2025-11-08T18:30:00.123456",
    "updated_at": "2025-11-08T18:31:15.654321",
    "productos": [
      {
        "producto_id": 1,
        "nombre": "Refrigeradora LG 420L",
        "descripcion": "Refrigeradora de dos puertas con tecnología Inverter",
        "imagen_url": "https://res.cloudinary.com/...",
        "categoria": "Refrigeración",
        "marca": "LG",
        "cantidad": 2,
        "precio_unitario": 149.99,
        "subtotal": 299.98,
        "garantia": {
          "cobertura_meses": 24,
          "marca": "LG"
        }
      }
    ]
  }
}
```

### Response - Error (404)

```json
{
  "ok": false,
  "error": "Nota de venta #999 no encontrada"
}
```

### Response - Error (401)

```json
{
  "ok": false,
  "error": "Se requiere Authorization header"
}
```

---

## 🔄 Flujos de Compra

### Flujo Web (Checkout)

```mermaid
sequenceDiagram
    participant F as Frontend Web
    participant B as Backend
    participant S as Stripe
    participant W as Webhook

    F->>B: POST /sales/checkout/create/
    B->>B: Crea NotaVenta (pendiente)
    B->>S: Crear Session
    S-->>B: session_id + url
    B-->>F: {url, session_id, nota_venta_id}
    F->>S: Redirigir a Stripe Checkout
    Note over S: Usuario completa pago
    S->>W: POST /webhook/stripe/ (checkout.session.completed)
    W->>B: Confirmar pago
    B->>B: Estado = "pagada", reduce stock
    W-->>S: 200 OK
    S->>F: Redirige a success_url?session_id=...
    F->>B: GET /checkout/verify/{session_id}/
    B-->>F: {estado: "pagada", total: ...}
```

### Flujo Móvil (Payment Intent)

```mermaid
sequenceDiagram
    participant A as App Móvil
    participant B as Backend
    participant S as Stripe SDK
    participant W as Webhook

    A->>B: POST /sales/create-payment/
    B->>B: Crea NotaVenta (pendiente)
    B->>S: Crear Payment Intent
    S-->>B: clientSecret + payment_intent_id
    B-->>A: {clientSecret, nota_venta_id, total}
    A->>S: initPaymentSheet(clientSecret)
    A->>S: presentPaymentSheet()
    Note over A,S: Usuario ingresa datos de tarjeta
    S->>W: payment_intent.succeeded
    W->>B: Confirmar pago
    B->>B: Estado = "pagada", reduce stock
    B->>A: Enviar notificación push
    W-->>S: 200 OK
    S-->>A: Payment Success
    A->>B: GET /mis-compras/{nota_venta_id}/
    B-->>A: {estado: "pagada", detalles: ...}
```

---

## 📊 Estados de NotaVenta

| Estado        | Descripción                           | ¿Se puede reembolsar? |
| ------------- | ------------------------------------- | --------------------- |
| `pendiente`   | Esperando pago                        | ❌                    |
| `pagada`      | Pago confirmado, stock reducido       | ✅                    |
| `fallida`     | Pago rechazado                        | ❌                    |
| `cancelada`   | Cancelada por usuario/sistema         | ❌                    |
| `reembolsada` | Reembolso procesado, stock restaurado | ❌                    |

---

## 🧪 Tarjetas de Prueba Stripe

Para probar en modo test:

| Escenario                 | Número de Tarjeta     | CVC | Fecha |
| ------------------------- | --------------------- | --- | ----- |
| ✅ Pago exitoso           | `4242 4242 4242 4242` | 123 | 12/30 |
| 🔐 Requiere autenticación | `4000 0025 0000 3155` | 123 | 12/30 |
| ❌ Pago rechazado         | `4000 0000 0000 9995` | 123 | 12/30 |

---

## 🔗 Endpoints Disponibles

| Endpoint                               | Método | Uso                                | Autenticación |
| -------------------------------------- | ------ | ---------------------------------- | ------------- |
| `/sales/checkout/create/`              | POST   | Checkout web con Stripe            | ✅ JWT        |
| `/sales/create-payment/`               | POST   | Payment Intent para apps móviles   | ✅ JWT        |
| `/sales/checkout/verify/{session_id}/` | GET    | Verificar estado de checkout web   | ✅ JWT        |
| `/sales/webhook/stripe/`               | POST   | Webhook de Stripe                  | ❌ Sin auth   |
| `/sales/mis-compras/`                  | GET    | Listar compras del usuario         | ✅ JWT        |
| `/sales/mis-compras/{id}/`             | GET    | Detalle de compra específica       | ✅ JWT        |
| `/sales/reembolso/{id}/`               | POST   | Solicitar reembolso                | ✅ JWT        |
| `/sales/ventas/`                       | GET    | Listar todas las ventas (paginado) | ✅ JWT        |
| `/sales/ventas/{id}/`                  | GET    | Detalle completo de venta          | ✅ JWT        |

## 🔗 URLs Base

**Desarrollo:**

```
http://localhost:8000/sales/
```

**Producción:**

```
https://parcial2backend.onrender.com/sales/
```

---

## 📝 Notas Importantes

1. **Webhook URL:** Debe configurarse en Stripe Dashboard apuntando a:

   ```
   https://tu-dominio.com/sales/webhook/stripe/
   ```

2. **CORS:** Asegúrate de que tu frontend esté en `CORS_ALLOWED_ORIGINS`

3. **JWT:** Los tokens expiran. Manejar error 401 y redirigir a login

4. **Stock:** Se reduce automáticamente al confirmar pago, se restaura al reembolsar

5. **Moneda:** Actualmente configurado en USD. Cambiar a BOB si es necesario

6. **Apps Móviles:** Para Flutter, usa el paquete `flutter_stripe` con el `clientSecret` del endpoint `/create-payment/`

7. **Notificaciones Push:** Se envían automáticamente al confirmar pagos y en caso de fallo (requiere FCM token registrado)

---

## 🚨 Códigos de Error HTTP

| Código | Significado                     |
| ------ | ------------------------------- |
| 200    | Éxito                           |
| 400    | Petición inválida (bad request) |
| 401    | No autenticado                  |
| 403    | No autorizado (forbidden)       |
| 404    | Recurso no encontrado           |
| 500    | Error interno del servidor      |
