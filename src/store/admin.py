from django.contrib import admin
from .models import Prenda, DetallePrenda, ResenaPrenda, Pedido, DetallePedido


class DetallePrendaInline(admin.StackedInline):
    model = DetallePrenda
    can_delete = False
    verbose_name = "Ficha Complementaria (Detalle)"
    verbose_name_plural = "Ficha Complementaria (Detalles de la Prenda)"
    extra = 0


class ResenaPrendaInline(admin.TabularInline):
    model = ResenaPrenda
    extra = 1
    fields = ('cliente_nombre', 'calificacion', 'comentario', 'fecha')
    readonly_fields = ('fecha',)
    verbose_name = "Reseña / Opinión"
    verbose_name_plural = "Reseñas de Clientes (Relación 1 a N)"


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    fields = ('prenda', 'cantidad', 'precio_unitario')
    verbose_name = "Prenda del Pedido"
    verbose_name_plural = "Prendas Incluidas (Modelo Intermedio: DetallePedido)"


@admin.register(Prenda)
class PrendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'marca', 'tipo', 'categoria', 'talla', 'precio', 'stock', 'disponible', 'activo')
    list_filter = ('tipo', 'categoria', 'disponible', 'activo')
    search_fields = ('nombre', 'marca', 'descripcion')
    list_editable = ('precio', 'stock', 'disponible', 'activo')
    inlines = [DetallePrendaInline, ResenaPrendaInline]


@admin.register(DetallePrenda)
class DetallePrendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'prenda', 'composicion', 'pais_origen')
    search_fields = ('prenda__nombre', 'composicion', 'cuidados', 'pais_origen')


@admin.register(ResenaPrenda)
class ResenaPrendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'prenda', 'cliente_nombre', 'calificacion', 'fecha')
    list_filter = ('calificacion', 'fecha')
    search_fields = ('prenda__nombre', 'cliente_nombre', 'comentario')


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'cliente_nombre', 'cliente_email', 'estado', 'fecha_creacion', 'get_total')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('codigo', 'cliente_nombre', 'cliente_email')
    inlines = [DetallePedidoInline]

    @admin.display(description="Total (S/)")
    def get_total(self, obj):
        return f"S/ {obj.total():.2f}"


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'prenda', 'cantidad', 'precio_unitario', 'get_subtotal')
    list_filter = ('pedido__estado', 'fecha_agregado')
    search_fields = ('pedido__codigo', 'prenda__nombre', 'pedido__cliente_nombre')

    @admin.display(description="Subtotal (S/)")
    def get_subtotal(self, obj):
        return f"S/ {obj.subtotal():.2f}"



