"""
URLs para el módulo de ventas
"""
from django.urls import path
from . import views

urlpatterns = [
    # Checkout con Stripe
    path('checkout/create/', views.crear_checkout, name='crear_checkout'),
    path('checkout/verify/<str:session_id>/', views.verificar_session, name='verificar_session'),
    
    # Payment Intent para apps móviles (Flutter, React Native)
    path('create-payment/', views.crear_payment_intent, name='crear_payment_intent'),
    
    # Webhook de Stripe (NO requiere autenticación)
    path('webhook/stripe/', views.webhook_stripe, name='webhook_stripe'),
    
    # Consulta de compras del usuario
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('mis-compras/<int:venta_id>/', views.detalle_compra, name='detalle_compra'),
    
    # Reembolsos
    path('reembolso/<int:venta_id>/', views.solicitar_reembolso, name='solicitar_reembolso'),
]
