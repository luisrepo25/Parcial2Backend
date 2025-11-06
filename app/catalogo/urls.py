from django.urls import path
from . import views

urlpatterns = [
    # Productos
    path('productos/', views.get_productos, name='catalogo-productos'),
    path('productos/<int:id>/', views.get_producto, name='catalogo-producto-detalle'),
    path('productos/buscar/', views.buscar_productos, name='catalogo-buscar'),
    path('productos/destacados/', views.get_productos_destacados, name='catalogo-destacados'),
    path('productos/nuevos/', views.get_productos_nuevos, name='catalogo-nuevos'),
    path('productos/mas-vendidos/', views.get_productos_mas_vendidos, name='catalogo-mas-vendidos'),
    
    # Categorías
    path('categorias/', views.get_categorias, name='catalogo-categorias'),
    path('categorias/<int:id>/productos/', views.get_productos_por_categoria, name='catalogo-categoria-productos'),
    
    # Marcas
    path('marcas/', views.get_marcas, name='catalogo-marcas'),
    path('marcas/<int:id>/productos/', views.get_productos_por_marca, name='catalogo-marca-productos'),
]
