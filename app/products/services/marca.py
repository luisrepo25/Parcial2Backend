from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Marca

def get_all_marcas():
    """
    Obtiene todas las marcas.
    """
    qs = Marca.objects.all().values("id", "nombre","created_at", "updated_at")
    return list(qs)

def get_marca_by_id(marca_id):
    """
    Obtiene una marca por su ID.
    """
    try:
        marca = Marca.objects.get(pk=marca_id)
        return {
            "id": marca.id,
            "nombre": marca.nombre,
            "created_at": marca.created_at,
            "updated_at": marca.updated_at,
        }
    except Marca.DoesNotExist:
        raise ValidationError(f"Marca con id {marca_id} no encontrada")

def create_marca(nombre):
    """
    Crea una nueva marca.
    """
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la marca es obligatorio")
    
    with transaction.atomic():
        marca = Marca.objects.create(
            nombre=nombre.strip(),
        )
        return {
            "id": marca.id,
            "nombre": marca.nombre,
            "created_at": marca.created_at,
            "updated_at": marca.updated_at,
        }

def update_marca(marca_id, nombre=None):
    """
    Actualiza una marca existente.
    """
    try:
        with transaction.atomic():
            marca = Marca.objects.get(pk=marca_id)
            
            if nombre is not None:
                if not nombre.strip():
                    raise ValidationError("El nombre no puede estar vacío")
                marca.nombre = nombre.strip()
            
            marca.save()
            
            return {
                "id": marca.id,
                "nombre": marca.nombre,
                "created_at": marca.created_at,
                "updated_at": marca.updated_at,
            }
    except Marca.DoesNotExist:
        raise ValidationError(f"Marca con id {marca_id} no encontrada")

def delete_marca(marca_id):
    """
    Elimina una marca por su ID.
    """
    try:
        with transaction.atomic():
            marca = Marca.objects.get(pk=marca_id)
            marca.delete()
            return True
    except Marca.DoesNotExist:
        raise ValidationError(f"Marca con id {marca_id} no encontrada")
