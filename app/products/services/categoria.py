from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Categoria


def get_all_categorias():
    """
    Obtiene todas las categorías.
    """
    qs = Categoria.objects.all().values("id", "nombre", "descripcion", "created_at", "updated_at")
    return list(qs)

def get_categoria_by_id(categoria_id):
    """
    Obtiene una categoría por su ID.
    """
    try:
        categoria = Categoria.objects.get(pk=categoria_id)
        return {
            "id": categoria.id,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "created_at": categoria.created_at,
            "updated_at": categoria.updated_at,
        }
    except Categoria.DoesNotExist:
        raise ValidationError(f"Categoría con id {categoria_id} no encontrada")

def create_categoria(nombre, descripcion=None):
    """
    Crea una nueva categoría.
    """
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre de la categoría es obligatorio")
    
    with transaction.atomic():
        categoria = Categoria.objects.create(
            nombre=nombre.strip(),
            descripcion=descripcion
        )
        return {
            "id": categoria.id,
            "nombre": categoria.nombre,
            "descripcion": categoria.descripcion,
            "created_at": categoria.created_at,
            "updated_at": categoria.updated_at,
        }

def update_categoria(categoria_id, nombre=None, descripcion=None):
    """
    Actualiza una categoría existente.
    """
    try:
        with transaction.atomic():
            categoria = Categoria.objects.get(pk=categoria_id)
            
            if nombre is not None:
                if not nombre.strip():
                    raise ValidationError("El nombre no puede estar vacío")
                categoria.nombre = nombre.strip()
            
            if descripcion is not None:
                categoria.descripcion = descripcion
            
            categoria.save()
            
            return {
                "id": categoria.id,
                "nombre": categoria.nombre,
                "descripcion": categoria.descripcion,
                "created_at": categoria.created_at,
                "updated_at": categoria.updated_at,
            }
    except Categoria.DoesNotExist:
        raise ValidationError(f"Categoría con id {categoria_id} no encontrada")

def delete_categoria(categoria_id):
    """
    Elimina una categoría por su ID.
    """
    try:
        with transaction.atomic():
            categoria = Categoria.objects.get(pk=categoria_id)
            categoria.delete()
            return True
    except Categoria.DoesNotExist:
        raise ValidationError(f"Categoría con id {categoria_id} no encontrada")
