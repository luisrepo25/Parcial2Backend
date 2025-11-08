"""
Vistas para el módulo de ventas
Maneja endpoints para checkout con Stripe, webhooks y consulta de compras
"""
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import os

from sales.service import service_stripe, service_sale
from users.services.jwt import jwt_required
from sales.models import NotaVenta
from notifications.services import fcm_service

# Configurar logging
logger = logging.getLogger(__name__)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def crear_checkout(request):
    """
    Crea una sesión de checkout en Stripe
    
    Body esperado:
    {
        "items": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 3, "cantidad": 1}
        ]
    }
    
    Response:
    {
        "ok": true,
        "session_id": "cs_test_...",
        "url": "https://checkout.stripe.com/...",
        "nota_venta_id": 1
    }
    """
    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        
        if not items_data:
            return JsonResponse({
                'ok': False,
                'error': 'Se requiere al menos un item en la compra'
            }, status=400)
        
        # Validar disponibilidad de productos
        items_validados = service_sale.validar_items_disponibles(items_data)
        
        # Crear nota de venta
        nota_venta = service_sale.crear_nota_venta(
            usuario_id=request.usuario.id,
            items=items_data,
            metodo_pago_nombre='Tarjeta'
        )
        
        # Preparar items para Stripe
        stripe_items = [
            {
                'producto': item['producto'],
                'cantidad': item['cantidad']
            }
            for item in items_validados
        ]
        
        # Crear sesión de Stripe
        session = service_stripe.crear_checkout_session(
            items=stripe_items,
            usuario_email=request.usuario.correo,
            metadata={
                'nota_venta_id': str(nota_venta.id),
                'usuario_id': str(request.usuario.id)
            }
        )
        
        # Actualizar nota de venta con session_id
        nota_venta.stripe_session_id = session.id
        nota_venta.save()
        
        logger.info(f"Checkout creado: NotaVenta #{nota_venta.id}, Session {session.id}")
        
        return JsonResponse({
            'ok': True,
            'session_id': session.id,
            'url': session.url,
            'nota_venta_id': nota_venta.id,
            'total': float(nota_venta.total)
        })
        
    except ValueError as e:
        logger.warning(f"Error de validación en checkout: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error al crear checkout: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al procesar la solicitud: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_stripe(request):
    """
    Endpoint para recibir webhooks de Stripe
    
    Eventos manejados:
    - checkout.session.completed: Pago completado exitosamente
    - payment_intent.payment_failed: Pago fallido
    - charge.refunded: Reembolso procesado
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Log para debugging
        logger.info("=" * 80)
        logger.info("🔔 WEBHOOK STRIPE RECIBIDO")
        logger.info(f"Signature: {sig_header[:20] if sig_header else 'NO SIGNATURE'}...")
        logger.info(f"Webhook secret configurado: {os.getenv('STRIPE_WEBHOOK_SECRET')[:10] if os.getenv('STRIPE_WEBHOOK_SECRET') else 'NO CONFIGURADO'}...")
        
        # Verificar la firma del webhook
        event = service_stripe.verificar_webhook_signature(payload, sig_header)
        
        logger.info(f"✅ Webhook verificado exitosamente")
        logger.info(f"Tipo de evento: {event['type']}")
        logger.info(f"Event ID: {event.get('id', 'N/A')}")
        
        # Manejar evento: Checkout completado
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            nota_venta_id = session['metadata'].get('nota_venta_id')
            session_id = session['id']
            payment_intent = session.get('payment_intent')
            
            logger.info(f"💰 CHECKOUT COMPLETADO")
            logger.info(f"   - Session ID: {session_id}")
            logger.info(f"   - Payment Intent: {payment_intent}")
            logger.info(f"   - Nota Venta ID (metadata): {nota_venta_id}")
            logger.info(f"   - Amount: {session.get('amount_total', 0) / 100}")
            logger.info(f"   - Customer Email: {session.get('customer_details', {}).get('email', 'N/A')}")
            
            if nota_venta_id:
                try:
                    logger.info(f"🔄 Intentando confirmar pago para NotaVenta #{nota_venta_id}...")
                    
                    service_sale.confirmar_pago(
                        nota_venta_id=int(nota_venta_id),
                        stripe_session_id=session_id,
                        stripe_payment_intent=payment_intent
                    )
                    
                    # Enviar por notifiacion al usuario que el pago fue confirmado
                    nota_venta = NotaVenta.objects.get(id=nota_venta_id)
                    fcm_service.enviar_notificacion_usuario(
                        usuario_id=nota_venta.usuario_id,
                        titulo="Pago Confirmado",
                        mensaje=f"Tu pago para la NotaVenta #{nota_venta_id} ha sido confirmado.",
                        data={
                            "tipo": "pago_confirmado",
                            "nota_venta_id": str(nota_venta_id)
                        }
                    )


                    logger.info(f"✅ PAGO CONFIRMADO EXITOSAMENTE: NotaVenta #{nota_venta_id}")
                    logger.info("=" * 80)
                    
                except NotaVenta.DoesNotExist:
                    logger.error(f"❌ NotaVenta #{nota_venta_id} NO ENCONTRADA en la base de datos")
                except Exception as e:
                    logger.error(f"❌ ERROR al confirmar pago: {str(e)}")
                    logger.error(f"Tipo de error: {type(e).__name__}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"⚠️ No se encontró nota_venta_id en metadata del checkout")
        
        # Manejar evento: Pago fallido
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']
            
            try:
                nota_venta = NotaVenta.objects.get(
                    stripe_payment_intent=payment_intent_id
                )
                service_sale.marcar_pago_fallido(nota_venta.id)
                logger.warning(f"Pago fallido: NotaVenta #{nota_venta.id}")
            except NotaVenta.DoesNotExist:
                logger.warning(f"NotaVenta no encontrada para payment_intent {payment_intent_id}")
        
        # Manejar evento: Reembolso
        elif event['type'] == 'charge.refunded':
            charge = event['data']['object']
            payment_intent_id = charge.get('payment_intent')
            
            if payment_intent_id:
                try:
                    nota_venta = NotaVenta.objects.get(
                        stripe_payment_intent=payment_intent_id
                    )
                    service_sale.procesar_reembolso(nota_venta.id)
                    logger.info(f"Reembolso procesado: NotaVenta #{nota_venta.id}")
                except NotaVenta.DoesNotExist:
                    logger.warning(f"NotaVenta no encontrada para reembolso {payment_intent_id}")
                except ValueError as e:
                    logger.error(f"Error al procesar reembolso: {str(e)}")
        
        return HttpResponse(status=200)
        
    except ValueError:
        logger.error("Payload inválido en webhook")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return HttpResponse(status=400)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def mis_compras(request):
    """
    Obtiene todas las compras del usuario autenticado
    
    Query params opcionales:
    - estado: filtrar por estado (pendiente, pagada, fallida, etc.)
    
    Response:
    {
        "ok": true,
        "compras": [...],
        "estadisticas": {...}
    }
    """
    try:
        estado = request.GET.get('estado', None)
        
        # Obtener ventas del usuario
        ventas = service_sale.obtener_ventas_usuario(
            usuario_id=request.usuario.id,
            estado=estado
        )
        
        # Obtener estadísticas
        estadisticas = service_sale.obtener_estadisticas_ventas_usuario(
            request.usuario.id
        )
        
        return JsonResponse({
            'ok': True,
            'compras': [{
                'id': v.id,
                'total': float(v.total),
                'estado': v.estado,
                'metodo_pago': v.metodo_pago.nombre,
                'created_at': v.created_at.isoformat(),
                'detalles': [{
                    'producto': {
                        'id': d.producto.id,
                        'nombre': d.producto.nombre,
                        'imagen_url': d.producto.imagen_url
                    },
                    'cantidad': d.cantidad,
                    'precio_unitario': float(d.precio_unitario),
                    'subtotal': float(d.subtotal)
                } for d in v.detalles.all()]
            } for v in ventas],
            'estadisticas': {
                'total_compras': estadisticas['total_compras'],
                'compras_pagadas': estadisticas['compras_pagadas'],
                'compras_pendientes': estadisticas['compras_pendientes'],
                'total_gastado': float(estadisticas['total_gastado'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error al obtener compras: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al obtener compras: {str(e)}'
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def detalle_compra(request, venta_id):
    """
    Obtiene el detalle completo de una compra específica
    
    Response:
    {
        "ok": true,
        "compra": {...}
    }
    """
    try:
        venta = service_sale.obtener_detalle_venta(venta_id)
        
        # Verificar que la venta pertenece al usuario autenticado
        if venta.usuario_id != request.usuario.id:
            return JsonResponse({
                'ok': False,
                'error': 'No tienes permiso para ver esta compra'
            }, status=403)
        
        return JsonResponse({
            'ok': True,
            'compra': {
                'id': venta.id,
                'total': float(venta.total),
                'estado': venta.estado,
                'metodo_pago': {
                    'nombre': venta.metodo_pago.nombre,
                    'descripcion': venta.metodo_pago.descripcion
                },
                'created_at': venta.created_at.isoformat(),
                'updated_at': venta.updated_at.isoformat(),
                'usuario': {
                    'email': venta.usuario.correo
                },
                'detalles': [{
                    'producto': {
                        'id': d.producto.id,
                        'nombre': d.producto.nombre,
                        'descripcion': d.producto.descripcion,
                        'imagen_url': d.producto.imagen_url,
                        'categoria': d.producto.categoria.nombre,
                        'marca': d.producto.marca.nombre,
                        'garantia': {
                            'cobertura': d.producto.garantia.cobertura
                        } if d.producto.garantia else None
                    },
                    'cantidad': d.cantidad,
                    'precio_unitario': float(d.precio_unitario),
                    'subtotal': float(d.subtotal)
                } for d in venta.detalles.all()]
            }
        })
        
    except NotaVenta.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Compra no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error al obtener detalle de compra: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al obtener detalle: {str(e)}'
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def solicitar_reembolso(request, venta_id):
    """
    Solicita un reembolso para una compra
    
    Response:
    {
        "ok": true,
        "message": "Reembolso procesado exitosamente"
    }
    """
    try:
        venta = NotaVenta.objects.get(id=venta_id)
        
        # Verificar que la venta pertenece al usuario
        if venta.usuario_id != request.usuario.id:
            return JsonResponse({
                'ok': False,
                'error': 'No tienes permiso para solicitar reembolso de esta compra'
            }, status=403)
        
        # Crear reembolso en Stripe
        if venta.stripe_payment_intent:
            service_stripe.crear_reembolso(
                payment_intent_id=venta.stripe_payment_intent,
                reason='requested_by_customer'
            )
        
        # El webhook de Stripe se encargará de actualizar el estado
        # Pero podemos procesarlo aquí también
        service_sale.procesar_reembolso(venta_id)
        
        logger.info(f"Reembolso solicitado: NotaVenta #{venta_id}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Reembolso procesado exitosamente'
        })
        
    except NotaVenta.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Compra no encontrada'
        }, status=404)
    except ValueError as e:
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error al solicitar reembolso: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al procesar reembolso: {str(e)}'
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def verificar_session(request, session_id):
    """
    Verifica el estado de una sesión de Stripe
    
    Response:
    {
        "ok": true,
        "session": {...},
        "nota_venta": {...}
    }
    """
    try:
        logger.info(f"🔍 Verificando session: {session_id}")
        
        # Obtener sesión de Stripe
        session = service_stripe.obtener_session(session_id)
        logger.info(f"   Stripe Status: {session.status}")
        logger.info(f"   Payment Status: {session.payment_status}")
        
        # Buscar nota de venta asociada
        nota_venta = NotaVenta.objects.get(stripe_session_id=session_id)
        logger.info(f"   NotaVenta #{nota_venta.id} - Estado DB: {nota_venta.estado}")
        
        # Verificar que pertenece al usuario
        if nota_venta.usuario_id != request.usuario.id:
            logger.warning(f"⚠️ Usuario {request.usuario.id} intentó acceder a venta de usuario {nota_venta.usuario_id}")
            return JsonResponse({
                'ok': False,
                'error': 'No autorizado'
            }, status=403)
        
        return JsonResponse({
            'ok': True,
            'session': {
                'id': session.id,
                'status': session.status,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total / 100,  # Convertir de centavos
            },
            'nota_venta': {
                'id': nota_venta.id,
                'estado': nota_venta.estado,
                'total': float(nota_venta.total)
            }
        })
        
    except NotaVenta.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Nota de venta no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error al verificar sesión: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar sesión: {str(e)}'
        }, status=500)
