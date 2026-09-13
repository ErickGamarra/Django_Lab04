import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from logistics.models import Proveedor, Sucursal, Transportista, CategoriaInsumo, Material

def seed():
    print("Iniciando sembrado de datos para app Logistics...")

    # 1. Categorías de Insumos (1:N)
    cat_telas, _ = CategoriaInsumo.objects.get_or_create(
        nombre="Telas y Tejidos",
        defaults={'descripcion': "Telas de punto, algodón pima, franela y rib para confección streetwear."}
    )
    cat_avios, _ = CategoriaInsumo.objects.get_or_create(
        nombre="Avíos y Fornituras",
        defaults={'descripcion': "Cierres metálicos, botones a presión, ojalillos y cordones."}
    )
    cat_hilos, _ = CategoriaInsumo.objects.get_or_create(
        nombre="Hilados y Conos",
        defaults={'descripcion': "Hilos de coser de poliéster y algodón para remalladora y recubridora."}
    )
    cat_empaque, _ = CategoriaInsumo.objects.get_or_create(
        nombre="Empaque y Etiquetas",
        defaults={'descripcion': "Bolsas biodegradables con marca, etiquetas tejidas y hangtags."}
    )
    print(f"Categorías registradas: {CategoriaInsumo.objects.count()}")

    # 2. Materiales (1:N)
    materiales_data = [
        ("Tela Algodón Pima 50/1 Negro", cat_telas, "Metros", Decimal("34.50"), 450),
        ("Tela Franela Reactiva Oversize Crema", cat_telas, "Metros", Decimal("28.00"), 320),
        ("Tela Rib 2x1 Spandex Negro", cat_telas, "Metros", Decimal("22.50"), 180),
        ("Cierre Metálico N° 5 Niquelado 60cm", cat_avios, "Piezas", Decimal("3.80"), 1200),
        ("Cordón Tubular Algodón con Puntera", cat_avios, "Metros", Decimal("1.20"), 850),
        ("Cono Hilo Poliéster 40/2 Negro", cat_hilos, "Conos", Decimal("8.50"), 160),
        ("Cono Hilo Poliéster 40/2 Blanco", cat_hilos, "Conos", Decimal("8.50"), 140),
        ("Bolsa Biodegradable UrbanTrend 40x50", cat_empaque, "Millares", Decimal("110.00"), 15),
    ]

    for nombre, cat, unidad, precio, stock in materiales_data:
        Material.objects.get_or_create(
            nombre=nombre,
            categoria=cat,
            defaults={
                'unidad_medida': unidad,
                'precio_unitario': precio,
                'stock': stock
            }
        )
    print(f"Materiales registrados: {Material.objects.count()}")

    # 3. Proveedores (Independiente)
    proveedores_data = [
        ("20601234567", "Textiles del Sur S.A.C.", "987654321", "contacto@textilesdelsur.com"),
        ("20512345678", "Hilanderías Peruanas E.I.R.L.", "976543210", "ventas@hilanderiasperu.com"),
        ("20498765432", "Avíos & Cierres Industriales S.A.", "954321098", "operaciones@aviosindustriales.pe"),
    ]

    for ruc, razon, tel, correo in proveedores_data:
        Proveedor.objects.get_or_create(
            ruc=ruc,
            defaults={
                'razon_social': razon,
                'telefono': tel,
                'correo': correo
            }
        )
    print(f"Proveedores registrados: {Proveedor.objects.count()}")

    # 4. Sucursales (Independiente)
    sucursales_data = [
        ("Almacén Central Lurín", "Av. Industrial 450, Lurín", "Lima", 50000),
        ("Tienda Flagship Miraflores", "Av. Larco 789", "Lima", 8000),
        ("Punto de Venta San Isidro", "Av. Conquistadores 340", "Lima", 5000),
    ]

    for nom, dir, ciudad, cap in sucursales_data:
        Sucursal.objects.get_or_create(
            nombre=nom,
            defaults={
                'direccion': dir,
                'ciudad': ciudad,
                'capacidad_almacen': cap
            }
        )
    print(f"Sucursales registradas: {Sucursal.objects.count()}")

    # 5. Transportistas (Independiente)
    transportistas_data = [
        ("Logística Express SAC", "B8F-912", "Camión 5TN", True),
        ("TransCargo Perú", "A1X-430", "Furgón 2TN", True),
        ("Rápido Urbano", "C9Z-501", "Moto Carga", True),
    ]

    for emp, placa, tipo, act in transportistas_data:
        Transportista.objects.get_or_create(
            placa=placa,
            defaults={
                'empresa': emp,
                'tipo_vehiculo': tipo,
                'activo': act
            }
        )
    print(f"Transportistas registrados: {Transportista.objects.count()}")

    # 6. Órdenes de Despacho y Detalles (N:M con modelo intermedio)
    from logistics.models import OrdenDespacho, DetalleDespacho, FichaTecnicaMaterial

    sucursal_miraflores = Sucursal.objects.filter(nombre__icontains="Miraflores").first()
    transportista_camion = Transportista.objects.filter(tipo_vehiculo__icontains="Camión").first()

    if sucursal_miraflores and transportista_camion:
        despacho1, _ = OrdenDespacho.objects.get_or_create(
            codigo="DSP-2026-001",
            defaults={
                'sucursal_destino': sucursal_miraflores,
                'transportista': transportista_camion,
                'estado': 'En Tránsito',
                'observaciones': 'Envío prioritario para reposición de inventario de temporada otoño/invierno.'
            }
        )

        mat_pima = Material.objects.filter(nombre__icontains="Pima").first()
        mat_rib = Material.objects.filter(nombre__icontains="Rib").first()

        if mat_pima:
            DetalleDespacho.objects.get_or_create(
                despacho=despacho1,
                material=mat_pima,
                defaults={
                    'cantidad_despachada': 120,
                    'costo_unitario_historico': Decimal("34.50"),
                    'lote_produccion': 'LOTE-2026-TX01',
                    'observaciones': 'Rollos inspeccionados con 100% de conformidad.'
                }
            )

        if mat_rib:
            DetalleDespacho.objects.get_or_create(
                despacho=despacho1,
                material=mat_rib,
                defaults={
                    'cantidad_despachada': 60,
                    'costo_unitario_historico': Decimal("22.50"),
                    'lote_produccion': 'LOTE-2026-TX02',
                    'observaciones': 'Entrega con precinto de seguridad intacto.'
                }
            )

        print(f"Órdenes de Despacho registradas: {OrdenDespacho.objects.count()}")
        print(f"Detalles de Despacho registrados: {DetalleDespacho.objects.count()}")

    print("¡Sembrado de datos finalizado con éxito!")

if __name__ == '__main__':
    seed()

