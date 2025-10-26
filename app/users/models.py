from django.db import models

class Usuario(models.Model):
    correo = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombres} <{self.correo}>"

class Cliente(models.Model):
    # Usa OneToOneField como PK y personaliza el nombre de columna en la BD
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id'   # aquí defines el nombre de la columna en la tabla users_cliente
    )
    apellidoMaterno = models.CharField(max_length=100)
    apellidoPaterno = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    ci = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Cliente: {self.nombres} {self.apellidoPaterno} {self.apellidoMaterno}"

# Administrador también hereda de Usuario
class Administrador(models.Model):
    # campos extra si se necesitan
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id'   # aquí defines el nombre de la columna en la tabla users_cliente
    )
    nombre = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return f"Administrador: {self.nombre} <{self.correo}>"