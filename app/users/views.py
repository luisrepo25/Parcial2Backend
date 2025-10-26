from django.http import HttpResponse , JsonResponse
from .services import services as user_services
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_GET,require_POST

import json

def hello(request):
    return HttpResponse("HUwU")

def register(request):
    return HttpResponse("This is the registration page.")

@require_http_methods(["GET"])
# @require_GET
def get_users(request):   
    # users = user_services.get_users()
    # return JsonResponse({"ok": True, "users": users}, status=200)

    # Ahora manejaremos los errores por si la base de datos no responde
    try:
        users = user_services.get_users()
        return JsonResponse({"ok": True, "users": users}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
# Funcion para registrarse como un cliente nuevo
# @require_POST
@csrf_exempt
@require_http_methods(["POST"])
def register_cliente(request):
    payload = json.loads(request.body.decode() or "{}")
    correo = payload.get("correo")
    nombres = payload.get("nombres")
    password = payload.get("password")
    apellidoMaterno = payload.get("apellidoMaterno")
    apellidoPaterno = payload.get("apellidoPaterno")
    ci = payload.get("ci")
    telefono = payload.get("telefono")

    try:
        nuevo_cliente = user_services.create_cliente(correo, nombres, password, apellidoMaterno, apellidoPaterno, ci, telefono)
        return JsonResponse({
            "ok": True,
            "cliente": {
                "id": nuevo_cliente.pk,
                "apellidoMaterno": nuevo_cliente.apellidoMaterno,
                "apellidoPaterno": nuevo_cliente.apellidoPaterno,
                "ci": nuevo_cliente.ci,
                "telefono": nuevo_cliente.telefono,
            }
        }, status=201)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

    # funcion para crear un admin nuevo
@csrf_exempt
@require_http_methods(["POST"])
def register_admin(request):
    payload = json.loads(request.body.decode() or "{}")
    correo = payload.get("correo")
    nombres = payload.get("nombres")
    password = payload.get("password")

    try:
        nuevo_admin = user_services.create_admin(correo, nombres, password)
        return JsonResponse({
            "ok": True,
            "admin": {
                "id": nuevo_admin.pk,
                "correo": nuevo_admin.usuario.correo,
                "nombres": nuevo_admin.nombre,
            }
        }, status=201)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
# Funcion para el login de un usuario
# @require_POST
@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    payload = json.loads(request.body.decode() or "{}")
    usuario = user_services.authenticate_usuario(payload.get("correo"), payload.get("password"))
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
            "apellidoMaterno": getattr(c, "apellidoMaterno", None),
            "apellidoPaterno": getattr(c, "apellidoPaterno", None),
            "ci": getattr(c, "ci", None),
            "telefono": getattr(c, "telefono", None),
        }
    # Si el usuario tiene un objeto Administrador relacionado
    elif hasattr(usuario, "administrador"):
        a = usuario.administrador
        user_data["rol"] = "admin"
        # Si Administrador no tiene campos propios, devolvemos referencia al usuario
        user_data["administrador"] = {
            "id": getattr(a, "pk", None),
            "nombre": getattr(a, "nombre", None),
            # añadir otros campos de Administrador si existen
        }
    else:
        user_data["rol"] = "usuario"

    return JsonResponse({"ok": True, "usuario": user_data})


