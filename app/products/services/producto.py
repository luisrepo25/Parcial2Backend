from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Producto, Categoria, Marca, Garantia
import cloudinary.uploader

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
            "imagen_url": producto.imagen_url,  # Corregido: imagen_url
            "created_at": producto.created_at.isoformat() if producto.created_at else None,
            "updated_at": producto.updated_at.isoformat() if producto.updated_at else None,
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
            "imagen_url": producto.imagen_url,  # Corregido: imagen_url
            "created_at": producto.created_at.isoformat() if producto.created_at else None,
            "updated_at": producto.updated_at.isoformat() if producto.updated_at else None,
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

def create_producto(nombre, descripcion, precio, stock, categoria_id, marca_id, garantia_id=None, imagen=None):
    """
    Crea un nuevo producto con imagen opcional en Cloudinary.
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
            imagen=imagen
        )
        
        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": str(producto.precio),
            "stock": producto.stock,
            "imagen_url": producto.imagen_url,
            "created_at": producto.created_at.isoformat() if producto.created_at else None,
            "updated_at": producto.updated_at.isoformat() if producto.updated_at else None,
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
                    categoria_id=None, marca_id=None, garantia_id=None, imagen=None):
    """
    Actualiza un producto existente con soporte para actualizar imagen en Cloudinary.
    """
    print(f"[SERVICE update_producto] Iniciando actualización para producto ID: {producto_id}")
    print(f"[SERVICE update_producto] Parámetros recibidos:")
    print(f"  - nombre: {nombre}")
    print(f"  - descripcion: {descripcion}")
    print(f"  - precio: {precio}")
    print(f"  - stock: {stock}")
    print(f"  - categoria_id: {categoria_id}")
    print(f"  - marca_id: {marca_id}")
    print(f"  - garantia_id: {garantia_id}")
    print(f"  - imagen: {imagen}")
    
    try:
        with transaction.atomic():
            print(f"[SERVICE update_producto] Buscando producto ID: {producto_id}")
            producto = Producto.objects.select_related('categoria', 'marca', 'garantia').get(pk=producto_id)
            print(f"[SERVICE update_producto] ✅ Producto encontrado: {producto.nombre}")
            
            if nombre is not None:
                if not nombre.strip():
                    raise ValidationError("El nombre no puede estar vacío")
                print(f"[SERVICE update_producto] Actualizando nombre: '{producto.nombre}' -> '{nombre}'")
                producto.nombre = nombre.strip()
            
            if descripcion is not None:
                if not descripcion.strip():
                    raise ValidationError("La descripción no puede estar vacía")
                print(f"[SERVICE update_producto] Actualizando descripción")
                producto.descripcion = descripcion.strip()
            
            if precio is not None:
                if precio <= 0:
                    raise ValidationError("El precio debe ser mayor a 0")
                print(f"[SERVICE update_producto] Actualizando precio: {producto.precio} -> {precio}")
                producto.precio = precio
            
            if stock is not None:
                if stock < 0:
                    raise ValidationError("El stock no puede ser negativo")
                print(f"[SERVICE update_producto] Actualizando stock: {producto.stock} -> {stock}")
                producto.stock = stock
            
            if categoria_id is not None:
                try:
                    categoria = Categoria.objects.get(pk=categoria_id)
                    print(f"[SERVICE update_producto] Actualizando categoría: {producto.categoria.nombre} -> {categoria.nombre}")
                    producto.categoria = categoria
                except Categoria.DoesNotExist:
                    raise ValidationError(f"Categoría con id {categoria_id} no encontrada")
            
            if marca_id is not None:
                try:
                    marca = Marca.objects.get(pk=marca_id)
                    print(f"[SERVICE update_producto] Actualizando marca: {producto.marca.nombre} -> {marca.nombre}")
                    producto.marca = marca
                except Marca.DoesNotExist:
                    raise ValidationError(f"Marca con id {marca_id} no encontrada")
            
            if garantia_id is not None:
                if garantia_id == 0:  # Permitir eliminar garantía enviando 0
                    print(f"[SERVICE update_producto] Eliminando garantía")
                    producto.garantia = None
                else:
                    try:
                        garantia = Garantia.objects.get(pk=garantia_id)
                        print(f"[SERVICE update_producto] Actualizando garantía")
                        producto.garantia = garantia
                    except Garantia.DoesNotExist:
                        raise ValidationError(f"Garantía con id {garantia_id} no encontrada")
            
            # Si hay nueva imagen, Cloudinary automáticamente reemplaza la anterior
            if imagen is not None:
                print(f"[SERVICE update_producto] Actualizando imagen: {imagen.name if imagen else 'None'}")
                producto.imagen = imagen
            
            print(f"[SERVICE update_producto] Guardando producto...")
            producto.save()
            print(f"[SERVICE update_producto] ✅ Producto guardado exitosamente")
            
            return {
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "precio": str(producto.precio),
                "stock": producto.stock,
                "imagen_url": producto.imagen_url,
                "created_at": producto.created_at.isoformat() if producto.created_at else None,
                "updated_at": producto.updated_at.isoformat() if producto.updated_at else None,
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
        print(f"[SERVICE update_producto] ❌ Producto con id {producto_id} no encontrado")
        raise ValidationError(f"Producto con id {producto_id} no encontrado")
    except Exception as e:
        print(f"[SERVICE update_producto] ❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def delete_producto(producto_id):
    """
    Elimina un producto por su ID y su imagen de Cloudinary si existe.
    """
    try:
        with transaction.atomic():
            producto = Producto.objects.get(pk=producto_id)
            
            # Eliminar imagen de Cloudinary si existe
            if producto.imagen:
                try:
                    # Obtener el public_id de Cloudinary
                    public_id = producto.imagen.public_id
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    # Log error pero continuar con la eliminación del producto
                    print(f"Error al eliminar imagen de Cloudinary: {e}")
            
            producto.delete()
            return True
    except Producto.DoesNotExist:
        raise ValidationError(f"Producto con id {producto_id} no encontrado")
