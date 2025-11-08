# 🔍 Guía para Revisar Logs del Pago

## 1. Iniciar el servidor con logs visibles

```powershell
cd "D:\MarioUniv\10mo\Matoneada Si2\Backend\app"
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

## 2. Hacer una prueba de pago

1. Ve al frontend y realiza una compra
2. Completa el pago en Stripe
3. Observa la consola del servidor

## 3. Buscar en los logs

### ✅ Logs que DEBES ver si todo funciona:

```
🔔 WEBHOOK STRIPE RECIBIDO
✅ Webhook verificado exitosamente
💰 CHECKOUT COMPLETADO
   - Session ID: cs_test_...
   - Payment Intent: pi_...
   - Nota Venta ID (metadata): 123
🔄 [confirmar_pago] Iniciando para NotaVenta #123
✅ NotaVenta encontrada - Estado actual: pendiente
💾 Actualizando información de Stripe y estado...
✅ Estado actualizado a: pagada
📦 Actualizando stock de productos...
✅ [confirmar_pago] Completado exitosamente
```

### ❌ Errores posibles:

#### Error 1: Webhook no llega

```
# NO aparece: "🔔 WEBHOOK STRIPE RECIBIDO"
# SOLUCIÓN: Verificar webhook secret en Stripe Dashboard
```

#### Error 2: NotaVenta no encontrada

```
❌ NotaVenta #123 NO EXISTE en la base de datos
# SOLUCIÓN: La venta no se creó correctamente antes del checkout
```

#### Error 3: Estado ya procesado

```
⚠️ La venta ya fue procesada con estado: pagada
# SOLUCIÓN: El webhook se ejecutó dos veces (normal, ignorar)
```

#### Error 4: Webhook secret incorrecto

```
❌ ERROR al verificar webhook signature
# SOLUCIÓN: Verificar STRIPE_WEBHOOK_SECRET en .env
```

## 4. Ver archivo de logs

También puedes revisar el archivo:

```
D:\MarioUniv\10mo\Matoneada Si2\Backend\app\debug.log
```

## 5. Verificar estado desde frontend

Después del pago, el frontend debe llamar:

```
GET /sales/verificar-session/{session_id}/
```

Y recibirás:

```json
{
  "ok": true,
  "session": {
    "status": "complete",
    "payment_status": "paid"
  },
  "nota_venta": {
    "estado": "pagada" // ← Debe ser "pagada" no "pendiente"
  }
}
```

## 🔥 Debugging en Producción (Render)

Si estás en producción:

1. Ve a Render Dashboard → Tu servicio
2. Click en "Logs"
3. Busca los mismos mensajes con emojis
4. Si no ves nada, el webhook NO está llegando a tu backend

### Verificar en Stripe:

1. Ve a Stripe Dashboard → Developers → Webhooks
2. Click en tu webhook endpoint
3. Pestaña "Recent deliveries"
4. Verás si Stripe envió el webhook y la respuesta que recibió

**Respuestas exitosas:** HTTP 200
**Respuestas fallidas:** HTTP 400/500 (ver mensaje de error)
