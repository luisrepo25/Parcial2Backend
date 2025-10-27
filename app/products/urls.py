
# urlpatterns
from django.urls import path
from .views import categoria, marca, garantia, producto

urlpatterns = [
    # Categorías
    path('categorias', categoria.get_categorias, name='get_categorias'),           
    path('categorias/create', categoria.create_categoria, name='create_categoria'), 
    path('categorias/<int:id>', categoria.get_categoria, name='get_categoria'),    
    path('categorias/<int:id>/update', categoria.update_categoria, name='update_categoria'),
    path('categorias/<int:id>/delete', categoria.delete_categoria, name='delete_categoria'),
    
    # Marcas
    path('marcas', marca.get_marcas, name='get_marcas'),                     
    path('marcas/create', marca.create_marca, name='create_marca'),            
    path('marcas/<int:id>', marca.get_marca, name='get_marca'),                
    path('marcas/<int:id>/update', marca.update_marca, name='update_marca'),   
    path('marcas/<int:id>/delete', marca.delete_marca, name='delete_marca'),  
    
    # Garantías
    path('garantias', garantia.get_garantias, name='get_garantias'),                  
    path('garantias/create', garantia.create_garantia, name='create_garantia'),        
    path('garantias/<int:id>', garantia.get_garantia, name='get_garantia'),             
    path('garantias/<int:id>/update', garantia.update_garantia, name='update_garantia'),
    path('garantias/<int:id>/delete', garantia.delete_garantia, name='delete_garantia'),
    
    # Productos
    path('productos', producto.get_productos, name='get_productos'),                    
    path('productos/create', producto.create_producto, name='create_producto'),
    path('productos/<int:id>', producto.get_producto, name='get_producto'),             
    path('productos/<int:id>/update', producto.update_producto, name='update_producto'),
    path('productos/<int:id>/delete', producto.delete_producto, name='delete_producto'),
]