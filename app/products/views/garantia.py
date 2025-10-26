from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from ..services import garantia as garantia_service
from users.services.jwt import jwt_required

# ============= GARANTÍAS =============

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_garantias(request):
    """
    GET /products/garantias
    Obtiene todas las garantías (requiere token JWT).
    """
    try:
        garantias = garantia_service.get_all_garantias()
        return JsonResponse({"ok": True, "garantias": garantias}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_garantia(request, id):
    """
    GET /products/garantias/<id>
    Obtiene una garantía por su ID.
    """
    try:
        garantia = garantia_service.get_garantia_by_id(id)
        return JsonResponse({"ok": True, "garantia": garantia}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def create_garantia(request):
    """
    POST /products/garantias/create
    Crea una nueva garantía.
    Body: {"cobertura": 12, "marca_id": 1}
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        cobertura = payload.get("cobertura")
        marca_id = payload.get("marca_id")
        
        garantia = garantia_service.create_garantia(cobertura, marca_id)
        return JsonResponse({"ok": True, "garantia": garantia}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["PUT"])
def update_garantia(request, id):
    """
    PUT /products/garantias/<id>/update
    Actualiza una garantía existente.
    Body: {"cobertura": 24, "marca_id": 2}
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        cobertura = payload.get("cobertura")
        marca_id = payload.get("marca_id")
        
        garantia = garantia_service.update_garantia(id, cobertura, marca_id)
        return JsonResponse({"ok": True, "garantia": garantia}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["DELETE"])
def delete_garantia(request, id):
    """
    DELETE /products/garantias/<id>/delete
    Elimina una garantía.
    """
    try:
        garantia_service.delete_garantia(id)
        return JsonResponse({"ok": True, "message": "Garantía eliminada"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
