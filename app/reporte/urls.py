"""
URLs para el módulo de reportes dinámicos
"""
from django.urls import path
from . import views

urlpatterns = [
    # Endpoint principal para generar reportes
    path('generar', views.generar_reporte_dinamico, name='generar_reporte'),
    
    # Endpoint para obtener ejemplos de prompts
    path('ejemplos', views.ejemplos_prompts, name='ejemplos_prompts'),
]