from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from users.models import Usuario
from users.services.jwt import jwt_required
from .services import fcm_service
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def registrar_token_fcm(request):
    """
    Registra el token FCM del dispositivo del usuario
    
    Body:
    {
        "token": "fcm_token_del_dispositivo"
    }
    
    Response:
    {
        "ok": true,
        "message": "Token FCM registrado exitosamente"
    }
    """
    try:
        data = json.loads(request.body)
        fcm_token = data.get('token')
        
        if not fcm_token:
            return JsonResponse({
                'ok': False,
                'error': 'Token FCM requerido'
            }, status=400)
        
        # Actualizar token del usuario (disponible en request.usuario gracias al decorador)
        request.usuario.fcm_token = fcm_token
        request.usuario.save()
        
        logger.info(f"✅ Token FCM registrado para usuario {request.usuario.correo}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Token FCM registrado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"❌ Error al registrar token FCM: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["DELETE"])
def eliminar_token_fcm(request):
    """
    Elimina el token FCM del usuario (útil al hacer logout)
    
    Response:
    {
        "ok": true,
        "message": "Token FCM eliminado"
    }
    """
    try:
        request.usuario.fcm_token = None
        request.usuario.save()
        
        logger.info(f"✅ Token FCM eliminado para usuario {request.usuario.correo}")
        
        return JsonResponse({
            'ok': True,
            'message': 'Token FCM eliminado'
        })
        
    except Exception as e:
        logger.error(f"❌ Error al eliminar token FCM: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def enviar_notificacion_test(request):
    """
    Endpoint de prueba para enviar una notificación
    
    Body:
    {
        "titulo": "Título de prueba",
        "mensaje": "Mensaje de prueba"
    }
    
    Response:
    {
        "ok": true,
        "resultado": {
            "success": true,
            "message_id": "..."
        }
    }
    """
    try:
        if not request.usuario.fcm_token:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no tiene token FCM registrado. Debe registrar su dispositivo primero.'
            }, status=400)
        
        data = json.loads(request.body)
        titulo = data.get('titulo', '🧪 Notificación de Prueba')
        mensaje = data.get('mensaje', 'Si ves esto, las notificaciones funcionan correctamente!')
        
        resultado = fcm_service.enviar_notificacion_fcm(
            token=request.usuario.fcm_token,
            titulo=titulo,
            mensaje=mensaje,
            data={
                'tipo': 'test',
                'usuario_id': str(request.usuario.id)
            }
        )
        
        return JsonResponse({
            'ok': resultado['success'],
            'resultado': resultado
        })
        
    except Usuario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Usuario no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación de prueba: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def suscribir_tema(request):
    """
    Suscribe al usuario a un tema de notificaciones
    
    Body:
    {
        "tema": "ofertas"
    }
    
    Response:
    {
        "ok": true,
        "message": "Suscrito al tema 'ofertas'"
    }
    """
    try:
        if not request.usuario.fcm_token:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no tiene token FCM registrado'
            }, status=400)
        
        data = json.loads(request.body)
        tema = data.get('tema')
        
        if not tema:
            return JsonResponse({
                'ok': False,
                'error': 'Tema requerido'
            }, status=400)
        
        resultado = fcm_service.suscribir_a_tema(request.usuario.fcm_token, tema)
        
        if resultado['success']:
            return JsonResponse({
                'ok': True,
                'message': f"Suscrito al tema '{tema}'"
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error desconocido')
            }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Error al suscribir a tema: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def enviar_notificacion_usuario(request):
    """
    Envía una notificación a un usuario específico
    
    Body:
    {
        "usuario_id": 123,
        "titulo": "Nueva oferta disponible",
        "mensaje": "50% de descuento en electrodomésticos",
        "data": {
            "tipo": "oferta",
            "descuento": "50",
            "url": "/productos/ofertas"
        }
    }
    
    Response:
    {
        "ok": true,
        "mensaje": "Notificación enviada exitosamente",
        "destinatario": "usuario@email.com"
    }
    """
    try:
        
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        titulo = data.get('titulo')
        mensaje = data.get('mensaje')
        extra_data = data.get('data', {})
        
        # Validar campos requeridos
        if not all([usuario_id, titulo, mensaje]):
            return JsonResponse({
                'ok': False,
                'error': 'usuario_id, titulo y mensaje son requeridos'
            }, status=400)
        
        # Obtener usuario destinatario
        try:
            destinatario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': f'Usuario con ID {usuario_id} no encontrado'
            }, status=404)
        
        # Verificar que tenga token FCM
        if not destinatario.fcm_token:
            return JsonResponse({
                'ok': False,
                'error': 'El usuario no tiene notificaciones habilitadas'
            }, status=400)
        
        # Enviar notificación
        resultado = fcm_service.enviar_notificacion_fcm(
            token=destinatario.fcm_token,
            titulo=titulo,
            mensaje=mensaje,
            data=extra_data
        )
        
        if resultado['success']:
            logger.info(f"📤 Notificación enviada a {destinatario.correo}")
            return JsonResponse({
                'ok': True,
                'mensaje': 'Notificación enviada exitosamente',
                'destinatario': destinatario.correo
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error al enviar notificación')
            }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def enviar_notificacion_masiva(request):
    """
    Envía una notificación a todos los usuarios con tokens FCM
    
    Body:
    {
        "titulo": "¡Black Friday!",
        "mensaje": "Hasta 70% de descuento en toda la tienda",
        "data": {
            "tipo": "promocion",
            "evento": "black_friday"
        }
    }
    
    Response:
    {
        "ok": true,
        "mensaje": "Notificación enviada",
        "enviadas": 45,
        "fallidas": 2
    }
    """
    try:
        
        data = json.loads(request.body)
        titulo = data.get('titulo')
        mensaje = data.get('mensaje')
        extra_data = data.get('data', {})
        
        # Validar campos requeridos
        if not all([titulo, mensaje]):
            return JsonResponse({
                'ok': False,
                'error': 'titulo y mensaje son requeridos'
            }, status=400)
        
        # Obtener todos los tokens FCM de usuarios activos
        usuarios_con_token = Usuario.objects.filter(
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        
        if not usuarios_con_token.exists():
            return JsonResponse({
                'ok': False,
                'error': 'No hay usuarios con notificaciones habilitadas'
            }, status=400)
        
        tokens = [u.fcm_token for u in usuarios_con_token]
        
        logger.info(f"📤 Enviando notificación masiva a {len(tokens)} usuarios")
        
        # Enviar notificación a todos
        resultado = fcm_service.enviar_notificacion_multiple(
            tokens=tokens,
            titulo=titulo,
            mensaje=mensaje,
            data=extra_data
        )
        
        if resultado['success']:
            return JsonResponse({
                'ok': True,
                'mensaje': 'Notificación masiva enviada',
                'enviadas': resultado['success_count'],
                'fallidas': resultado['failure_count'],
                'total_usuarios': len(tokens)
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error al enviar notificaciones')
            }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación masiva: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def enviar_notificacion_por_tema(request):
    """
    Envía notificación a todos los usuarios suscritos a un tema
    
    Body:
    {
        "tema": "ofertas",
        "titulo": "Nueva oferta de laptops",
        "mensaje": "MacBook Pro con 30% de descuento",
        "data": {
            "tipo": "oferta",
            "categoria": "laptops"
        }
    }
    
    Response:
    {
        "ok": true,
        "mensaje": "Notificación enviada al tema 'ofertas'"
    }
    """
    try:
        
        data = json.loads(request.body)
        tema = data.get('tema')
        titulo = data.get('titulo')
        mensaje = data.get('mensaje')
        extra_data = data.get('data', {})
        
        # Validar campos requeridos
        if not all([tema, titulo, mensaje]):
            return JsonResponse({
                'ok': False,
                'error': 'tema, titulo y mensaje son requeridos'
            }, status=400)
        
        # Enviar notificación al tema
        resultado = fcm_service.enviar_notificacion_por_tema(
            tema=tema,
            titulo=titulo,
            mensaje=mensaje,
            data=extra_data
        )
        
        if resultado['success']:
            logger.info(f"📤 Notificación enviada al tema '{tema}'")
            return JsonResponse({
                'ok': True,
                'mensaje': f"Notificación enviada al tema '{tema}'"
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error al enviar notificación')
            }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación por tema: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def obtener_mis_notificaciones(request):
    """
    Obtiene todas las notificaciones del usuario autenticado
    
    Query params:
    - no_leidas: Si es "true", solo retorna notificaciones no leídas
    
    Response:
    {
        "ok": true,
        "notificaciones": [...],
        "total": 10
    }
    """
    try:
        solo_no_leidas = request.GET.get('no_leidas', 'false').lower() == 'true'
        
        resultado = fcm_service.obtener_notificaciones_usuario(
            idUsuario=request.usuario.id,
            solo_no_leidas=solo_no_leidas
        )
        
        if resultado['success']:
            return JsonResponse({
                'ok': True,
                'notificaciones': resultado['notificaciones'],
                'total': resultado['total']
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error al obtener notificaciones')
            }, status=500)
        
    except Exception as e:
        logger.error(f"❌ Error al obtener notificaciones: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@jwt_required
@require_http_methods(["PUT"])
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación como leída para el usuario autenticado
    
    Params:
    - notificacion_id: ID de la notificación
    
    Response:
    {
        "ok": true,
        "message": "Notificación marcada como leída"
    }
    """
    try:
        resultado = fcm_service.leer_notificacion(
            idUsuario=request.usuario.id,
            idNotificacion=notificacion_id
        )
        
        if resultado['success']:
            return JsonResponse({
                'ok': True,
                'message': resultado['message']
            })
        else:
            return JsonResponse({
                'ok': False,
                'error': resultado.get('error', 'Error al marcar notificación')
            }, status=404 if 'no encontrada' in resultado.get('error', '') else 500)
        
    except Exception as e:
        logger.error(f"❌ Error al marcar notificación: {str(e)}")
        return JsonResponse({
            'ok': False,
            'error': str(e)
        }, status=500)
