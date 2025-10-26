from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Producto, Categoria, Marca, Garantia

def get_all_productos():
    """
    Obtiene todos los productos con información de categoría, marca y garantía.
    """
    productos = Producto.objects.select_related('categoria', 'marca', 'garantia').all()
    result = []
    for producto in productos:
        result.append({
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": str(producto.precio),
            "stock": producto.stock,
            "image_url": producto.image_url,
            "created_at": producto.created_at,
            "updated_at": producto.updated_at,
            "categoria": {
                "id": producto.categoria.id,
                "nombre": producto.categoria.nombre,
            },
            "marca": {
                "id": producto.marca.id,
                "nombre": producto.marca.nombre,
            },
            "garantia": {
                "id": producto.garantia.id,
                "cobertura": producto.garantia.cobertura,
            } if producto.garantia else None,
        })
    return result

def get_producto_by_id(producto_id):
    """
    Obtiene un producto por su ID con toda la información relacionada.
    """
    try:
        producto = Producto.objects.select_related('categoria', 'marca', 'garantia').get(pk=producto_id)
        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": str(producto.precio),
            "stock": producto.stock,
            "image_url": producto.image_url,
            "created_at": producto.created_at,
            "updated_at": producto.updated_at,
            "categoria": {
                "id": producto.categoria.id,
                "nombre": producto.categoria.nombre,
            },
            "marca": {
                "id": producto.marca.id,
                "nombre": producto.marca.nombre,
            },
            "garantia": {
                "id": producto.garantia.id,
                "cobertura": producto.garantia.cobertura,
            } if producto.garantia else None,
        }
    except Producto.DoesNotExist:
        raise ValidationError(f"Producto con id {producto_id} no encontrado")

def create_producto(nombre, descripcion, precio, stock, categoria_id, marca_id, garantia_id=None, image_url=None):
    """
    Crea un nuevo producto.
    """
    # Validaciones
    if not nombre or not nombre.strip():
        raise ValidationError("El nombre del producto es obligatorio")
    
    if not descripcion or not descripcion.strip():
        raise ValidationError("La descripción del producto es obligatoria")
    
    if not precio or precio <= 0:
        raise ValidationError("El precio debe ser mayor a 0")
    
    if stock is None or stock < 0:
        raise ValidationError("El stock no puede ser negativo")
    
    if not categoria_id:
        raise ValidationError("Debe especificar una categoría")
    
    if not marca_id:
        raise ValidationError("Debe especificar una marca")
    
    # Verificar que existan las entidades relacionadas
    try:
        categoria = Categoria.objects.get(pk=categoria_id)
    except Categoria.DoesNotExist:
        raise ValidationError(f"Categoría con id {categoria_id} no encontrada")
    
    try:
        marca = Marca.objects.get(pk=marca_id)
    except Marca.DoesNotExist:
        raise ValidationError(f"Marca con id {marca_id} no encontrada")
    
    garantia = None
    if garantia_id:
        try:
            garantia = Garantia.objects.get(pk=garantia_id)
        except Garantia.DoesNotExist:
            raise ValidationError(f"Garantía con id {garantia_id} no encontrada")
    
    with transaction.atomic():
        producto = Producto.objects.create(
            nombre=nombre.strip(),
            descripcion=descripcion.strip(),
            precio=precio,
            stock=stock,
            categoria=categoria,
            marca=marca,
            garantia=garantia,
            image_url=image_url
        )
        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": str(producto.precio),
            "stock": producto.stock,
            "image_url": producto.image_url,
            "created_at": producto.created_at,
            "updated_at": producto.updated_at,
            "categoria": {
                "id": producto.categoria.id,
                "nombre": producto.categoria.nombre,
            },
            "marca": {
                "id": producto.marca.id,
                "nombre": producto.marca.nombre,
            },
            "garantia": {
                "id": producto.garantia.id,
                "cobertura": producto.garantia.cobertura,
            } if producto.garantia else None,
        }

def update_producto(producto_id, nombre=None, descripcion=None, precio=None, stock=None, 
                    categoria_id=None, marca_id=None, garantia_id=None, image_url=None):
    """
    Actualiza un producto existente.
    """
    try:
        with transaction.atomic():
            producto = Producto.objects.select_related('categoria', 'marca', 'garantia').get(pk=producto_id)
            
            if nombre is not None:
                if not nombre.strip():
                    raise ValidationError("El nombre no puede estar vacío")
                producto.nombre = nombre.strip()
            
            if descripcion is not None:
                if not descripcion.strip():
                    raise ValidationError("La descripción no puede estar vacía")
                producto.descripcion = descripcion.strip()
            
            if precio is not None:
                if precio <= 0:
                    raise ValidationError("El precio debe ser mayor a 0")
                producto.precio = precio
            
            if stock is not None:
                if stock < 0:
                    raise ValidationError("El stock no puede ser negativo")
                producto.stock = stock
            
            if categoria_id is not None:
                try:
                    categoria = Categoria.objects.get(pk=categoria_id)
                    producto.categoria = categoria
                except Categoria.DoesNotExist:
                    raise ValidationError(f"Categoría con id {categoria_id} no encontrada")
            
            if marca_id is not None:
                try:
                    marca = Marca.objects.get(pk=marca_id)
                    producto.marca = marca
                except Marca.DoesNotExist:
                    raise ValidationError(f"Marca con id {marca_id} no encontrada")
            
            if garantia_id is not None:
                if garantia_id == 0:  # Permitir eliminar garantía enviando 0
                    producto.garantia = None
                else:
                    try:
                        garantia = Garantia.objects.get(pk=garantia_id)
                        producto.garantia = garantia
                    except Garantia.DoesNotExist:
                        raise ValidationError(f"Garantía con id {garantia_id} no encontrada")
            
            if image_url is not None:
                producto.image_url = image_url
            
            producto.save()
            
            return {
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "precio": str(producto.precio),
                "stock": producto.stock,
                "image_url": producto.image_url,
                "created_at": producto.created_at,
                "updated_at": producto.updated_at,
                "categoria": {
                    "id": producto.categoria.id,
                    "nombre": producto.categoria.nombre,
                },
                "marca": {
                    "id": producto.marca.id,
                    "nombre": producto.marca.nombre,
                },
                "garantia": {
                    "id": producto.garantia.id,
                    "cobertura": producto.garantia.cobertura,
                } if producto.garantia else None,
            }
    except Producto.DoesNotExist:
        raise ValidationError(f"Producto con id {producto_id} no encontrado")

def delete_producto(producto_id):
    """
    Elimina un producto por su ID.
    """
    try:
        with transaction.atomic():
            producto = Producto.objects.get(pk=producto_id)
            producto.delete()
            return True
    except Producto.DoesNotExist:
        raise ValidationError(f"Producto con id {producto_id} no encontrado")
