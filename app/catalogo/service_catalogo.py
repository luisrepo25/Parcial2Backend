from django.db.models import Q, Count
from products.models import Producto, Categoria, Marca
from datetime import datetime, timedelta


def serializar_producto_simple(producto):
    """Serializa un producto con información básica"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': float(producto.precio),
        'stock': producto.stock,
        'imagen_url': producto.imagen_url,
        'categoria': {
            'id': producto.categoria.id,
            'nombre': producto.categoria.nombre
        } if producto.categoria else None,
        'marca': {
            'id': producto.marca.id,
            'nombre': producto.marca.nombre
        } if producto.marca else None,
    }


def serializar_producto_completo(producto):
    """Serializa un producto con toda la información"""
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio': float(producto.precio),
        'stock': producto.stock,
        'imagen_url': producto.imagen_url,
        'created_at': producto.created_at.isoformat() if producto.created_at else None,
        'updated_at': producto.updated_at.isoformat() if producto.updated_at else None,
        'categoria': {
            'id': producto.categoria.id,
            'nombre': producto.categoria.nombre,
            'descripcion': producto.categoria.descripcion
        } if producto.categoria else None,
        'marca': {
            'id': producto.marca.id,
            'nombre': producto.marca.nombre
        } if producto.marca else None,
        'garantia': {
            'id': producto.garantia.id,
            'cobertura': producto.garantia.cobertura,
            'marca': {
                'id': producto.garantia.Marca.id,
                'nombre': producto.garantia.Marca.nombre
            }
        } if producto.garantia else None,
    }


# ============= PRODUCTOS =============

def get_todos_productos():
    """Obtiene todos los productos"""
    return Producto.objects.select_related('categoria', 'marca', 'garantia').all()


def get_producto_by_id(producto_id):
    """Obtiene un producto por su ID"""
    return Producto.objects.select_related('categoria', 'marca', 'garantia').get(id=producto_id)


def buscar_productos(query, categoria_id=None, marca_id=None, min_precio=None, max_precio=None):
    """
    Busca productos por nombre o descripción con filtros opcionales
    """
    productos = Producto.objects.select_related('categoria', 'marca', 'garantia')
    
    # Búsqueda por texto
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    
    # Filtro por categoría
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    # Filtro por marca
    if marca_id:
        productos = productos.filter(marca_id=marca_id)
    
    # Filtro por precio mínimo
    if min_precio is not None:
        productos = productos.filter(precio__gte=min_precio)
    
    # Filtro por precio máximo
    if max_precio is not None:
        productos = productos.filter(precio__lte=max_precio)
    
    return productos


def get_productos_destacados(limit=12):
    """Obtiene productos destacados (los más recientes por defecto)"""
    return Producto.objects.select_related('categoria', 'marca', 'garantia').order_by('-created_at')[:limit]


def get_productos_nuevos(dias=30, limit=12):
    """Obtiene productos agregados en los últimos N días"""
    fecha_limite = datetime.now() - timedelta(days=dias)
    return Producto.objects.filter(
        created_at__gte=fecha_limite
    ).select_related('categoria', 'marca', 'garantia').order_by('-created_at')[:limit]


def get_productos_mas_vendidos(limit=10):
    """
    Obtiene productos más vendidos
    TODO: Implementar cuando se integre con el módulo de ventas
    Por ahora retorna productos aleatorios
    """
    return Producto.objects.select_related('categoria', 'marca', 'garantia').order_by('?')[:limit]


# ============= CATEGORÍAS =============

def get_todas_categorias():
    """Obtiene todas las categorías con cantidad de productos"""
    return Categoria.objects.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')


def get_categoria_by_id(categoria_id):
    """Obtiene una categoría por su ID"""
    return Categoria.objects.annotate(
        total_productos=Count('productos')
    ).get(id=categoria_id)


def get_productos_por_categoria(categoria_id):
    """Obtiene productos de una categoría específica"""
    return Producto.objects.filter(
        categoria_id=categoria_id
    ).select_related('categoria', 'marca', 'garantia')


# ============= MARCAS =============

def get_todas_marcas():
    """Obtiene todas las marcas con cantidad de productos"""
    return Marca.objects.annotate(
        total_productos=Count('productos')
    ).order_by('nombre')


def get_marca_by_id(marca_id):
    """Obtiene una marca por su ID"""
    return Marca.objects.annotate(
        total_productos=Count('productos')
    ).get(id=marca_id)


def get_productos_por_marca(marca_id):
    """Obtiene productos de una marca específica"""
    return Producto.objects.filter(
        marca_id=marca_id
    ).select_related('categoria', 'marca', 'garantia')
