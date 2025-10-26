from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from ..services import categoria as categoria_service
from users.services.jwt import jwt_required

# Create your views here.

# ============= CATEGORÍAS =============
@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_categorias(request):
    """
    GET /products/categorias/
    Obtiene todas las categorías.
    """
    try:
        categorias = categoria_service.get_all_categorias()
        return JsonResponse({"ok": True, "categorias": categorias}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_categoria(request, id): 
    """
    GET /products/categorias/<id>/
    Obtiene una categoría por su ID.
    """
    try:
        categoria = categoria_service.get_categoria_by_id(id)
        return JsonResponse({"ok": True, "categoria": categoria}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_categoria(request):
    """
    POST /products/categorias/
    Crea una nueva categoría.
    Body: {"nombre": "...", "descripcion": "..."}
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        descripcion = payload.get("descripcion")
        
        categoria = categoria_service.create_categoria(nombre, descripcion)
        return JsonResponse({"ok": True, "categoria": categoria}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_categoria(request, id):
    """
    PUT /products/categorias/<id>/
    Actualiza una categoría existente.
    Body: {"nombre": "...", "descripcion": "..."}
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        descripcion = payload.get("descripcion")
        
        categoria = categoria_service.update_categoria(id, nombre, descripcion)
        return JsonResponse({"ok": True, "categoria": categoria}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_categoria(request, id):
    """
    DELETE /products/categorias/<id>/
    Elimina una categoría.
    """
    try:
        categoria_service.delete_categoria(id)
        return JsonResponse({"ok": True, "message": "Categoría eliminada"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
