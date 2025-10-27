from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
from ..services import producto as producto_service
from users.services.jwt import jwt_required

# ============= PRODUCTOS =============

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_productos(request):
    """
    GET /products/productos
    Obtiene todos los productos (requiere token JWT).
    """
    try:
        productos = producto_service.get_all_productos()
        return JsonResponse({"ok": True, "productos": productos}, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["GET"])
def get_producto(request, id):
    """
    GET /products/productos/<id>
    Obtiene un producto por su ID.
    """
    try:
        producto = producto_service.get_producto_by_id(id)
        return JsonResponse({"ok": True, "producto": producto}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required  # Mover JWT al final
def create_producto(request):
    """
    POST /products/productos/create
    Crea un nuevo producto con imagen opcional.
    
    Content-Type: multipart/form-data
    
    Campos del form-data:
    - nombre: string (requerido)
    - descripcion: string (requerido)
    - precio: decimal (requerido)
    - stock: integer (requerido)
    - categoria_id: integer (requerido)
    - marca_id: integer (requerido)
    - garantia_id: integer (opcional)
    - imagen: file (opcional) - archivo de imagen
    """
    try:
        # Obtener datos del form-data
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        categoria_id = request.POST.get("categoria_id")
        marca_id = request.POST.get("marca_id")
        garantia_id = request.POST.get("garantia_id")
        
        # Convertir tipos de datos
        if precio:
            precio = float(precio)
        if stock:
            stock = int(stock)
        if categoria_id:
            categoria_id = int(categoria_id)
        if marca_id:
            marca_id = int(marca_id)
        if garantia_id:
            garantia_id = int(garantia_id)
        
        # Obtener imagen si existe
        imagen = request.FILES.get('imagen') or request.FILES.get('image') or request.FILES.get('file')
        
        producto = producto_service.create_producto(
            nombre, descripcion, precio, stock, 
            categoria_id, marca_id, garantia_id, imagen
        )
        return JsonResponse({"ok": True, "producto": producto, "message": "Producto creado exitosamente"}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": f"Error en formato de datos: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])  # Cambiar a POST para que Django parsee multipart/form-data
@jwt_required
def update_producto(request, id):
    """
    POST /products/productos/<id>/update (cambiar en frontend también)
    Actualiza un producto existente.
    
    Content-Type: multipart/form-data
    
    Campos del form-data (todos opcionales):
    - nombre: string
    - descripcion: string
    - precio: decimal
    - stock: integer
    - categoria_id: integer
    - marca_id: integer
    - garantia_id: integer (usar 0 para eliminar garantía)
    - imagen: file - archivo de imagen nueva
    """
    try:
        # DEBUG: Información del request
        print("=" * 60)
        print(f"[UPDATE_PRODUCTO] ID: {id}")
        print(f"[UPDATE_PRODUCTO] Method: {request.method}")
        print(f"[UPDATE_PRODUCTO] Content-Type: {request.content_type}")
        print(f"[UPDATE_PRODUCTO] POST keys: {list(request.POST.keys())}")
        print(f"[UPDATE_PRODUCTO] POST data: {dict(request.POST)}")
        print(f"[UPDATE_PRODUCTO] FILES keys: {list(request.FILES.keys())}")
        print(f"[UPDATE_PRODUCTO] FILES data: {dict(request.FILES)}")
        
        # Intentar imprimir todos los posibles nombres de archivo
        for key in request.FILES.keys():
            file = request.FILES[key]
            print(f"[UPDATE_PRODUCTO] Archivo encontrado con key '{key}': {file.name}, {file.size} bytes")
        
        print("=" * 60)
        
        # Obtener datos del form-data
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        categoria_id = request.POST.get("categoria_id")
        marca_id = request.POST.get("marca_id")
        garantia_id = request.POST.get("garantia_id")
        
        # Buscar imagen con múltiples nombres posibles
        imagen = None
        for possible_key in ['imagen', 'image', 'file', 'photo', 'picture']:
            if possible_key in request.FILES:
                imagen = request.FILES[possible_key]
                print(f"[UPDATE_PRODUCTO] ✅ Imagen encontrada con key '{possible_key}': {imagen.name}")
                break
        
        if not imagen:
            print(f"[UPDATE_PRODUCTO] ⚠️ No se encontró imagen en FILES")
        
        # Convertir tipos si existen
        if precio is not None and precio != '':
            precio = float(precio)
        else:
            precio = None
            
        if stock is not None and stock != '':
            stock = int(stock)
        else:
            stock = None
            
        if categoria_id is not None and categoria_id != '':
            categoria_id = int(categoria_id)
        else:
            categoria_id = None
            
        if marca_id is not None and marca_id != '':
            marca_id = int(marca_id)
        else:
            marca_id = None
            
        if garantia_id is not None and garantia_id != '':
            garantia_id = int(garantia_id)
        else:
            garantia_id = None
        
        producto = producto_service.update_producto(
            id, nombre, descripcion, precio, stock, 
            categoria_id, marca_id, garantia_id, imagen
        )
        
        print(f"[UPDATE_PRODUCTO] ✅ Producto actualizado exitosamente")
        return JsonResponse({"ok": True, "producto": producto, "message": "Producto actualizado exitosamente"}, status=200)
    except ValidationError as e:
        print(f"[UPDATE_PRODUCTO] ❌ ValidationError: {str(e)}")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except ValueError as e:
        print(f"[UPDATE_PRODUCTO] ❌ ValueError: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": f"Error en formato de datos: {str(e)}"}, status=400)
    except Exception as e:
        print(f"[UPDATE_PRODUCTO] ❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@jwt_required
@require_http_methods(["DELETE"])
def delete_producto(request, id):
    """
    DELETE /products/productos/<id>/delete
    Elimina un producto y su imagen de Cloudinary.
    """
    try:
        producto_service.delete_producto(id)
        return JsonResponse({"ok": True, "message": "Producto eliminado exitosamente"}, status=200)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ============= ENDPOINT DE PRUEBA (SIN JWT) =============
@csrf_exempt
@jwt_required
@require_http_methods(["POST"])
def test_upload(request):
    """
    POST /products/productos/test-upload
    Endpoint de prueba para verificar subida de archivos SIN JWT.
    """
    try:
        print("=" * 60)
        print("TEST UPLOAD - POST data:", dict(request.POST))
        print("TEST UPLOAD - FILES data:", dict(request.FILES))
        print("TEST UPLOAD - Content-Type:", request.content_type)
        print("=" * 60)
        
        imagen = request.FILES.get('imagen') or request.FILES.get('image') or request.FILES.get('file')
        
        if not imagen:
            return JsonResponse({
                "ok": False, 
                "error": "No se recibió ningún archivo",
                "post_keys": list(request.POST.keys()),
                "files_keys": list(request.FILES.keys())
            }, status=400)
        
        print(f"✅ Archivo recibido: {imagen.name}")
        print(f"   Tamaño: {imagen.size} bytes")
        print(f"   Tipo: {imagen.content_type}")
        
        return JsonResponse({
            "ok": True,
            "message": "Archivo recibido correctamente",
            "file_info": {
                "name": imagen.name,
                "size": imagen.size,
                "content_type": imagen.content_type
            }
        }, status=200)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ============= ENDPOINT ALTERNATIVO CON BASE64 =============
@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def create_producto_base64(request):
    """
    POST /products/productos/create-base64
    Crea un nuevo producto con imagen en base64.
    
    Content-Type: application/json
    
    Body: {
        "nombre": "...",
        "descripcion": "...",
        "precio": 99.99,
        "stock": 10,
        "categoria_id": 1,
        "marca_id": 1,
        "garantia_id": 1,
        "imagen_base64": "data:image/jpeg;base64,/9j/4AAQ...",  // opcional
        "imagen_filename": "producto.jpg"  // opcional
    }
    """
    try:
        import base64
        from django.core.files.base import ContentFile
        
        payload = json.loads(request.body.decode() or "{}")
        nombre = payload.get("nombre")
        descripcion = payload.get("descripcion")
        precio = payload.get("precio")
        stock = payload.get("stock")
        categoria_id = payload.get("categoria_id")
        marca_id = payload.get("marca_id")
        garantia_id = payload.get("garantia_id")
        imagen_base64 = payload.get("imagen_base64")
        imagen_filename = payload.get("imagen_filename", "producto.jpg")
        
        # Convertir base64 a archivo
        imagen = None
        if imagen_base64:
            try:
                # Remover el prefijo data:image/...;base64, si existe
                if ',' in imagen_base64:
                    imagen_base64 = imagen_base64.split(',')[1]
                
                # Decodificar base64
                imagen_data = base64.b64decode(imagen_base64)
                imagen = ContentFile(imagen_data, name=imagen_filename)
                print(f"✅ Imagen base64 decodificada: {imagen_filename}, {len(imagen_data)} bytes")
            except Exception as e:
                print(f"❌ Error al decodificar base64: {e}")
                return JsonResponse({"ok": False, "error": f"Error al procesar imagen: {str(e)}"}, status=400)
        
        producto = producto_service.create_producto(
            nombre, descripcion, precio, stock, 
            categoria_id, marca_id, garantia_id, imagen
        )
        return JsonResponse({"ok": True, "producto": producto, "message": "Producto creado exitosamente"}, status=201)
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    except ValueError as e:
        return JsonResponse({"ok": False, "error": f"Error en formato de datos: {str(e)}"}, status=400)
    except Exception as e:
        print(f"Error al crear producto: {e}")
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
