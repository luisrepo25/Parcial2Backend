# 📱 API de Notificaciones Push - Documentación

## 📋 Índice

1. [Registro de Tokens](#registro-de-tokens)
2. [Envío de Notificaciones Individuales](#envío-individual)
3. [Envío de Notificaciones Masivas](#envío-masivo)
4. [Notificaciones por Tema](#notificaciones-por-tema)
5. [Casos de Uso Reales](#casos-de-uso)

---

## 🔐 Autenticación

Todos los endpoints requieren el header:

```
Authorization: Bearer {JWT_TOKEN}
```

---

## 1️⃣ Registro de Tokens

### Registrar Token FCM

**Endpoint:** `POST /notifications/register-token/`

**Cuándo usar:** Cuando el usuario abre la app por primera vez o inicia sesión.

**Request:**

```json
{
  "token": "fcm_token_del_dispositivo_obtenido_del_frontend"
}
```

**Response:**

```json
{
  "ok": true,
  "message": "Token FCM registrado exitosamente"
}
```

---

### Eliminar Token FCM

**Endpoint:** `DELETE /notifications/remove-token/`

**Cuándo usar:** Cuando el usuario cierra sesión.

**Response:**

```json
{
  "ok": true,
  "message": "Token FCM eliminado"
}
```

---

## 2️⃣ Envío Individual

### Enviar notificación a un usuario específico

**Endpoint:** `POST /notifications/send/`

**Cuándo usar:**

- Confirmar compra
- Cambio de estado de pedido
- Respuesta a soporte
- Mensaje personalizado

**Request:**

```json
{
  "usuario_id": 5,
  "titulo": "¡Tu pedido está en camino! 📦",
  "mensaje": "Tu pedido #12345 salió de nuestro almacén y llegará mañana",
  "data": {
    "tipo": "pedido",
    "pedido_id": "12345",
    "estado": "en_camino",
    "url": "/mis-pedidos/12345"
  }
}
```

**Response:**

```json
{
  "ok": true,
  "mensaje": "Notificación enviada exitosamente",
  "destinatario": "usuario@email.com"
}
```

---

## 3️⃣ Envío Masivo

### Enviar notificación a todos los usuarios

**Endpoint:** `POST /notifications/send-all/`

**Cuándo usar:**

- Anuncios importantes
- Mantenimiento programado
- Eventos especiales (Black Friday, Navidad)
- Nuevas funcionalidades

**Request:**

```json
{
  "titulo": "🎉 Black Friday - Hasta 70% OFF",
  "mensaje": "Las mejores ofertas del año están aquí. ¡No te las pierdas!",
  "data": {
    "tipo": "promocion",
    "evento": "black_friday",
    "url": "/ofertas/black-friday",
    "fecha_inicio": "2025-11-25",
    "fecha_fin": "2025-11-30"
  }
}
```

**Response:**

```json
{
  "ok": true,
  "mensaje": "Notificación masiva enviada",
  "enviadas": 1523,
  "fallidas": 12,
  "total_usuarios": 1535
}
```

---

## 4️⃣ Notificaciones por Tema

### Paso 1: Suscribir usuario a un tema

**Endpoint:** `POST /notifications/subscribe-topic/`

**Request:**

```json
{
  "tema": "ofertas_electrodomesticos"
}
```

**Temas sugeridos:**

- `ofertas_electrodomesticos`
- `nuevos_productos`
- `descuentos_exclusivos`
- `restock_favoritos`

---

### Paso 2: Enviar notificación al tema

**Endpoint:** `POST /notifications/send-topic/`

**Cuándo usar:**

- Ofertas de categorías específicas
- Nuevos productos por categoría
- Alertas de stock disponible

**Request:**

```json
{
  "tema": "ofertas_electrodomesticos",
  "titulo": "🔥 Flash Sale: Refrigeradores",
  "mensaje": "Solo hoy: 40% de descuento en refrigeradores Samsung",
  "data": {
    "tipo": "oferta",
    "categoria": "refrigeradores",
    "marca": "Samsung",
    "descuento": "40",
    "duracion": "24h",
    "url": "/productos/refrigeradores/samsung"
  }
}
```

**Response:**

```json
{
  "ok": true,
  "mensaje": "Notificación enviada al tema 'ofertas_electrodomesticos'"
}
```

---

## 5️⃣ Casos de Uso Reales

### 🛒 Caso 1: Confirmación de Compra

```json
POST /notifications/send/

{
  "usuario_id": 15,
  "titulo": "✅ Compra Confirmada",
  "mensaje": "Tu pedido por $1,250.00 ha sido confirmado",
  "data": {
    "tipo": "compra_confirmada",
    "pedido_id": "12345",
    "total": "1250.00",
    "fecha_entrega_estimada": "2025-11-15",
    "url": "/mis-compras/12345"
  }
}
```

---

### 📦 Caso 2: Actualización de Estado del Pedido

```json
POST /notifications/send/

{
  "usuario_id": 15,
  "titulo": "📦 Tu pedido fue entregado",
  "mensaje": "El pedido #12345 fue entregado exitosamente. ¡Disfrútalo!",
  "data": {
    "tipo": "pedido_entregado",
    "pedido_id": "12345",
    "fecha_entrega": "2025-11-14 14:30",
    "url": "/calificar-pedido/12345"
  }
}
```

---

### 🎁 Caso 3: Oferta Personalizada

```json
POST /notifications/send/

{
  "usuario_id": 15,
  "titulo": "🎁 Oferta especial para ti",
  "mensaje": "Como cliente frecuente, tienes 15% de descuento adicional",
  "data": {
    "tipo": "oferta_personalizada",
    "codigo_descuento": "CLIENTE15",
    "descuento": "15",
    "validez": "7d",
    "url": "/mi-cupon/CLIENTE15"
  }
}
```

---

### 🔔 Caso 4: Producto de Vuelta en Stock

```json
POST /notifications/send/

{
  "usuario_id": 15,
  "titulo": "🔔 Producto disponible",
  "mensaje": "El iPhone 15 Pro que agregaste a favoritos está de vuelta en stock",
  "data": {
    "tipo": "restock",
    "producto_id": "789",
    "producto_nombre": "iPhone 15 Pro",
    "precio": "1199.99",
    "stock": "5",
    "url": "/productos/789"
  }
}
```

---

### 💳 Caso 5: Recordatorio de Carrito Abandonado

```json
POST /notifications/send/

{
  "usuario_id": 15,
  "titulo": "🛒 Tu carrito te espera",
  "mensaje": "Tienes 3 productos en tu carrito. ¡Completa tu compra ahora!",
  "data": {
    "tipo": "carrito_abandonado",
    "items_count": "3",
    "total": "450.00",
    "url": "/carrito"
  }
}
```

---

### 🎉 Caso 6: Evento Masivo

```json
POST /notifications/send-all/

{
  "titulo": "🎉 Cyber Monday - Última Oportunidad",
  "mensaje": "Termina en 6 horas. No pierdas estas ofertas increíbles",
  "data": {
    "tipo": "evento_urgente",
    "evento": "cyber_monday",
    "tiempo_restante": "6h",
    "descuento_max": "70",
    "url": "/cyber-monday"
  }
}
```

---

## 🔥 Integración con Webhook de Stripe

Puedes enviar notificaciones automáticas cuando ocurra un pago. En `sales/views.py`:

```python
from notifications.services import fcm_service

@csrf_exempt
def webhook_stripe(request):
    # ... código existente ...

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        nota_venta_id = session['metadata'].get('nota_venta_id')

        if nota_venta_id:
            nota_venta = service_sale.confirmar_pago(...)

            # 🔔 Enviar notificación automática
            if nota_venta.usuario.fcm_token:
                fcm_service.enviar_notificacion_fcm(
                    token=nota_venta.usuario.fcm_token,
                    titulo="¡Pago Exitoso! 🎉",
                    mensaje=f"Tu compra de ${nota_venta.total} ha sido confirmada",
                    data={
                        'tipo': 'pago_exitoso',
                        'nota_venta_id': str(nota_venta.id),
                        'total': str(nota_venta.total),
                        'url': f'/mis-compras/{nota_venta.id}'
                    }
                )
```

---

## 📊 Estructura del campo `data`

El campo `data` es **opcional** pero muy útil para:

- **Navegación:** Redirigir al usuario a una pantalla específica
- **Acciones:** Ejecutar lógica cuando el usuario toca la notificación
- **Contexto:** Pasar información adicional a la app

**Ejemplo completo:**

```json
{
  "data": {
    "tipo": "oferta|pedido|alerta|promo|info",
    "id": "identificador_del_recurso",
    "url": "/ruta/en/la/app",
    "accion": "abrir_producto|ver_pedido|ir_carrito",
    "prioridad": "alta|media|baja",
    "fecha_expiracion": "2025-12-31T23:59:59Z"
    // ... cualquier otro dato personalizado
  }
}
```

---

## ⚠️ Errores Comunes

### Error: "Usuario no tiene token FCM registrado"

**Causa:** El usuario no llamó al endpoint `/notifications/register-token/`
**Solución:** Asegurar que el frontend registre el token al iniciar sesión

### Error: "Token no válido o expirado"

**Causa:** El token FCM expiró o el usuario desinstaló la app
**Solución:** Manejar el error y pedir al usuario que registre nuevamente el token

### Error: "No hay usuarios con notificaciones habilitadas"

**Causa:** Ningún usuario tiene un `fcm_token` en la base de datos
**Solución:** Verificar que el frontend esté registrando tokens correctamente

---

## 🚀 Ejemplos con cURL

### Enviar notificación individual:

```bash
curl -X POST http://localhost:8000/notifications/send/ \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": 1,
    "titulo": "Prueba",
    "mensaje": "Esta es una notificación de prueba",
    "data": {"tipo": "test"}
  }'
```

### Enviar notificación masiva:

```bash
curl -X POST http://localhost:8000/notifications/send-all/ \
  -H "Authorization: Bearer TU_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Anuncio Importante",
    "mensaje": "Mantenimiento programado mañana a las 2am",
    "data": {"tipo": "mantenimiento"}
  }'
```

---

## ✅ Checklist de Implementación

- [ ] Archivo `firebase-credentials.json` en la raíz del proyecto
- [ ] Variable `FIREBASE_CREDENTIALS_PATH` en `.env`
- [ ] Paquetes `firebase-admin` y `pyfcm` instalados
- [ ] App `notifications` registrada en `INSTALLED_APPS`
- [ ] URLs de notifications incluidas en `urls.py` principal
- [ ] Frontend configurado para obtener token FCM
- [ ] Frontend envía token al backend con `/register-token/`
- [ ] Probar con endpoint `/test/` antes de usar en producción
