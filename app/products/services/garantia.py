from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Garantia, Marca

def get_all_garantias():
    """
    Obtiene todas las garantías con información de la marca.
    """
    garantias = Garantia.objects.select_related('Marca').all()
    result = []
    for garantia in garantias:
        result.append({
            "id": garantia.id,
            "cobertura": garantia.cobertura,
            "marca": {
                "id": garantia.Marca.id,
                "nombre": garantia.Marca.nombre,
            } if garantia.Marca else None,
        })
    return result

def get_garantia_by_id(garantia_id):
    """
    Obtiene una garantía por su ID con información de la marca.
    """
    try:
        garantia = Garantia.objects.select_related('Marca').get(pk=garantia_id)
        return {
            "id": garantia.id,
            "cobertura": garantia.cobertura,
            "marca": {
                "id": garantia.Marca.id,
                "nombre": garantia.Marca.nombre,
            } if garantia.Marca else None,
        }
    except Garantia.DoesNotExist:
        raise ValidationError(f"Garantía con id {garantia_id} no encontrada")

def create_garantia(cobertura, marca_id):
    """
    Crea una nueva garantía asociada a una marca.
    """
    if not cobertura or cobertura <= 0:
        raise ValidationError("La cobertura debe ser mayor a 0 meses")
    
    if not marca_id:
        raise ValidationError("Debe especificar una marca")
    
    try:
        marca = Marca.objects.get(pk=marca_id)
    except Marca.DoesNotExist:
        raise ValidationError(f"Marca con id {marca_id} no encontrada")
    
    with transaction.atomic():
        garantia = Garantia.objects.create(
            cobertura=cobertura,
            Marca=marca
        )
        return {
            "id": garantia.id,
            "cobertura": garantia.cobertura,
            "marca": {
                "id": garantia.Marca.id,
                "nombre": garantia.Marca.nombre,
            },
        }

def update_garantia(garantia_id, cobertura=None, marca_id=None):
    """
    Actualiza una garantía existente.
    """
    try:
        with transaction.atomic():
            garantia = Garantia.objects.select_related('Marca').get(pk=garantia_id)
            
            if cobertura is not None:
                if cobertura <= 0:
                    raise ValidationError("La cobertura debe ser mayor a 0 meses")
                garantia.cobertura = cobertura
            
            if marca_id is not None:
                try:
                    marca = Marca.objects.get(pk=marca_id)
                    garantia.Marca = marca
                except Marca.DoesNotExist:
                    raise ValidationError(f"Marca con id {marca_id} no encontrada")
            
            garantia.save()
            
            return {
                "id": garantia.id,
                "cobertura": garantia.cobertura,
                "marca_id": garantia.Marca.id,
                "marca_nombre": garantia.Marca.nombre,
            }
    except Garantia.DoesNotExist:
        raise ValidationError(f"Garantía con id {garantia_id} no encontrada")

def delete_garantia(garantia_id):
    """
    Elimina una garantía por su ID.
    """
    try:
        with transaction.atomic():
            garantia = Garantia.objects.get(pk=garantia_id)
            garantia.delete()
            return True
    except Garantia.DoesNotExist:
        raise ValidationError(f"Garantía con id {garantia_id} no encontrada")
