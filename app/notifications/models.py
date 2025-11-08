from django.db import models
from users.models import Usuario


# Create your models here.

class Notificacion(models.Model):
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_notificacion'
        ordering = ['-created_at']

    def __str__(self):
        return f"Notificación #{self.id} - {self.titulo}"
    
class Noti_Usuario(models.Model):
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name='notificaciones_usuario')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    leida = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications_notiusuario'
        ordering = ['-created_at']

    def __str__(self):
        return f"Noti_Usuario #{self.id} - Notificación #{self.notificacion.id} para Usuario #{self.usuario_id}"

