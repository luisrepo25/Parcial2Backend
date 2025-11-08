"""
Servicio de lógica de negocio para ventas
Maneja la creación de ventas, confirmación de pagos y gestión de stock
"""
from django.db import transaction
from django.db.models import F
from sales.models import NotaVenta, Detalle_Venta, MetodoPago
from products.models import Producto
from users.models import Usuario


@transaction.atomic
def crear_nota_venta(usuario_id, items, metodo_pago_nombre='Tarjeta'):
    """
    Crea una nota de venta con sus detalles
    
    Args:
        usuario_id: ID del usuario que realiza la compra
        items: Lista de items [{'producto_id': int, 'cantidad': int}]
        metodo_pago_nombre: Nombre del método de pago (default: 'Tarjeta')
    
    Returns:
        NotaVenta instance creada
    
    Raises:
        ValueError: Si hay problemas con stock o datos inválidos
        Usuario.DoesNotExist: Si el usuario no existe
        Producto.DoesNotExist: Si algún producto no existe
    """
    # Verificar que el usuario existe
    usuario = Usuario.objects.get(id=usuario_id)
    
    # Obtener o crear el método de pago
    metodo_pago, _ = MetodoPago.objects.get_or_create(
        nombre=metodo_pago_nombre,
        defaults={'descripcion': f'Pago con {metodo_pago_nombre}', 'estado': True}
    )
    
    # Crear nota de venta
    nota_venta = NotaVenta.objects.create(
        usuario=usuario,
        metodo_pago=metodo_pago,
        estado='pendiente',
        total=0
    )
    
    total = 0
    detalles = []
    
    # Crear detalles y validar stock
    for item in items:
        producto = Producto.objects.select_for_update().get(id=item['producto_id'])
        cantidad = item['cantidad']
        
        # Verificar stock suficiente
        if producto.stock < cantidad:
            raise ValueError(
                f"Stock insuficiente para '{producto.nombre}'. "
                f"Disponible: {producto.stock}, Solicitado: {cantidad}"
            )
        
        # Calcular subtotal
        precio_unitario = producto.precio
        subtotal = cantidad * precio_unitario
        
        # Crear detalle con subtotal calculado
        detalle = Detalle_Venta(
            nota_venta=nota_venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal  # ← Calculado manualmente para bulk_create
        )
        detalles.append(detalle)
        total += subtotal
    
    # Guardar todos los detalles
    Detalle_Venta.objects.bulk_create(detalles)
    
    # Actualizar el total de la nota de venta
    nota_venta.total = total
    nota_venta.save()
    
    return nota_venta


@transaction.atomic
def confirmar_pago(nota_venta_id, stripe_session_id, stripe_payment_intent):
    """
    Confirma el pago exitoso y actualiza el stock de productos
    
    Args:
        nota_venta_id: ID de la nota de venta
        stripe_session_id: ID de la sesión de Stripe
        stripe_payment_intent: ID del payment intent de Stripe
    
    Returns:
        NotaVenta instance actualizada
    
    Raises:
        ValueError: Si la venta ya fue confirmada o no se puede procesar
        NotaVenta.DoesNotExist: Si la nota de venta no existe
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔄 [confirmar_pago] Iniciando para NotaVenta #{nota_venta_id}")
    logger.info(f"   - Session ID: {stripe_session_id}")
    logger.info(f"   - Payment Intent: {stripe_payment_intent}")
    
    try:
        nota_venta = NotaVenta.objects.select_for_update().get(id=nota_venta_id)
        logger.info(f"✅ NotaVenta encontrada - Estado actual: {nota_venta.estado}")
        logger.info(f"   - Total: ${nota_venta.total}")
        logger.info(f"   - Usuario ID: {nota_venta.usuario_id}")
    except NotaVenta.DoesNotExist:
        logger.error(f"❌ NotaVenta #{nota_venta_id} NO EXISTE en la base de datos")
        raise
    
    # Verificar que la venta está pendiente
    if nota_venta.estado != 'pendiente':
        logger.warning(f"⚠️ La venta ya fue procesada con estado: {nota_venta.estado}")
        raise ValueError(
            f"La venta ya fue procesada con estado: {nota_venta.estado}"
        )
    
    # Actualizar información de Stripe
    logger.info("💾 Actualizando información de Stripe y estado...")
    nota_venta.stripe_session_id = stripe_session_id
    nota_venta.stripe_payment_intent = stripe_payment_intent
    nota_venta.estado = 'pagada'
    nota_venta.save()
    logger.info(f"✅ Estado actualizado a: {nota_venta.estado}")
    
    # Reducir stock de productos
    logger.info("📦 Actualizando stock de productos...")
    for detalle in nota_venta.detalles.select_related('producto'):
        logger.info(f"   - Producto: {detalle.producto.nombre} | Cantidad: {detalle.cantidad}")
        # Usar F() para evitar race conditions
        Producto.objects.filter(id=detalle.producto.id).update(
            stock=F('stock') - detalle.cantidad
        )
    
    logger.info(f"✅ [confirmar_pago] Completado exitosamente para NotaVenta #{nota_venta_id}")
    
    return nota_venta


@transaction.atomic
def marcar_pago_fallido(nota_venta_id, motivo=None):
    """
    Marca una venta como fallida
    
    Args:
        nota_venta_id: ID de la nota de venta
        motivo: Razón del fallo (opcional)
    
    Returns:
        NotaVenta instance actualizada
    """
    nota_venta = NotaVenta.objects.get(id=nota_venta_id)
    nota_venta.estado = 'fallida'
    nota_venta.save()
    
    return nota_venta


@transaction.atomic
def cancelar_venta(nota_venta_id):
    """
    Cancela una venta pendiente
    
    Args:
        nota_venta_id: ID de la nota de venta
    
    Returns:
        NotaVenta instance actualizada
    
    Raises:
        ValueError: Si la venta no puede ser cancelada
    """
    nota_venta = NotaVenta.objects.get(id=nota_venta_id)
    
    if nota_venta.estado not in ['pendiente', 'fallida']:
        raise ValueError(
            f"No se puede cancelar una venta con estado: {nota_venta.estado}"
        )
    
    nota_venta.estado = 'cancelada'
    nota_venta.save()
    
    return nota_venta


@transaction.atomic
def procesar_reembolso(nota_venta_id):
    """
    Procesa un reembolso y restaura el stock de productos
    
    Args:
        nota_venta_id: ID de la nota de venta a reembolsar
    
    Returns:
        NotaVenta instance actualizada
    
    Raises:
        ValueError: Si la venta no puede ser reembolsada
    """
    nota_venta = NotaVenta.objects.select_for_update().get(id=nota_venta_id)
    
    # Verificar que la venta está pagada
    if nota_venta.estado != 'pagada':
        raise ValueError(
            "Solo se pueden reembolsar ventas pagadas. "
            f"Estado actual: {nota_venta.estado}"
        )
    
    # Actualizar estado
    nota_venta.estado = 'reembolsada'
    nota_venta.save()
    
    # Restaurar stock de productos
    for detalle in nota_venta.detalles.select_related('producto'):
        Producto.objects.filter(id=detalle.producto.id).update(
            stock=F('stock') + detalle.cantidad
        )
    
    return nota_venta


def obtener_ventas_usuario(usuario_id, estado=None):
    """
    Obtiene todas las ventas de un usuario
    
    Args:
        usuario_id: ID del usuario
        estado: Filtrar por estado específico (opcional)
    
    Returns:
        QuerySet de NotaVenta con detalles cargados
    """
    query = NotaVenta.objects.filter(usuario_id=usuario_id)
    
    if estado:
        query = query.filter(estado=estado)
    
    return query.select_related('metodo_pago', 'usuario').prefetch_related(
        'detalles__producto__categoria',
        'detalles__producto__marca'
    ).order_by('-created_at')


def obtener_detalle_venta(nota_venta_id):
    """
    Obtiene el detalle completo de una venta específica
    
    Args:
        nota_venta_id: ID de la nota de venta
    
    Returns:
        NotaVenta instance con toda la información relacionada
    
    Raises:
        NotaVenta.DoesNotExist: Si la venta no existe
    """
    return NotaVenta.objects.select_related(
        'usuario',
        'metodo_pago'
    ).prefetch_related(
        'detalles__producto__categoria',
        'detalles__producto__marca',
        'detalles__producto__garantia'
    ).get(id=nota_venta_id)


def validar_items_disponibles(items):
    """
    Valida que todos los productos existan y tengan stock suficiente
    
    Args:
        items: Lista de items [{'producto_id': int, 'cantidad': int}]
    
    Returns:
        List de productos con información de disponibilidad
    
    Raises:
        ValueError: Si algún producto no existe o no tiene stock
    """
    productos_validados = []
    
    for item in items:
        try:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = item['cantidad']
            
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para '{producto.nombre}'")
            
            if producto.stock < cantidad:
                raise ValueError(
                    f"Stock insuficiente para '{producto.nombre}'. "
                    f"Disponible: {producto.stock}, Solicitado: {cantidad}"
                )
            
            productos_validados.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': producto.precio * cantidad
            })
            
        except Producto.DoesNotExist:
            raise ValueError(f"Producto con ID {item['producto_id']} no existe")
    
    return productos_validados


def calcular_total_items(items):
    """
    Calcula el total de una lista de items
    
    Args:
        items: Lista de items validados con 'subtotal'
    
    Returns:
        Decimal con el total
    """
    return sum(item['subtotal'] for item in items)


def obtener_estadisticas_ventas_usuario(usuario_id):
    """
    Obtiene estadísticas de ventas de un usuario
    
    Args:
        usuario_id: ID del usuario
    
    Returns:
        Dict con estadísticas
    """
    from django.db.models import Count, Sum
    
    ventas = NotaVenta.objects.filter(usuario_id=usuario_id)
    
    return {
        'total_compras': ventas.count(),
        'compras_pagadas': ventas.filter(estado='pagada').count(),
        'compras_pendientes': ventas.filter(estado='pendiente').count(),
        'total_gastado': ventas.filter(estado='pagada').aggregate(
            total=Sum('total')
        )['total'] or 0,
    }
