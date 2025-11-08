"""
Servicio para integración con Stripe
Maneja la creación de sesiones de pago, webhooks y reembolsos
"""
import stripe
import os
from django.conf import settings

# Configurar la API key de Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def crear_checkout_session(items, usuario_email, metadata=None):
    """
    Crea una sesión de checkout en Stripe
    
    Args:
        items: Lista de items con formato [{'producto': Producto, 'cantidad': int}]
        usuario_email: Email del usuario
        metadata: Datos adicionales (ej: usuario_id, nota_venta_id)
    
    Returns:
        Stripe Session object con url de pago y session_id
    
    Raises:
        stripe.error.StripeError: Si hay error en la API de Stripe
    """
    try:
        line_items = []
        
        for item in items:
            producto = item['producto']
            cantidad = item['cantidad']
            
            # Stripe requiere el precio en centavos
            precio_en_centavos = int(float(producto.precio) * 100)
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',  # Puedes cambiar a 'bob' para bolivianos
                    'product_data': {
                        'name': producto.nombre,
                        'description': producto.descripcion[:500] if producto.descripcion else '',
                        'images': [producto.imagen_url] if producto.imagen_url else [],
                    },
                    'unit_amount': precio_en_centavos,
                },
                'quantity': cantidad,
            })
        
        # Obtener el primer origen CORS permitido para las URLs de redirección
        cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')
        success_url = f"{cors_origins.split(',')[0]}/tienda/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{cors_origins.split(',')[0]}/tienda/checkout/cancel"
        
        # Crear la sesión de checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=usuario_email,
            metadata=metadata or {},
        )
        
        return session
        
    except Exception as e:
        raise Exception(f"Error al crear sesión de Stripe: {str(e)}")


def verificar_webhook_signature(payload, sig_header):
    """
    Verifica la firma del webhook de Stripe para asegurar que la petición
    es auténtica y viene de Stripe
    
    Args:
        payload: Body del request (bytes)
        sig_header: Header 'Stripe-Signature' de la petición
    
    Returns:
        Event object de Stripe si la firma es válida
    
    Raises:
        ValueError: Si el payload es inválido
        stripe.error.SignatureVerificationError: Si la firma no coincide
    """
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        raise ValueError('STRIPE_WEBHOOK_SECRET no está configurado')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError as e:
        raise ValueError('Payload inválido')
    except Exception as e:
        # Captura cualquier error de Stripe durante la verificación
        raise Exception(f'Error al verificar firma del webhook: {str(e)}')


def obtener_session(session_id):
    """
    Obtiene los detalles de una sesión de checkout
    
    Args:
        session_id: ID de la sesión de Stripe
    
    Returns:
        Session object con todos los detalles
    """
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise Exception(f"Error al obtener sesión: {str(e)}")


def crear_reembolso(payment_intent_id, amount=None, reason=None):
    """
    Crea un reembolso total o parcial
    
    Args:
        payment_intent_id: ID del payment intent a reembolsar
        amount: Cantidad a reembolsar en centavos (None = reembolso completo)
        reason: Razón del reembolso ('duplicate', 'fraudulent', 'requested_by_customer')
    
    Returns:
        Refund object de Stripe
    """
    try:
        refund_data = {'payment_intent': payment_intent_id}
        
        if amount:
            refund_data['amount'] = amount
            
        if reason:
            refund_data['reason'] = reason
        
        return stripe.Refund.create(**refund_data)
        
    except Exception as e:
        raise Exception(f"Error al crear reembolso: {str(e)}")


def obtener_payment_intent(payment_intent_id):
    """
    Obtiene los detalles de un payment intent
    
    Args:
        payment_intent_id: ID del payment intent
    
    Returns:
        PaymentIntent object
    """
    try:
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception as e:
        raise Exception(f"Error al obtener payment intent: {str(e)}")


def cancelar_payment_intent(payment_intent_id):
    """
    Cancela un payment intent que aún no ha sido capturado
    
    Args:
        payment_intent_id: ID del payment intent a cancelar
    
    Returns:
        PaymentIntent object cancelado
    """
    try:
        return stripe.PaymentIntent.cancel(payment_intent_id)
    except Exception as e:
        raise Exception(f"Error al cancelar payment intent: {str(e)}")
