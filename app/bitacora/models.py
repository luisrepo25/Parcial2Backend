from django.db import models

# Create your models here.

# Modelo para registrar acciones en la bitácora
class Bitacora(models.Model):
    accion = models.CharField(max_length=255)
    usuario = models.CharField(max_length=100)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    detalles = models.TextField(blank=True, null=True)
    resultado = models.CharField(max_length=50, blank=True, null=True)


    class Meta:
        db_table = 'bitacora'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.fecha_hora} - {self.usuario} - {self.accion}"