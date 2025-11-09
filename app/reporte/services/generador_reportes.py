"""
Servicio para generar reportes basados en la estructura interpretada por OpenAI
"""
import logging
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone

from sales.models import NotaVenta, Detalle_Venta
from products.models import Producto, Categoria, Marca
from users.models import Usuario, Cliente
from bitacora.models import Bitacora

logger = logging.getLogger(__name__)


def generar_reporte(estructura):
    """
    Genera un reporte basado en la estructura interpretada
    
    Args:
        estructura (dict): Estructura del reporte generada por OpenAI
        
    Returns:
        dict: Datos del reporte generado
    """
    tipo_reporte = estructura.get('tipo_reporte')
    filtros = estructura.get('filtros', {})
    campos = estructura.get('campos', [])
    agrupacion = estructura.get('agrupacion')
    orden = estructura.get('orden', 'desc')
    limite = estructura.get('limite', 100)
    
    logger.info(f"📊 Generando reporte tipo: {tipo_reporte}")
    
    # Delegar al generador específico según el tipo
    if tipo_reporte == 'ventas':
        return generar_reporte_ventas(filtros, campos, agrupacion, orden, limite)
    elif tipo_reporte == 'productos':
        return generar_reporte_productos(filtros, campos, agrupacion, orden, limite)
    elif tipo_reporte == 'usuarios' or tipo_reporte == 'clientes':
        return generar_reporte_usuarios(filtros, campos, agrupacion, orden, limite)
    elif tipo_reporte == 'bitacora':
        return generar_reporte_bitacora(filtros, campos, agrupacion, orden, limite)
    else:
        raise ValueError(f"Tipo de reporte no soportado: {tipo_reporte}")


def aplicar_filtros_fecha(queryset, filtros, campo_fecha='created_at'):
    """
    Aplica filtros de fecha al queryset
    """
    fecha_desde = filtros.get('fecha_desde')
    fecha_hasta = filtros.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.fromisoformat(fecha_desde)
            queryset = queryset.filter(**{f'{campo_fecha}__gte': fecha_desde_dt})
        except ValueError:
            logger.warning(f"Fecha desde inválida: {fecha_desde}")
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.fromisoformat(fecha_hasta)
            # Agregar 1 día para incluir todo el día final
            fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
            queryset = queryset.filter(**{f'{campo_fecha}__lt': fecha_hasta_dt})
        except ValueError:
            logger.warning(f"Fecha hasta inválida: {fecha_hasta}")
    
    return queryset


def generar_reporte_ventas(filtros, campos, agrupacion, orden, limite):
    """Genera reporte de ventas"""
    queryset = NotaVenta.objects.select_related('usuario', 'metodo_pago')
    
    # Aplicar filtros de fecha
    queryset = aplicar_filtros_fecha(queryset, filtros)
    
    # Aplicar otros filtros
    if 'estado' in filtros:
        queryset = queryset.filter(estado=filtros['estado'])
    
    if 'usuario_id' in filtros:
        queryset = queryset.filter(usuario_id=filtros['usuario_id'])
    
    # Ordenar
    orden_campo = '-created_at' if orden == 'desc' else 'created_at'
    queryset = queryset.order_by(orden_campo)[:limite]
    
    # Serializar resultados
    datos = []
    for venta in queryset:
        dato = {
            'id': venta.id,
            'total': float(venta.total),
            'estado': venta.estado,
            'created_at': venta.created_at.isoformat(),
            'usuario_correo': venta.usuario.correo,
            'metodo_pago': venta.metodo_pago.nombre if venta.metodo_pago else None
        }
        datos.append(dato)
    
    # Calcular estadísticas
    estadisticas = queryset.aggregate(
        total_ventas=Count('id'),
        monto_total=Sum('total'),
        monto_promedio=Avg('total')
    )
    
    return {
        'tipo': 'ventas',
        'total_registros': len(datos),
        'datos': datos,
        'estadisticas': {
            'total_ventas': estadisticas['total_ventas'] or 0,
            'monto_total': float(estadisticas['monto_total'] or 0),
            'monto_promedio': float(estadisticas['monto_promedio'] or 0)
        }
    }


def generar_reporte_productos(filtros, campos, agrupacion, orden, limite):
    """Genera reporte de productos"""
    queryset = Producto.objects.select_related('categoria', 'marca', 'garantia')
    
    # Aplicar filtros
    if 'categoria_id' in filtros:
        queryset = queryset.filter(categoria_id=filtros['categoria_id'])
    
    if 'marca_id' in filtros:
        queryset = queryset.filter(marca_id=filtros['marca_id'])
    
    if 'stock_minimo' in filtros:
        queryset = queryset.filter(stock__lte=filtros['stock_minimo'])
    
    # Ordenar
    orden_campo = '-created_at' if orden == 'desc' else 'created_at'
    queryset = queryset.order_by(orden_campo)[:limite]
    
    # Serializar resultados
    datos = []
    for producto in queryset:
        dato = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'categoria': producto.categoria.nombre if producto.categoria else None,
            'marca': producto.marca.nombre if producto.marca else None,
            'created_at': producto.created_at.isoformat()
        }
        datos.append(dato)
    
    # Estadísticas
    estadisticas = queryset.aggregate(
        total_productos=Count('id'),
        stock_total=Sum('stock'),
        precio_promedio=Avg('precio')
    )
    
    return {
        'tipo': 'productos',
        'total_registros': len(datos),
        'datos': datos,
        'estadisticas': {
            'total_productos': estadisticas['total_productos'] or 0,
            'stock_total': estadisticas['stock_total'] or 0,
            'precio_promedio': float(estadisticas['precio_promedio'] or 0)
        }
    }


def generar_reporte_usuarios(filtros, campos, agrupacion, orden, limite):
    """Genera reporte de usuarios/clientes"""
    queryset = Cliente.objects.select_related('usuario')
    
    # Aplicar filtros de fecha
    queryset = aplicar_filtros_fecha(queryset, filtros)
    
    # Ordenar
    orden_campo = '-usuario__created_at' if orden == 'desc' else 'usuario__created_at'
    queryset = queryset.order_by(orden_campo)[:limite]
    
    # Serializar resultados
    datos = []
    for cliente in queryset:
        dato = {
            'id': cliente.id,
            'nombres': cliente.nombres,
            'apellidos': f"{cliente.apellidoPaterno} {cliente.apellidoMaterno}",
            'correo': cliente.usuario.correo,
            'ci': cliente.ci,
            'telefono': cliente.telefono,
            'created_at': cliente.usuario.created_at.isoformat() if cliente.usuario.created_at else None
        }
        datos.append(dato)
    
    return {
        'tipo': 'clientes',
        'total_registros': len(datos),
        'datos': datos,
        'estadisticas': {
            'total_clientes': len(datos)
        }
    }


def generar_reporte_bitacora(filtros, campos, agrupacion, orden, limite):
    """Genera reporte de bitácora"""
    queryset = Bitacora.objects.all()
    
    # Aplicar filtros de fecha
    queryset = aplicar_filtros_fecha(queryset, filtros, campo_fecha='fecha_hora')
    
    # Aplicar otros filtros
    if 'accion' in filtros:
        queryset = queryset.filter(accion=filtros['accion'])
    
    if 'resultado' in filtros:
        queryset = queryset.filter(resultado=filtros['resultado'])
    
    if 'usuario' in filtros:
        queryset = queryset.filter(usuario__icontains=filtros['usuario'])
    
    # Ordenar
    orden_campo = '-fecha_hora' if orden == 'desc' else 'fecha_hora'
    queryset = queryset.order_by(orden_campo)[:limite]
    
    # Serializar resultados
    datos = []
    for registro in queryset:
        dato = {
            'id': registro.id,
            'accion': registro.accion,
            'usuario': registro.usuario,
            'fecha_hora': registro.fecha_hora.isoformat(),
            'detalles': registro.detalles,
            'resultado': registro.resultado
        }
        datos.append(dato)
    
    # Estadísticas
    estadisticas = queryset.aggregate(
        total_acciones=Count('id'),
        exitosas=Count('id', filter=Q(resultado='EXITOSO')),
        fallidas=Count('id', filter=Q(resultado='FALLIDO'))
    )
    
    return {
        'tipo': 'bitacora',
        'total_registros': len(datos),
        'datos': datos,
        'estadisticas': {
            'total_acciones': estadisticas['total_acciones'] or 0,
            'exitosas': estadisticas['exitosas'] or 0,
            'fallidas': estadisticas['fallidas'] or 0
        }
    }
