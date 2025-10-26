
from ..models import *
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password , check_password

import jwt
from datetime import datetime, timedelta
from django.conf import settings

def get_users():
    # Crearemos una lista de usuarios de ejemplo
    
    usuarios = Usuario.objects.all()
    usuarios_list = []
    for usuario in usuarios:
        usuarios_list.append({
            "id": usuario.id,
            "correo": usuario.correo,
            "nombres": usuario.nombres,
        })
    return usuarios_list

# Funcion para crear un usuario nuevo 
def create_user(correo, password):
    hashed_password = make_password(password)
    nuevo_usuario = Usuario(correo=correo , password=hashed_password)
    nuevo_usuario.save()
    return nuevo_usuario    

# funcion para crear un cliente nuevo
# Primero crearemos su usuario de dicho cliente y luego crearemos el cliente
def create_cliente(correo, nombres, password, apellidoMaterno, apellidoPaterno, ci, telefono):
    usuario = create_user(correo, password)
    nuevo_cliente = Cliente(usuario=usuario, nombres=nombres, apellidoMaterno=apellidoMaterno, apellidoPaterno=apellidoPaterno, ci=ci, telefono=telefono)
    nuevo_cliente.save()
    return nuevo_cliente

def create_admin(correo,nombres,password):
    usuario = create_user(correo, password)
    nuevo_admin = Administrador(usuario=usuario, nombre=nombres)
    nuevo_admin.save()
    return nuevo_admin

# Funcion utilizando PyJwt para crear un token JWT para el usuario que se autentica
def create_jwt_token(usuario):
    payload = {
        'user_id': usuario.id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

# Funcion para autenticar a un usuario y devolverle el usuario y su token JWT
def authenticate_usuario( correo , password ):
    try:
        usuario = Usuario.objects.get(correo=correo)
        if check_password(password, usuario.password):
            token = create_jwt_token(usuario)
            # Sumamos el token a la respuesta para devolverla como un JSON
            usuario.token = token
            return usuario
        else:
            return None
    except ObjectDoesNotExist:
        return None

