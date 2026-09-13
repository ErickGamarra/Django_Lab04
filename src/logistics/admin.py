from django.contrib import admin
from .models import (
    Proveedor,
    Sucursal,
    Transportista,
    CategoriaInsumo,
    Material,
    FichaTecnicaMaterial,
    OrdenDespacho,
    DetalleDespacho,
)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'ruc', 'telefono', 'correo')
    search_fields = ('razon_social', 'ruc')


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'direccion', 'capacidad_almacen')
    list_filter = ('ciudad',)


@admin.register(Transportista)
class TransportistaAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'placa', 'tipo_vehiculo', 'activo')
    list_filter = ('activo', 'tipo_vehiculo')


@admin.register(CategoriaInsumo)
class CategoriaInsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)


class FichaTecnicaInline(admin.StackedInline):
    model = FichaTecnicaMaterial
    can_delete = False
    verbose_name = "Ficha Técnica Textil"
    verbose_name_plural = "Ficha Técnica Textil"


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'unidad_medida', 'precio_unitario', 'stock')
    list_filter = ('categoria',)
    search_fields = ('nombre',)
    inlines = [FichaTecnicaInline]


@admin.register(FichaTecnicaMaterial)
class FichaTecnicaMaterialAdmin(admin.ModelAdmin):
    list_display = ('material', 'composicion', 'densidad_gramaje', 'temperatura_lavado')
    search_fields = ('material__nombre', 'composicion')


class DetalleDespachoInline(admin.TabularInline):
    model = DetalleDespacho
    extra = 1


@admin.register(OrdenDespacho)
class OrdenDespachoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'sucursal_destino', 'transportista', 'estado', 'fecha_emision')
    list_filter = ('estado', 'sucursal_destino')
    search_fields = ('codigo', 'sucursal_destino__nombre')
    inlines = [DetalleDespachoInline]


@admin.register(DetalleDespacho)
class DetalleDespachoAdmin(admin.ModelAdmin):
    list_display = ('despacho', 'material', 'cantidad_despachada', 'costo_unitario_historico', 'lote_produccion', 'subtotal')
    list_filter = ('despacho__estado',)
    search_fields = ('despacho__codigo', 'material__nombre', 'lote_produccion')

