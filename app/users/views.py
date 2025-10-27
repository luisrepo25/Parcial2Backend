from django.http import HttpResponse, JsonResponse
from .services import services as user_services
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from users.services.jwt import jwt_required

import json

def hello(request):
    return HttpResponse("HUwU")

# ============= USUARIOS =============
@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_users(request):
    """GET /users/ - Obtiene todos los usuarios"""
    try:
        users = user_services.get_users()
        return JsonResponse({"ok": True, "users": users}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_user(request, id):
    """GET /users/<id> - Obtiene un usuario por ID"""
    try:
        user = user_services.get_user_by_id(id)
        return JsonResponse({"ok": True, "user": user}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """
    POST /users/create - Crea un usuario (base, cliente o admin)
    Body: {
        "correo": "...",
        "password": "...",
        "tipo_usuario": "cliente" | "admin" | "usuario",
        // Si tipo_usuario es "cliente":
        "nombres": "...",
        "apellidoPaterno": "...",
        "apellidoMaterno": "...",
        "ci": "...",
        "telefono": "..." (opcional)
        // Si tipo_usuario es "admin":
        "nombre": "..."
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        correo = payload.get("correo")
        password = payload.get("password")
        tipo_usuario = payload.get("tipo_usuario", "usuario")
        
        # Extraer datos adicionales según el tipo
        kwargs = {}
        if tipo_usuario == "cliente":
            kwargs["nombres"] = payload.get("nombres")
            kwargs["apellidoPaterno"] = payload.get("apellidoPaterno")
            kwargs["apellidoMaterno"] = payload.get("apellidoMaterno")
            kwargs["ci"] = payload.get("ci")
            kwargs["telefono"] = payload.get("telefono")
        elif tipo_usuario == "admin":
            kwargs["nombre"] = payload.get("nombre")
        
        usuario = user_services.create_user(correo, password, tipo_usuario, **kwargs)
        return JsonResponse({"ok": True, "usuario": usuario}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["PUT"])
def update_user(request, id):
    """
    PUT /users/<id>/update - Actualiza un usuario
    Body: {
        "correo": "..." (opcional),
        "password": "..." (opcional)
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        correo = payload.get("correo")
        password = payload.get("password")
        
        usuario = user_services.update_user(id, correo, password)
        return JsonResponse({"ok": True, "usuario": usuario}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request, id):
    """DELETE /users/<id>/delete - Elimina un usuario"""
    try:
        user_services.delete_user(id)
        return JsonResponse({"ok": True, "message": "Usuario eliminado"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

# ============= CLIENTES =============

@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_clientes(request):
    """GET /users/clientes - Obtiene todos los clientes"""
    try:
        clientes = user_services.get_all_clientes()
        return JsonResponse({"ok": True, "clientes": clientes}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_cliente(request, id):
    """GET /users/clientes/<id> - Obtiene un cliente por ID"""
    try:
        cliente = user_services.get_cliente_by_id(id)
        return JsonResponse({"ok": True, "cliente": cliente}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_cliente(request):
    """
    POST /users/register - Crea un nuevo cliente
    Body: {
        "correo": "...",
        "nombres": "...",
        "password": "...",
        "apellidoMaterno": "...",
        "apellidoPaterno": "...",
        "ci": "...",
        "telefono": "..." (opcional)
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        correo = payload.get("correo")
        nombres = payload.get("nombres")
        password = payload.get("password")
        apellidoMaterno = payload.get("apellidoMaterno")
        apellidoPaterno = payload.get("apellidoPaterno")
        ci = payload.get("ci")
        telefono = payload.get("telefono")

        resultado = user_services.create_cliente(
            correo, nombres, password, apellidoMaterno, apellidoPaterno, ci, telefono
        )
        return JsonResponse({"ok": True, "resultado": resultado}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["PUT"])
def update_cliente(request, id):
    """
    PUT /users/clientes/<id>/update - Actualiza un cliente
    Body: {
        "nombres": "..." (opcional),
        "apellidoPaterno": "..." (opcional),
        "apellidoMaterno": "..." (opcional),
        "ci": "..." (opcional),
        "telefono": "..." (opcional)
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombres = payload.get("nombres")
        apellidoPaterno = payload.get("apellidoPaterno")
        apellidoMaterno = payload.get("apellidoMaterno")
        ci = payload.get("ci")
        telefono = payload.get("telefono")
        
        cliente = user_services.update_cliente(
            id, nombres, apellidoPaterno, apellidoMaterno, ci, telefono
        )
        return JsonResponse({"ok": True, "cliente": cliente}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_cliente(request, id):
    """DELETE /users/clientes/<id>/delete - Elimina un cliente"""
    try:
        user_services.delete_cliente(id)
        return JsonResponse({"ok": True, "message": "Cliente eliminado"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

# ============= ADMINISTRADORES =============
@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_admins(request):
    """GET /users/admins - Obtiene todos los administradores"""
    try:
        admins = user_services.get_all_admins()
        return JsonResponse({"ok": True, "admins": admins}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["GET"])
def get_admin(request, id):
    """GET /users/admins/<id> - Obtiene un admin por ID"""
    try:
        admin = user_services.get_admin_by_id(id)
        return JsonResponse({"ok": True, "admin": admin}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["POST"])
def register_admin(request):
    """
    POST /users/register_admin - Crea un nuevo administrador
    Body: {
        "correo": "...",
        "nombres": "...",
        "password": "..."
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        correo = payload.get("correo")
        nombres = payload.get("nombres")
        password = payload.get("password")

        resultado = user_services.create_admin(correo, nombres, password)
        return JsonResponse({"ok": True, "resultado": resultado}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["PUT"])
def update_admin(request, id):
    """
    PUT /users/admins/<id>/update - Actualiza un administrador
    Body: {
        "nombre": "..." (opcional)
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        
        admin = user_services.update_admin(id, nombre)
        return JsonResponse({"ok": True, "admin": admin}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@jwt_required
@csrf_exempt
@require_http_methods(["DELETE"])
def delete_admin(request, id):
    """DELETE /users/admins/<id>/delete - Elimina un administrador"""
    try:
        user_services.delete_admin(id)
        return JsonResponse({"ok": True, "message": "Administrador eliminado"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

# ============= AUTENTICACIÓN =============

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """
    POST /users/auth - Autentica un usuario
    Body: {
        "correo": "...",
        "password": "..."
    }
    """
    try:
        payload = json.loads(request.body.decode() or "{}")
        usuario = user_services.authenticate_usuario(
            payload.get("correo"), 
            payload.get("password")
        )
        
        if not usuario:
            return JsonResponse({"ok": False, "msg": "credenciales inválidas"}, status=401)

        # Datos base del usuario
        user_data = {
            "id": getattr(usuario, "pk", None),
            "correo": getattr(usuario, "correo", None),
        }

        # Agregar token si el servicio lo proporciona
        token = getattr(usuario, "token", None)
        if token:
            user_data["token"] = token

        # Si el usuario tiene un objeto Cliente relacionado
        if hasattr(usuario, "cliente"):
            c = usuario.cliente
            user_data["rol"] = "cliente"
            user_data["cliente"] = {
                "id": getattr(c, "pk", None),
                "usuario_id": getattr(c, "usuario_id", None),
                "nombres": getattr(c, "nombres", None),
                "apellidoMaterno": getattr(c, "apellidoMaterno", None),
                "apellidoPaterno": getattr(c, "apellidoPaterno", None),
                "ci": getattr(c, "ci", None),
                "telefono": getattr(c, "telefono", None),
            }
        # Si el usuario tiene un objeto Administrador relacionado
        elif hasattr(usuario, "administrador"):
            a = usuario.administrador
            user_data["rol"] = "admin"
            user_data["administrador"] = {
                "id": getattr(a, "pk", None),
                "nombre": getattr(a, "nombre", None),
            }
        else:
            user_data["rol"] = "usuario"

        return JsonResponse({"ok": True, "usuario": user_data})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


