"""
Servicio de lógica de negocio para la bitácora
Maneja el registro y consulta de acciones del sistema
"""
import logging
from django.core.paginator import Paginator, EmptyPage
from bitacora.models import Bitacora

logger = logging.getLogger(__name__)


def registrar_accion(accion, usuario, detalles=None, resultado='exitoso'):
    """
    Registra una acción en la bitácora del sistema
    
    Args:
        accion: Descripción de la acción realizada (ej: "Login", "Crear Producto", "Actualizar Usuario")
        usuario: Identificador del usuario (email, nombre o ID)
        detalles: Información adicional sobre la acción (opcional)
        resultado: Resultado de la acción (default: 'exitoso', otras: 'fallido', 'error')
    
    Returns:
        Bitacora: Instancia del registro creado
    
    Example:
        registrar_accion(
            accion="Crear Producto",
            usuario="admin@example.com",
            detalles="Producto: Laptop Dell XPS 15, ID: 123",
            resultado="exitoso"
        )
    """
    try:
        # Convertir usuario a string si es un objeto
        usuario_str = str(usuario)
        
        # Crear registro en la bitácora
        registro = Bitacora.objects.create(
            accion=accion,
            usuario=usuario_str,
            detalles=detalles,
            resultado=resultado
        )
        
        logger.info(f"📝 Bitácora: {accion} - Usuario: {usuario_str} - Resultado: {resultado}")
        
        return registro
        
    except Exception as e:
        logger.error(f"❌ Error al registrar en bitácora: {str(e)}")
        # No lanzar excepción para no interrumpir el flujo principal
        return None


def obtener_ultimas_acciones(page=1, page_size=50, accion=None, usuario=None, resultado=None):
    """
    Obtiene las últimas acciones registradas en la bitácora con paginación
    
    Args:
        page: Número de página (default: 1)
        page_size: Tamaño de página (default: 50, max: 200)
        accion: Filtrar por tipo de acción (opcional)
        usuario: Filtrar por usuario (opcional)
        resultado: Filtrar por resultado (opcional)
    
    Returns:
        dict: Acciones paginadas y metadata
    """
    try:
        # Limitar page_size a máximo 200
        page_size = min(page_size, 200)
        
        # Construir query
        query = Bitacora.objects.all()
        
        # Aplicar filtros
        if accion:
            query = query.filter(accion__icontains=accion)
        
        if usuario:
            query = query.filter(usuario__icontains=usuario)
        
        if resultado:
            query = query.filter(resultado=resultado)
        
        # Aplicar paginación
        paginator = Paginator(query, page_size)
        
        try:
            acciones_page = paginator.page(page)
        except EmptyPage:
            acciones_page = paginator.page(paginator.num_pages)
        
        # Serializar acciones
        acciones_data = []
        for registro in acciones_page:
            acciones_data.append({
                'id': registro.id,
                'accion': registro.accion,
                'usuario': registro.usuario,
                'fecha_hora': registro.fecha_hora.isoformat(),
                'detalles': registro.detalles,
                'resultado': registro.resultado
            })
        
        logger.info(f"📋 Consultando bitácora - Página {acciones_page.number}/{paginator.num_pages}")
        
        return {
            'acciones': acciones_data,
            'pagination': {
                'page': acciones_page.number,
                'page_size': page_size,
                'total_items': paginator.count,
                'total_pages': paginator.num_pages,
                'has_next': acciones_page.has_next(),
                'has_previous': acciones_page.has_previous()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error al obtener acciones de bitácora: {str(e)}")
        raise


def obtener_estadisticas_bitacora():
    """
    Obtiene estadísticas generales de la bitácora
    
    Returns:
        dict: Estadísticas de acciones registradas
    """
    try:
        from django.db.models import Count
        
        total_registros = Bitacora.objects.count()
        
        # Contar por resultado
        por_resultado = Bitacora.objects.values('resultado').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Contar acciones más frecuentes
        acciones_frecuentes = Bitacora.objects.values('accion').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Usuarios más activos
        usuarios_activos = Bitacora.objects.values('usuario').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return {
            'total_registros': total_registros,
            'por_resultado': list(por_resultado),
            'acciones_frecuentes': list(acciones_frecuentes),
            'usuarios_activos': list(usuarios_activos)
        }
        
    except Exception as e:
        logger.error(f"❌ Error al obtener estadísticas: {str(e)}")
        raise


def limpiar_bitacora_antigua(dias=90):
    """
    Elimina registros de bitácora más antiguos que X días
    
    Args:
        dias: Número de días a mantener (default: 90)
    
    Returns:
        int: Número de registros eliminados
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        registros_eliminados = Bitacora.objects.filter(
            fecha_hora__lt=fecha_limite
        ).delete()[0]
        
        logger.info(f"🗑️ Bitácora: {registros_eliminados} registros antiguos eliminados")
        
        return registros_eliminados
        
    except Exception as e:
        logger.error(f"❌ Error al limpiar bitácora: {str(e)}")
        raise
