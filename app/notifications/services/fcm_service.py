import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
from users.models import Usuario
from notifications.models import Notificacion, Noti_Usuario

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
                # Buscar archivo de credenciales en múltiples ubicaciones
                possible_paths = [
                    # Ruta en Render (Secret Files)
                    '/etc/secrets/firebase-credentials.json',
                    # Ruta local (desarrollo)
                    os.path.join(settings.BASE_DIR, os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')),
                    # Ruta alternativa
                    os.path.join(settings.BASE_DIR, 'firebase-credentials.json'),
                ]
                
                cred_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        cred_path = path
                        logger.info(f"📁 Archivo de credenciales encontrado en: {path}")
                        break
                
                if not cred_path:
                    logger.error(f"❌ Archivo de credenciales no encontrado en ninguna ubicación:")
                    for path in possible_paths:
                        logger.error(f"   - {path}")
                    raise FileNotFoundError(
                        f"Firebase credentials not found. Tried: {', '.join(possible_paths)}"
                    )
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                _firebase_initialized = True
                logger.info("✅ Firebase Admin SDK inicializado correctamente")
            except Exception as e:
                logger.error(f"❌ Error al inicializar Firebase: {str(e)}")
                raise


def enviar_notificacion_fcm(idUsuario, titulo, mensaje, data=None):
    """
    Envía una notificación push a un dispositivo específico y la guarda en BD
    
    Args:
        idUsuario: ID del usuario destinatario
        titulo: Título de la notificación
        mensaje: Cuerpo de la notificación
        data: Datos adicionales (dict)
    
    Returns:
        dict: Resultado del envío
    """
    try:
        # Obtener el usuario
        usuario = Usuario.objects.get(id=idUsuario)
        token = usuario.fcm_token
        
        if not token:
            logger.warning(f"⚠️ Usuario {idUsuario} no tiene token FCM")
            return {
                'success': False,
                'error': 'Usuario no tiene token FCM registrado'
            }
        
        # 1. Guardar notificación en BD
        notificacion = Notificacion.objects.create(
            titulo=titulo,
            mensaje=mensaje
        )
        
        # 2. Crear relación Noti_Usuario
        noti_usuario = Noti_Usuario.objects.create(
            notificacion=notificacion,
            usuario=usuario,
            leida=False
        )
        
        logger.info(f"💾 Notificación #{notificacion.id} guardada para usuario {usuario.correo}")
        
        # 3. Enviar notificación push
        inicializar_firebase()
        
        logger.info(f"📤 Enviando notificación a token: {token[:20]}...")
        
        # Construir mensaje
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data={
                **(data or {}),
                'notificacion_id': str(notificacion.id),  # ID para poder marcar como leída
            },
            token=token,
        )
        
        # Enviar
        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada exitosamente: {response}")
        
        return {
            'success': True,
            'message_id': response,
            'notificacion_id': notificacion.id
        }
        
    except Usuario.DoesNotExist:
        logger.error(f"❌ Usuario {idUsuario} no encontrado")
        return {
            'success': False,
            'error': 'Usuario no encontrado'
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


def enviar_notificacion_multiple(usuarios_ids, titulo, mensaje, data=None):
    """
    Envía notificación a múltiples usuarios y guarda en BD
    
    Args:
        usuarios_ids: Lista de IDs de usuarios
            ejemplo: [1, 2, 3, ...]
        titulo: Título de la notificación
        mensaje: Cuerpo de la notificación
        data: Datos adicionales (dict)
    
    Returns:
        dict: Resultado del envío
    """
    try:
        # 1. Guardar notificación en BD
        notificacion = Notificacion.objects.create(
            titulo=titulo,
            mensaje=mensaje
        )
        
        logger.info(f"💾 Notificación #{notificacion.id} creada para {len(usuarios_ids)} usuarios")
        
        # 2. Obtener usuarios con tokens
        usuarios = Usuario.objects.filter(
            id__in=usuarios_ids,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        
        if not usuarios.exists():
            logger.warning("⚠️ Ningún usuario tiene token FCM registrado")
            return {
                'success': False,
                'error': 'Ningún usuario tiene notificaciones habilitadas'
            }
        
        # 3. Crear relaciones Noti_Usuario para todos
        noti_usuarios = []
        tokens = []
        for usuario in usuarios:
            noti_usuarios.append(
                Noti_Usuario(
                    notificacion=notificacion,
                    usuario=usuario,
                    leida=False
                )
            )
            tokens.append(usuario.fcm_token)
        
        Noti_Usuario.objects.bulk_create(noti_usuarios)
        logger.info(f"💾 {len(noti_usuarios)} relaciones Noti_Usuario creadas")
        
        # 4. Enviar notificaciones push
        inicializar_firebase()
        
        logger.info(f"📤 Enviando notificación a {len(tokens)} dispositivos")
        
        # Construir mensaje
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje,
            ),
            data={
                **(data or {}),
                'notificacion_id': str(notificacion.id),
            },
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
            'failure_count': response.failure_count,
            'notificacion_id': notificacion.id
        }
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificaciones: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    
def leer_notificacion(idUsuario, idNotificacion):
    """
    Marca una notificación como leída para un usuario específico
    
    Args:
        idUsuario: ID del usuario
        idNotificacion: ID de la notificación
    
    Returns:
        dict: Resultado de la operación
    """
    try:
        # Buscar la relación Noti_Usuario
        noti_usuario = Noti_Usuario.objects.get(
            notificacion_id=idNotificacion,
            usuario_id=idUsuario
        )
        
        # Marcar como leída
        noti_usuario.leida = True
        noti_usuario.save()
        
        logger.info(f"✅ Notificación {idNotificacion} marcada como leída para el usuario {idUsuario}")
        
        return {
            'success': True,
            'message': f'Notificación {idNotificacion} marcada como leída.'
        }
        
    except Noti_Usuario.DoesNotExist:
        logger.error(f"❌ Notificación {idNotificacion} no encontrada para el usuario {idUsuario}")
        return {
            'success': False,
            'error': 'Notificación no encontrada para este usuario'
        }
    except Exception as e:
        logger.error(f"❌ Error al marcar notificación como leída: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def obtener_notificaciones_usuario(idUsuario, solo_no_leidas=False):
    """
    Obtiene todas las notificaciones de un usuario
    
    Args:
        idUsuario: ID del usuario
        solo_no_leidas: Si True, solo retorna notificaciones no leídas
    
    Returns:
        dict: Lista de notificaciones
    """
    try:
        query = Noti_Usuario.objects.filter(usuario_id=idUsuario).select_related('notificacion')
        
        if solo_no_leidas:
            query = query.filter(leida=False)
        
        notificaciones = []
        for noti_usuario in query:
            notificaciones.append({
                'id': noti_usuario.notificacion.id,
                'titulo': noti_usuario.notificacion.titulo,
                'mensaje': noti_usuario.notificacion.mensaje,
                'leida': noti_usuario.leida,
                'created_at': noti_usuario.created_at.isoformat(),
            })
        
        logger.info(f"📋 {len(notificaciones)} notificaciones obtenidas para usuario {idUsuario}")
        
        return {
            'success': True,
            'notificaciones': notificaciones,
            'total': len(notificaciones)
        }
        
    except Exception as e:
        logger.error(f"❌ Error al obtener notificaciones: {str(e)}")
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


def listar_todas_notificaciones(page=1, page_size=10, leida=None):
    """
    Lista todas las notificaciones del sistema con paginación
    
    Args:
        page: Número de página (default: 1)
        page_size: Tamaño de página (default: 10, max: 100)
        leida: Filtrar por estado leído (opcional: True/False)
    
    Returns:
        dict: Notificaciones paginadas y metadata
    """
    from django.core.paginator import Paginator, EmptyPage
    from notifications.models import Notificacion, Noti_Usuario
    from django.db.models import Count, Q
    
    try:
        # Limitar page_size a máximo 100
        page_size = min(page_size, 100)
        
        # Construir query con anotaciones
        query = Notificacion.objects.annotate(
            total_enviados=Count('notificaciones_usuario'),
            total_leidos=Count('notificaciones_usuario', filter=Q(notificaciones_usuario__leida=True))
        ).order_by('-created_at')
        
        # Aplicar paginación
        paginator = Paginator(query, page_size)
        
        try:
            notificaciones_page = paginator.page(page)
        except EmptyPage:
            notificaciones_page = paginator.page(paginator.num_pages)
        
        # Serializar notificaciones
        notificaciones_data = []
        for notif in notificaciones_page:
            notificaciones_data.append({
                'id': notif.id,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'created_at': notif.created_at.isoformat(),
                'updated_at': notif.updated_at.isoformat(),
                'total_enviados': notif.total_enviados,
                'total_leidos': notif.total_leidos,
                'total_no_leidos': notif.total_enviados - notif.total_leidos
            })
        
        logger.info(f"📋 Listando notificaciones - Página {notificaciones_page.number}/{paginator.num_pages}")
        
        return {
            'notificaciones': notificaciones_data,
            'pagination': {
                'page': notificaciones_page.number,
                'page_size': page_size,
                'total_items': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': notificaciones_page.has_next(),
                'has_previous': notificaciones_page.has_previous()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error al listar notificaciones: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def obtener_destinatarios_notificacion(notificacion_id):
    """
    Obtiene todos los usuarios que recibieron una notificación específica
    con su estado de lectura
    
    Args:
        notificacion_id: ID de la notificación
    
    Returns:
        dict: Información de la notificación y sus destinatarios
    
    Raises:
        Notificacion.DoesNotExist: Si la notificación no existe
    """
    from notifications.models import Notificacion, Noti_Usuario
    
    try:
        # Obtener la notificación
        notificacion = Notificacion.objects.get(id=notificacion_id)
        
        # Obtener todos los destinatarios
        destinatarios = Noti_Usuario.objects.filter(
            notificacion_id=notificacion_id
        ).select_related('usuario')
        
        # Serializar destinatarios
        usuarios_data = []
        for noti_usuario in destinatarios:
            try:
                cliente = noti_usuario.usuario.cliente
                nombre_completo = f"{cliente.nombres} {cliente.apellidoPaterno}"
            except:
                nombre_completo = "Usuario sin nombre"
            
            usuarios_data.append({
                'id': noti_usuario.id,
                'usuario': {
                    'id': noti_usuario.usuario.id,
                    'nombre': nombre_completo,
                    'correo': noti_usuario.usuario.correo
                },
                'leida': noti_usuario.leida,
                'fecha_envio': noti_usuario.created_at.isoformat(),
                'fecha_lectura': noti_usuario.updated_at.isoformat() if noti_usuario.leida else None
            })
        
        # Calcular estadísticas
        total_enviados = destinatarios.count()
        total_leidos = destinatarios.filter(leida=True).count()
        
        logger.info(f"🔍 Destinatarios de notificación #{notificacion_id}: {total_enviados} usuarios")
        
        return {
            'notificacion': {
                'id': notificacion.id,
                'titulo': notificacion.titulo,
                'mensaje': notificacion.mensaje,
                'created_at': notificacion.created_at.isoformat()
            },
            'estadisticas': {
                'total_enviados': total_enviados,
                'total_leidos': total_leidos,
                'total_no_leidos': total_enviados - total_leidos,
                'porcentaje_leidos': round((total_leidos / total_enviados * 100), 2) if total_enviados > 0 else 0
            },
            'destinatarios': usuarios_data
        }
        
    except Notificacion.DoesNotExist:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener destinatarios: {str(e)}")
        raise
