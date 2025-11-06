from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from products.models import Producto, Categoria, Marca
from . import service_catalogo


# ============= PRODUCTOS =============

@require_http_methods(["GET"])
def get_productos(request):
    """
    GET /catalogo/productos/
    Lista todos los productos con paginación
    Query params: ?page=1&per_page=12
    """
    try:
        productos = service_catalogo.get_todos_productos()
        
        # Paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        
        paginator = Paginator(productos, per_page)
        productos_page = paginator.get_page(page)
        
        return JsonResponse({
            'ok': True,
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos_page],
            'pagination': {
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': productos_page.number,
                'has_next': productos_page.has_next(),
                'has_previous': productos_page.has_previous(),
                'per_page': per_page
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_producto(request, id):
    """
    GET /catalogo/productos/<id>/
    Obtiene el detalle completo de un producto
    """
    try:
        producto = service_catalogo.get_producto_by_id(id)
        return JsonResponse({
            'ok': True,
            'producto': service_catalogo.serializar_producto_completo(producto)
        }, status=200)
    except Producto.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Producto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def buscar_productos(request):
    """
    GET /catalogo/productos/buscar?q=licuadora&categoria=1&marca=2&min_precio=50&max_precio=500
    Busca productos por nombre/descripción con filtros opcionales
    Query params: 
    - q: texto de búsqueda
    - categoria: ID de categoría
    - marca: ID de marca
    - min_precio: precio mínimo
    - max_precio: precio máximo
    - page: página actual
    - per_page: productos por página
    """
    try:
        query = request.GET.get('q', '').strip()
        categoria_id = request.GET.get('categoria')
        marca_id = request.GET.get('marca')
        min_precio = request.GET.get('min_precio')
        max_precio = request.GET.get('max_precio')
        
        # Convertir a tipos apropiados
        if categoria_id:
            categoria_id = int(categoria_id)
        if marca_id:
            marca_id = int(marca_id)
        if min_precio:
            min_precio = float(min_precio)
        if max_precio:
            max_precio = float(max_precio)
        
        productos = service_catalogo.buscar_productos(
            query=query,
            categoria_id=categoria_id,
            marca_id=marca_id,
            min_precio=min_precio,
            max_precio=max_precio
        )
        
        # Paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        
        paginator = Paginator(productos, per_page)
        productos_page = paginator.get_page(page)
        
        return JsonResponse({
            'ok': True,
            'query': query,
            'filtros': {
                'categoria': categoria_id,
                'marca': marca_id,
                'min_precio': min_precio,
                'max_precio': max_precio
            },
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos_page],
            'pagination': {
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': productos_page.number,
                'has_next': productos_page.has_next(),
                'has_previous': productos_page.has_previous(),
            }
        }, status=200)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': f'Error en parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_productos_destacados(request):
    """
    GET /catalogo/productos/destacados/
    Obtiene productos destacados
    Query params: ?limit=12
    """
    try:
        limit = int(request.GET.get('limit', 12))
        productos = service_catalogo.get_productos_destacados(limit=limit)
        
        return JsonResponse({
            'ok': True,
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos]
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_productos_nuevos(request):
    """
    GET /catalogo/productos/nuevos/
    Obtiene productos nuevos (últimos 30 días por defecto)
    Query params: ?dias=30&limit=12
    """
    try:
        dias = int(request.GET.get('dias', 30))
        limit = int(request.GET.get('limit', 12))
        
        productos = service_catalogo.get_productos_nuevos(dias=dias, limit=limit)
        
        return JsonResponse({
            'ok': True,
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos],
            'dias': dias
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_productos_mas_vendidos(request):
    """
    GET /catalogo/productos/mas-vendidos/
    Obtiene productos más vendidos
    Query params: ?limit=10
    """
    try:
        limit = int(request.GET.get('limit', 10))
        productos = service_catalogo.get_productos_mas_vendidos(limit=limit)
        
        return JsonResponse({
            'ok': True,
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos],
            'note': 'Esta funcionalidad requiere integración con el módulo de ventas'
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ============= CATEGORÍAS =============

@require_http_methods(["GET"])
def get_categorias(request):
    """
    GET /catalogo/categorias/
    Lista todas las categorías con cantidad de productos
    """
    try:
        categorias = service_catalogo.get_todas_categorias()
        
        return JsonResponse({
            'ok': True,
            'categorias': [{
                'id': c.id,
                'nombre': c.nombre,
                'descripcion': c.descripcion,
                'total_productos': c.total_productos,
                'created_at': c.created_at.isoformat() if c.created_at else None,
            } for c in categorias],
            'total': categorias.count()
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_productos_por_categoria(request, id):
    """
    GET /catalogo/categorias/<id>/productos/
    Obtiene productos de una categoría específica
    Query params: ?page=1&per_page=12&order_by=precio&sort=asc
    """
    try:
        # Verificar que la categoría existe
        categoria = service_catalogo.get_categoria_by_id(id)
        
        # Obtener productos
        productos = service_catalogo.get_productos_por_categoria(id)
        
        # Aplicar ordenamiento
        order_by = request.GET.get('order_by', 'created_at')
        sort = request.GET.get('sort', 'desc')
        
        campos_validos = ['precio', 'nombre', 'created_at', 'stock']
        if order_by in campos_validos:
            if sort == 'desc':
                order_by = f'-{order_by}'
            productos = productos.order_by(order_by)
        
        # Paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        
        paginator = Paginator(productos, per_page)
        productos_page = paginator.get_page(page)
        
        return JsonResponse({
            'ok': True,
            'categoria': {
                'id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion,
                'total_productos': categoria.total_productos
            },
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos_page],
            'pagination': {
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': productos_page.number,
                'has_next': productos_page.has_next(),
                'has_previous': productos_page.has_previous(),
            }
        }, status=200)
    except Categoria.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Categoría no encontrada'}, status=404)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': f'Error en parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ============= MARCAS =============

@require_http_methods(["GET"])
def get_marcas(request):
    """
    GET /catalogo/marcas/
    Lista todas las marcas con cantidad de productos
    """
    try:
        marcas = service_catalogo.get_todas_marcas()
        
        return JsonResponse({
            'ok': True,
            'marcas': [{
                'id': m.id,
                'nombre': m.nombre,
                'total_productos': m.total_productos,
                'created_at': m.created_at.isoformat() if m.created_at else None,
            } for m in marcas],
            'total': marcas.count()
        }, status=200)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_productos_por_marca(request, id):
    """
    GET /catalogo/marcas/<id>/productos/
    Obtiene productos de una marca específica
    Query params: ?page=1&per_page=12&order_by=precio&sort=asc
    """
    try:
        # Verificar que la marca existe
        marca = service_catalogo.get_marca_by_id(id)
        
        # Obtener productos
        productos = service_catalogo.get_productos_por_marca(id)
        
        # Aplicar ordenamiento
        order_by = request.GET.get('order_by', 'created_at')
        sort = request.GET.get('sort', 'desc')
        
        campos_validos = ['precio', 'nombre', 'created_at', 'stock']
        if order_by in campos_validos:
            if sort == 'desc':
                order_by = f'-{order_by}'
            productos = productos.order_by(order_by)
        
        # Paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 12))
        
        paginator = Paginator(productos, per_page)
        productos_page = paginator.get_page(page)
        
        return JsonResponse({
            'ok': True,
            'marca': {
                'id': marca.id,
                'nombre': marca.nombre,
                'total_productos': marca.total_productos
            },
            'productos': [service_catalogo.serializar_producto_simple(p) for p in productos_page],
            'pagination': {
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': productos_page.number,
                'has_next': productos_page.has_next(),
                'has_previous': productos_page.has_previous(),
            }
        }, status=200)
    except Marca.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Marca no encontrada'}, status=404)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': f'Error en parámetros: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

