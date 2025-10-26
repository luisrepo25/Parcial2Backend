from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from ..services import producto as producto_service
from users.services.jwt import jwt_required

# ============= PRODUCTOS =============

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_productos(request):
    """
    GET /products/productos
    Obtiene todos los productos (requiere token JWT).
    """
    try:
        productos = producto_service.get_all_productos()
        return JsonResponse({"ok": True, "productos": productos}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_producto(request, id):
    """
    GET /products/productos/<id>
    Obtiene un producto por su ID.
    """
    try:
        producto = producto_service.get_producto_by_id(id)
        return JsonResponse({"ok": True, "producto": producto}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def create_producto(request):
    """
    POST /products/productos/create
    Crea un nuevo producto.
    Body: {
        "nombre": "...",
        "descripcion": "...",
        "precio": 99.99,
        "stock": 10,
        "categoria_id": 1,
        "marca_id": 1,
        "garantia_id": 1,  // opcional
        "image_url": "..."  // opcional
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        descripcion = payload.get("descripcion")
        precio = payload.get("precio")
        stock = payload.get("stock")
        categoria_id = payload.get("categoria_id")
        marca_id = payload.get("marca_id")
        garantia_id = payload.get("garantia_id")
        image_url = payload.get("image_url")
        
        producto = producto_service.create_producto(
            nombre, descripcion, precio, stock, 
            categoria_id, marca_id, garantia_id, image_url
        )
        return JsonResponse({"ok": True, "producto": producto}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["PUT"])
def update_producto(request, id):
    """
    PUT /products/productos/<id>/update
    Actualiza un producto existente.
    Body: {
        "nombre": "...",
        "descripcion": "...",
        "precio": 99.99,
        "stock": 10,
        "categoria_id": 1,
        "marca_id": 1,
        "garantia_id": 1,  // opcional, usar 0 para eliminar garantía
        "image_url": "..."  // opcional
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        descripcion = payload.get("descripcion")
        precio = payload.get("precio")
        stock = payload.get("stock")
        categoria_id = payload.get("categoria_id")
        marca_id = payload.get("marca_id")
        garantia_id = payload.get("garantia_id")
        image_url = payload.get("image_url")
        
        producto = producto_service.update_producto(
            id, nombre, descripcion, precio, stock, 
            categoria_id, marca_id, garantia_id, image_url
        )
        return JsonResponse({"ok": True, "producto": producto}, status=200)
    except ValidationError as e:
        # mostrar en consola el error para depuración
        print(f"ValidationError al actualizar producto: {e}")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        print(f"ValidationError al actualizar producto: {e}")
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["DELETE"])
def delete_producto(request, id):
    """
    DELETE /products/productos/<id>/delete
    Elimina un producto.
    """
    try:
        producto_service.delete_producto(id)
        return JsonResponse({"ok": True, "message": "Producto eliminado"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
