from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from ..services import marca as marca_service
from users.services.jwt import jwt_required

# ============= MARCAS =============

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_marcas(request):
    """
    GET /products/marcas
    Obtiene todas las marcas (requiere token JWT).
    """
    try:
        marcas = marca_service.get_all_marcas()
        return JsonResponse({"ok": True, "marcas": marcas}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_marca(request, id):
    """
    GET /products/marcas/<id>
    Obtiene una marca por su ID.
    """
    try:
        marca = marca_service.get_marca_by_id(id)
        return JsonResponse({"ok": True, "marca": marca}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def create_marca(request):
    """
    POST /products/marcas/create
    Crea una nueva marca.
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        
        marca = marca_service.create_marca(nombre)
        return JsonResponse({"ok": True, "marca": marca}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["PUT"])
def update_marca(request, id):
    """
    PUT /products/marcas/<id>/update
    Actualiza una marca existente.
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        
        marca = marca_service.update_marca(id, nombre)
        return JsonResponse({"ok": True, "marca": marca}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["DELETE"])
def delete_marca(request, id):
    """
    DELETE /products/marcas/<id>/delete
    Elimina una marca.
    """
    try:
        marca_service.delete_marca(id)
        return JsonResponse({"ok": True, "message": "Marca eliminada"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
