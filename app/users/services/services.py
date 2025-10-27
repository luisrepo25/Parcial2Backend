
from ..models import *
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.hashers import make_password , check_password
from django.db import transaction


import jwt
from datetime import datetime, timedelta
from django.conf import settings

# ============= USUARIOS =============

def get_users():
    """Obtiene todos los usuarios"""
    usuarios = Usuario.objects.all()
    usuarios_list = []
    for usuario in usuarios:
        usuarios_list.append({
            "id": usuario.id,
            "correo": usuario.correo,
            "created_at": usuario.created_at,
            "updated_at": usuario.updated_at,
        })
    return usuarios_list

def get_user_by_id(user_id):
    """Obtiene un usuario por ID"""
    try:
        usuario = Usuario.objects.get(pk=user_id)
        return {
            "id": usuario.id,
            "correo": usuario.correo,
            "created_at": usuario.created_at,
            "updated_at": usuario.updated_at,
        }
    except Usuario.DoesNotExist:
        raise ValidationError(f"Usuario con id {user_id} no encontrado")

def create_user(correo, password, tipo_usuario="usuario", **kwargs):
    """
    Crea un usuario y opcionalmente un Cliente o Administrador
    tipo_usuario: 'cliente', 'admin', o 'usuario' (solo usuario base)
    kwargs: datos adicionales según el tipo (nombres, apellidos, ci, telefono para cliente; nombre para admin)
    """
    if not correo or not password:
        raise ValidationError("Correo y contraseña son obligatorios")
    
    # Verificar que el correo no exista
    if Usuario.objects.filter(correo=correo).exists():
        raise ValidationError(f"El correo {correo} ya está registrado")
    
    with transaction.atomic():
        hashed_password = make_password(password)
        nuevo_usuario = Usuario.objects.create(correo=correo, password=hashed_password)
        
        resultado = {
            "id": nuevo_usuario.id,
            "correo": nuevo_usuario.correo,
            "tipo": tipo_usuario,
            "created_at": nuevo_usuario.created_at,
        }
        
        # Crear Cliente si se especifica
        if tipo_usuario == "cliente":
            nombres = kwargs.get("nombres")
            apellidoPaterno = kwargs.get("apellidoPaterno")
            apellidoMaterno = kwargs.get("apellidoMaterno")
            ci = kwargs.get("ci")
            telefono = kwargs.get("telefono")
            
            if not all([nombres, apellidoPaterno, apellidoMaterno, ci]):
                raise ValidationError("Para crear un cliente se requieren: nombres, apellidoPaterno, apellidoMaterno, ci")
            
            cliente = Cliente.objects.create(
                usuario=nuevo_usuario,
                nombres=nombres,
                apellidoPaterno=apellidoPaterno,
                apellidoMaterno=apellidoMaterno,
                ci=ci,
                telefono=telefono
            )
            resultado["cliente"] = {
                "id": cliente.pk,
                "nombres": cliente.nombres,
                "apellidoPaterno": cliente.apellidoPaterno,
                "apellidoMaterno": cliente.apellidoMaterno,
                "ci": cliente.ci,
                "telefono": cliente.telefono,
            }
        
        # Crear Administrador si se especifica
        elif tipo_usuario == "admin":
            nombre = kwargs.get("nombre")
            if not nombre:
                raise ValidationError("Para crear un admin se requiere: nombre")
            
            admin = Administrador.objects.create(
                usuario=nuevo_usuario,
                nombre=nombre
            )
            resultado["administrador"] = {
                "id": admin.pk,
                "nombre": admin.nombre,
            }
        
        return resultado

def update_user(user_id, correo=None, password=None):
    """Actualiza un usuario (correo o contraseña)"""
    try:
        with transaction.atomic():
            usuario = Usuario.objects.get(pk=user_id)
            
            if correo is not None:
                # Verificar que el nuevo correo no esté en uso
                if Usuario.objects.filter(correo=correo).exclude(pk=user_id).exists():
                    raise ValidationError(f"El correo {correo} ya está en uso")
                usuario.correo = correo
            
            if password is not None:
                usuario.password = make_password(password)
            
            usuario.save()
            
            return {
                "id": usuario.id,
                "correo": usuario.correo,
                "updated_at": usuario.updated_at,
            }
    except Usuario.DoesNotExist:
        raise ValidationError(f"Usuario con id {user_id} no encontrado")

def delete_user(user_id):
    """Elimina un usuario (y su cliente/admin asociado por CASCADE)"""
    try:
        with transaction.atomic():
            usuario = Usuario.objects.get(pk=user_id)
            usuario.delete()
            return True
    except Usuario.DoesNotExist:
        raise ValidationError(f"Usuario con id {user_id} no encontrado")

# ============= CLIENTES =============

def get_all_clientes():
    """Obtiene todos los clientes con información del usuario"""
    clientes = Cliente.objects.select_related('usuario').all()
    result = []
    for cliente in clientes:
        result.append({
            "id": cliente.pk,
            "usuario_id": cliente.usuario.id,
            "correo": cliente.usuario.correo,
            "nombres": cliente.nombres,
            "apellidoPaterno": cliente.apellidoPaterno,
            "apellidoMaterno": cliente.apellidoMaterno,
            "ci": cliente.ci,
            "telefono": cliente.telefono,
        })
    return result

def get_cliente_by_id(cliente_id):
    """Obtiene un cliente por ID"""
    try:
        cliente = Cliente.objects.select_related('usuario').get(pk=cliente_id)
        return {
            "id": cliente.pk,
            "usuario_id": cliente.usuario.id,
            "correo": cliente.usuario.correo,
            "nombres": cliente.nombres,
            "apellidoPaterno": cliente.apellidoPaterno,
            "apellidoMaterno": cliente.apellidoMaterno,
            "ci": cliente.ci,
            "telefono": cliente.telefono,
        }
    except Cliente.DoesNotExist:
        raise ValidationError(f"Cliente con id {cliente_id} no encontrado")

def create_cliente(correo, nombres, password, apellidoMaterno, apellidoPaterno, ci, telefono):
    """Crea un cliente (wrapper del create_user)"""
    return create_user(
        correo=correo,
        password=password,
        tipo_usuario="cliente",
        nombres=nombres,
        apellidoPaterno=apellidoPaterno,
        apellidoMaterno=apellidoMaterno,
        ci=ci,
        telefono=telefono
    )

def update_cliente(cliente_id, nombres=None, apellidoPaterno=None, apellidoMaterno=None, ci=None, telefono=None):
    """Actualiza los datos de un cliente"""
    try:
        with transaction.atomic():
            cliente = Cliente.objects.get(pk=cliente_id)
            
            if nombres is not None:
                cliente.nombres = nombres
            if apellidoPaterno is not None:
                cliente.apellidoPaterno = apellidoPaterno
            if apellidoMaterno is not None:
                cliente.apellidoMaterno = apellidoMaterno
            if ci is not None:
                cliente.ci = ci
            if telefono is not None:
                cliente.telefono = telefono
            
            cliente.save()
            
            return {
                "id": cliente.pk,
                "nombres": cliente.nombres,
                "apellidoPaterno": cliente.apellidoPaterno,
                "apellidoMaterno": cliente.apellidoMaterno,
                "ci": cliente.ci,
                "telefono": cliente.telefono,
            }
    except Cliente.DoesNotExist:
        raise ValidationError(f"Cliente con id {cliente_id} no encontrado")

def delete_cliente(cliente_id):
    """Elimina un cliente (y su usuario por CASCADE)"""
    try:
        with transaction.atomic():
            cliente = Cliente.objects.get(pk=cliente_id)
            # Al eliminar el usuario, el cliente se elimina por CASCADE
            cliente.usuario.delete()
            return True
    except Cliente.DoesNotExist:
        raise ValidationError(f"Cliente con id {cliente_id} no encontrado")

# ============= ADMINISTRADORES =============

def get_all_admins():
    """Obtiene todos los administradores con información del usuario"""
    admins = Administrador.objects.select_related('usuario').all()
    result = []
    for admin in admins:
        result.append({
            "id": admin.pk,
            "usuario_id": admin.usuario.id,
            "correo": admin.usuario.correo,
            "nombre": admin.nombre,
        })
    return result

def get_admin_by_id(admin_id):
    """Obtiene un administrador por ID"""
    try:
        admin = Administrador.objects.select_related('usuario').get(pk=admin_id)
        return {
            "id": admin.pk,
            "usuario_id": admin.usuario.id,
            "correo": admin.usuario.correo,
            "nombre": admin.nombre,
        }
    except Administrador.DoesNotExist:
        raise ValidationError(f"Administrador con id {admin_id} no encontrado")

def create_admin(correo, nombres, password):
    """Crea un administrador (wrapper del create_user)"""
    return create_user(
        correo=correo,
        password=password,
        tipo_usuario="admin",
        nombre=nombres
    )

def update_admin(admin_id, nombre=None):
    """Actualiza el nombre de un administrador"""
    try:
        with transaction.atomic():
            admin = Administrador.objects.get(pk=admin_id)
            
            if nombre is not None:
                admin.nombre = nombre
            
            admin.save()
            
            return {
                "id": admin.pk,
                "nombre": admin.nombre,
            }
    except Administrador.DoesNotExist:
        raise ValidationError(f"Administrador con id {admin_id} no encontrado")

def delete_admin(admin_id):
    """Elimina un administrador (y su usuario por CASCADE)"""
    try:
        with transaction.atomic():
            admin = Administrador.objects.get(pk=admin_id)
            # Al eliminar el usuario, el admin se elimina por CASCADE
            admin.usuario.delete()
            return True
    except Administrador.DoesNotExist:
        raise ValidationError(f"Administrador con id {admin_id} no encontrado")

# ============= AUTENTICACIÓN =============

def create_jwt_token(usuario):
    """Crea un token JWT para el usuario"""
    payload = {
        'user_id': usuario.id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

def authenticate_usuario(correo, password):
    """Autentica un usuario y devuelve el usuario con token"""
    try:
        usuario = Usuario.objects.get(correo=correo)
        if check_password(password, usuario.password):
            token = create_jwt_token(usuario)
            usuario.token = token
            return usuario
        else:
            return None
    except ObjectDoesNotExist:
        return None

