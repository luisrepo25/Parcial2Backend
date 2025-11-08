from django.urls import path
from . import views

urlpatterns = [
    # Registro de tokens FCM
    path('register-token/', views.registrar_token_fcm, name='registrar_token_fcm'),
    path('remove-token/', views.eliminar_token_fcm, name='eliminar_token_fcm'),
    
    # Pruebas
    path('test/', views.enviar_notificacion_test, name='enviar_notificacion_test'),
    
    # Temas
    path('subscribe-topic/', views.suscribir_tema, name='suscribir_tema'),
    
    # Envío de notificaciones (uso real)
    path('send/', views.enviar_notificacion_usuario, name='enviar_notificacion_usuario'),
    path('send-all/', views.enviar_notificacion_masiva, name='enviar_notificacion_masiva'),
    path('send-topic/', views.enviar_notificacion_por_tema, name='enviar_notificacion_por_tema'),
]
