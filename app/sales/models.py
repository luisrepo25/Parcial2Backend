from django.db import models
from users.models import Usuario
from products.models import Producto

# Create your models here.

class MetodoPago(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)  # Indica si el método de pago está activo

    def __str__(self):
        return self.nombre
    

class NotaVenta(models.Model):
    estado = models.BooleanField(default=True)  
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT, related_name='notas_venta')
    total = models.DecimalField(max_digits=10, decimal_places=2)    
    # Relacion con usuario
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='notas_venta')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NotaVenta {self.id}"

class Detalle_Venta(models.Model):
    nota_venta = models.ForeignKey(NotaVenta, on_delete=models.CASCADE, related_name='detalles_venta')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_venta')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Detalle_Venta {self.id} de NotaVenta {self.nota_venta.id}"

