import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
from users.models import Usuario

logger = logging.getLogger(__name__)

# Variable para verificar si ya está inicializado
_firebase_initialized = False


def inicializar_firebase():
    """Inicializa Firebase Admin SDK si no está inicializado"""
    global _firebase_initialized
    
    if not _firebase_initialized:
        try:
            # Verificar si ya hay una app inicializada
            firebase_admin.get_app()
            _firebase_initialized = True
            logger.info("✅ Firebase Admin SDK ya estaba inicializado")
        except ValueError:
            # No hay app inicializada, crear una nueva
            try:
                cred_path = os.path.join(settings.BASE_DIR, os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json'))
                
                if not os.path.exists(cred_path):
                    logger.error(f"❌ Archivo de credenciales no encontrado: {cred_path}")
                    raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                logger.info("✅ Firebase Admin SDK inicializado correctamente")
            except Exception as e:
                logger.error(f"❌ Error al inicializar Firebase: {str(e)}")
                raise


def enviar_notificacion_fcm(idUsuario, titulo, mensaje, data=None):
    """
    Envía una notificación push a un dispositivo específico
    
    Args:
        token: FCM token del dispositivo
        titulo: Título de la notificación
        mensaje: Cuerpo de la notificación
        data: Datos adicionales (dict)
    
    Returns:
        dict: Resultado del envío
    """
    try:
        inicializar_firebase()
        
        logger.info(f"📤 Enviando notificación a token: {token[:20]}...")

        # obtener el fcm token del usuario
        usuario = Usuario.objects.get(id=idUsuario)
        token = usuario.fcm_token
        
        # Construir mensaje
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data=data or {},
            token=token,
        )
        
        # Enviar
        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada exitosamente: {response}")
        
        return {
            'success': True,
            'message_id': response
        }
        
    except messaging.UnregisteredError:
        logger.warning(f"⚠️ Token no registrado o expirado: {token[:20]}...")
        return {
            'success': False,
            'error': 'Token no válido o expirado'
        }
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def enviar_notificacion_multiple(tokens, titulo, mensaje, data=None):
    """
    Envía notificación a múltiples dispositivos
    
    Args:
        tokens: Lista de FCM tokens
        titulo: Título de la notificación
        mensaje: Cuerpo de la notificación
        data: Datos adicionales (dict)
    
    Returns:
        dict: Resultado del envío
    """
    try:
        inicializar_firebase()
        
        logger.info(f"📤 Enviando notificación a {len(tokens)} dispositivos")
        
        # Construir mensaje
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data=data or {},
            tokens=tokens,
        )
        
        # Enviar
        response = messaging.send_multicast(message)
        
        logger.info(f"✅ {response.success_count} notificaciones enviadas")
        if response.failure_count > 0:
            logger.warning(f"⚠️ {response.failure_count} notificaciones fallaron")
        
        return {
            'success': True,
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificaciones: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def enviar_notificacion_por_tema(tema, titulo, mensaje, data=None):
    """
    Envía notificación a todos los dispositivos suscritos a un tema
    
    Args:
        tema: Nombre del tema (ej: 'ofertas', 'nuevos_productos')
        titulo: Título de la notificación
        mensaje: Cuerpo de la notificación
        data: Datos adicionales (dict)
    
    Returns:
        dict: Resultado del envío
    """
    try:
        inicializar_firebase()
        
        logger.info(f"📤 Enviando notificación al tema: {tema}")
        
        # Construir mensaje
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data=data or {},
            topic=tema,
        )
        
        # Enviar
        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada al tema '{tema}': {response}")
        
        return {
            'success': True,
            'message_id': response
        }
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación al tema: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def suscribir_a_tema(tokens, tema):
    """
    Suscribe dispositivos a un tema
    
    Args:
        tokens: Lista de FCM tokens o un solo token (str)
        tema: Nombre del tema
    
    Returns:
        dict: Resultado de la suscripción
    """
    try:
        inicializar_firebase()
        
        if isinstance(tokens, str):
            tokens = [tokens]
        
        logger.info(f"📝 Suscribiendo {len(tokens)} dispositivos al tema '{tema}'")
        
        response = messaging.subscribe_to_topic(tokens, tema)
        logger.info(f"✅ {response.success_count} dispositivos suscritos al tema '{tema}'")
        
        return {
            'success': True,
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }
        
    except Exception as e:
        logger.error(f"❌ Error al suscribir a tema: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
