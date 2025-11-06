from django.contrib import admin
from .models import MetodoPago, NotaVenta, Detalle_Venta


class DetalleVentaInline(admin.TabularInline):
    """Inline para mostrar detalles de venta en la nota de venta"""
    model = Detalle_Venta
    extra = 0
    readonly_fields = ('subtotal', 'created_at')
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'estado', 'created_at')
    list_filter = ('estado', 'created_at')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(NotaVenta)
class NotaVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'estado', 'total', 'metodo_pago', 'created_at')
    list_filter = ('estado', 'metodo_pago', 'created_at')
    search_fields = ('usuario__correo', 'stripe_session_id', 'stripe_payment_intent')
    readonly_fields = ('created_at', 'updated_at', 'stripe_session_id', 'stripe_payment_intent')
    inlines = [DetalleVentaInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'metodo_pago', 'estado', 'total')
        }),
        ('Información de Stripe', {
            'fields': ('stripe_session_id', 'stripe_payment_intent'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Detalle_Venta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nota_venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('created_at',)
    search_fields = ('producto__nombre', 'nota_venta__id')
    readonly_fields = ('subtotal', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('nota_venta', 'producto')
