
from django.urls import path
from . import views

urlpatterns = [
    # ============= AUTENTICACIÓN =============
    path('auth', views.login, name='auth'),
    
    # ============= USUARIOS =============
    path('', views.get_users, name='get_users'),  
    path('<int:id>/', views.get_user, name='get_user'), 
    path('create/', views.create_user, name='create_user'),  
    path('<int:id>/update/', views.update_user, name='update_user'),  
    path('<int:id>/delete/', views.delete_user, name='delete_user'),  
    
    # ============= CLIENTES =============
    path('clientes/', views.get_clientes, name='get_clientes'),  
    path('clientes/<int:id>/', views.get_cliente, name='get_cliente'), 
    path('clientes/register/', views.register_cliente, name='register_cliente'), 
    path('clientes/<int:id>/update/', views.update_cliente, name='update_cliente'), 
    path('clientes/<int:id>/delete/', views.delete_cliente, name='delete_cliente'),  
    
    # ============= ADMINISTRADORES =============
    path('admins/', views.get_admins, name='get_admins'), 
    path('admins/<int:id>/', views.get_admin, name='get_admin'),  
    path('admins/register/', views.register_admin, name='register_admin'), 
    path('admins/<int:id>/update/', views.update_admin, name='update_admin'), 
    path('admins/<int:id>/delete/', views.delete_admin, name='delete_admin'),
]


