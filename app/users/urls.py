
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.hello),
    path('register', views.register_cliente),
    path('auth', views.login),
    path('', views.get_users),
    path('register_admin', views.register_admin),
]


