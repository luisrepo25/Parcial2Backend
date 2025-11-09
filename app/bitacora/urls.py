"""
URLs para el módulo de bitácora
"""
from django.urls import path
from . import views

urlpatterns = [
    # Consulta de bitácora
    path('', views.obtener_bitacora, name='obtener_bitacora'),
]
