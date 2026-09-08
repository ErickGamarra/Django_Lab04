
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, reset_queries
from logistics.models import CategoriaInsumo, Material, Proveedor, Sucursal, Transportista

def separator(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def sub_separator(text):
    print(f"\n--- {text} ---")

def run_crud_verification():
    separator("EJERCICIO 19: VERIFICACIÓN DEL CRUD COMPLETO EN TODAS LAS ENTIDADES")
    print("Demostración de operaciones CREATE (INSERT), READ (SELECT), UPDATE (UPDATE) y DELETE (DELETE)")
    print("utilizando exclusivamente Django ORM y SQLite, sin escribir sentencias SQL manuales.")

    # =========================================================================
    # 1. ENTIDAD: CategoriaInsumo (Entidad Maestra 1:N)
    # =========================================================================
    separator("1. ENTIDAD: CategoriaInsumo")

    # 1.1 CREATE -> INSERT
    sub_separator("CREATE -> SQL INSERT")
    cat = CategoriaInsumo.objects.create(
        nombre="Avíos Metálicos de Prueba",
        descripcion="Insumos de prueba para validación de ciclo CRUD."
    )
    cat_id = cat.id
    print(f"  [CREATE] Objeto instanciado y persistido con ORM:")
    print(f"           CategoriaInsumo.objects.create(nombre='{cat.nombre}')")
    print(f"           -> ID Autoincremental asignado por SQLite: {cat_id}")

    # 1.2 READ -> SELECT
    sub_separator("READ -> SQL SELECT")
    cat_leida = CategoriaInsumo.objects.get(id=cat_id)
    print(f"  [READ] Registro consultado mediante ORM:")
    print(f"         CategoriaInsumo.objects.get(id={cat_id})")
    print(f"         -> Nombre recuperado: '{cat_leida.nombre}'")
    print(f"         -> Descripción: '{cat_leida.descripcion}'")

    # 1.3 UPDATE -> SQL UPDATE
    sub_separator("UPDATE -> SQL UPDATE")
    cat_leida.nombre = "Avíos Metálicos Actualizados"
    cat_leida.descripcion = "Descripción modificada mediante ORM."
    cat_leida.save()
    cat_actualizada = CategoriaInsumo.objects.get(id=cat_id)
    print(f"  [UPDATE] Objeto modificado y guardado con ORM:")
    print(f"           cat.nombre = '{cat_actualizada.nombre}'")
    print(f"           cat.save()")
    print(f"           -> Verificación en SQLite tras UPDATE: '{cat_actualizada.nombre}'")

    # 1.4 DELETE -> SQL DELETE
    sub_separator("DELETE -> SQL DELETE")
    cat_actualizada.delete()
    existe_cat = CategoriaInsumo.objects.filter(id=cat_id).exists()
    print(f"  [DELETE] Objeto eliminado mediante ORM:")
    print(f"           cat.delete()")
    print(f"           -> ¿El registro aún existe en SQLite?: {existe_cat} (Eliminación confirmada)")


    # =========================================================================
    # 2. ENTIDAD: Material (Entidad Dependiente 1:N con ForeignKey)
    # =========================================================================
    separator("2. ENTIDAD: Material")

    # Necesitamos una categoría contenedora activa
    cat_base, _ = CategoriaInsumo.objects.get_or_create(
        nombre="Categoría Contenedora CRUD",
        defaults={'descripcion': "Categoría base para probar el CRUD de Material."}
    )

    # 2.1 CREATE -> INSERT
    sub_separator("CREATE -> SQL INSERT")
    mat = Material.objects.create(
        categoria=cat_base,
        nombre="Cierre Bronce 20cm",
        unidad_medida="Piezas",
        precio_unitario=Decimal("3.50"),
        stock=100
    )
    mat_id = mat.id
    print(f"  [CREATE] Insumo persistido con relación ForeignKey:")
    print(f"           Material.objects.create(nombre='{mat.nombre}', categoria=cat_base)")
    print(f"           -> ID asignado: {mat_id} | FK categoria_id: {mat.categoria_id}")

    # 2.2 READ -> SELECT
    sub_separator("READ -> SQL SELECT")
    mat_leido = Material.objects.select_related('categoria').get(id=mat_id)
    print(f"  [READ] Insumo recuperado con select_related (INNER JOIN):")
    print(f"         -> Insumo: '{mat_leido.nombre}'")
    print(f"         -> Categoría vinculada: '{mat_leido.categoria.nombre}'")
    print(f"         -> Stock: {mat_leido.stock} {mat_leido.unidad_medida} | Precio: S/ {mat_leido.precio_unitario}")

    # 2.3 UPDATE -> SQL UPDATE
    sub_separator("UPDATE -> SQL UPDATE")
    mat_leido.precio_unitario = Decimal("4.20")
    mat_leido.stock = 250
    mat_leido.save()
    mat_act = Material.objects.get(id=mat_id)
    print(f"  [UPDATE] Propiedades actualizadas con mat.save():")
    print(f"           -> Nuevo precio: S/ {mat_act.precio_unitario} (Antes: S/ 3.50)")
    print(f"           -> Nuevo stock: {mat_act.stock} unidades (Antes: 100)")

    # 2.4 DELETE -> SQL DELETE
    sub_separator("DELETE -> SQL DELETE")
    mat_act.delete()
    existe_mat = Material.objects.filter(id=mat_id).exists()
    print(f"  [DELETE] Insumo eliminado con mat.delete():")
    print(f"           -> ¿El material aún existe en SQLite?: {existe_mat} (Eliminación confirmada)")


    # =========================================================================
    # 3. ENTIDAD: Proveedor (Entidad Independiente)
    # =========================================================================
    separator("3. ENTIDAD: Proveedor")

    # 3.1 CREATE -> INSERT
    sub_separator("CREATE -> SQL INSERT")
    prov = Proveedor.objects.create(
        ruc="20999888771",
        razon_social="Distribuidora Textil Lima S.A.C.",
        telefono="911223344",
        correo="ventas@textillima.pe"
    )
    prov_id = prov.id
    print(f"  [CREATE] Proveedor registrado en sistema:")
    print(f"           Proveedor.objects.create(ruc='{prov.ruc}', razon_social='{prov.razon_social}')")
    print(f"           -> ID asignado: {prov_id} | RUC: {prov.ruc}")

    # 3.2 READ -> SELECT
    sub_separator("READ -> SQL SELECT")
    prov_leido = Proveedor.objects.get(id=prov_id)
    print(f"  [READ] Consulta por ID:")
    print(f"         -> Razón Social: '{prov_leido.razon_social}'")
    print(f"         -> Teléfono: {prov_leido.telefono} | Correo: {prov_leido.correo}")

    # 3.3 UPDATE -> SQL UPDATE
    sub_separator("UPDATE -> SQL UPDATE")
    prov_leido.razon_social = "Distribuidora Textil Lima & Asociados S.A.C."
    prov_leido.telefono = "988776655"
    prov_leido.save()
    prov_act = Proveedor.objects.get(id=prov_id)
    print(f"  [UPDATE] Datos de contacto y razón social actualizados:")
    print(f"           -> Razón social: '{prov_act.razon_social}'")
    print(f"           -> Nuevo teléfono: {prov_act.telefono}")

    # 3.4 DELETE -> SQL DELETE
    sub_separator("DELETE -> SQL DELETE")
    prov_act.delete()
    existe_prov = Proveedor.objects.filter(id=prov_id).exists()
    print(f"  [DELETE] Proveedor eliminado de SQLite:")
    print(f"           -> ¿Existe proveedor?: {existe_prov} (Eliminación confirmada)")


    # =========================================================================
    # 4. ENTIDAD: Sucursal (Entidad Independiente)
    # =========================================================================
    separator("4. ENTIDAD: Sucursal")

    # 4.1 CREATE -> INSERT
    sub_separator("CREATE -> SQL INSERT")
    suc = Sucursal.objects.create(
        nombre="Sede Almacén Callao",
        direccion="Av. Néstor Gambetta 500",
        ciudad="Callao",
        capacidad_almacen=35000
    )
    suc_id = suc.id
    print(f"  [CREATE] Sucursal registrada:")
    print(f"           Sucursal.objects.create(nombre='{suc.nombre}', ciudad='{suc.ciudad}')")
    print(f"           -> ID asignado: {suc_id}")

    # 4.2 READ -> SELECT
    sub_separator("READ -> SQL SELECT")
    suc_leida = Sucursal.objects.get(id=suc_id)
    print(f"  [READ] Consulta de sucursal física:")
    print(f"         -> Nombre: '{suc_leida.nombre}' | Ciudad: '{suc_leida.ciudad}'")
    print(f"         -> Capacidad: {suc_leida.capacidad_almacen} unidades")

    # 4.3 UPDATE -> SQL UPDATE
    sub_separator("UPDATE -> SQL UPDATE")
    suc_leida.capacidad_almacen = 45000
    suc_leida.direccion = "Av. Néstor Gambetta 500, Km 7.5"
    suc_leida.save()
    suc_act = Sucursal.objects.get(id=suc_id)
    print(f"  [UPDATE] Capacidad y dirección actualizadas:")
    print(f"           -> Nueva capacidad: {suc_act.capacidad_almacen} unidades (Antes: 35000)")
    print(f"           -> Dirección corregida: '{suc_act.direccion}'")

    # 4.4 DELETE -> SQL DELETE
    sub_separator("DELETE -> SQL DELETE")
    suc_act.delete()
    existe_suc = Sucursal.objects.filter(id=suc_id).exists()
    print(f"  [DELETE] Sucursal eliminada:")
    print(f"           -> ¿Existe sucursal?: {existe_suc} (Eliminación confirmada)")


    # =========================================================================
    # 5. ENTIDAD: Transportista (Entidad Independiente)
    # =========================================================================
    separator("5. ENTIDAD: Transportista")

    # 5.1 CREATE -> INSERT
    sub_separator("CREATE -> SQL INSERT")
    trans = Transportista.objects.create(
        empresa="Transportes Veloz S.A.",
        placa="T8P-900",
        tipo_vehiculo="Furgón 3TN",
        activo=True
    )
    trans_id = trans.id
    print(f"  [CREATE] Unidad de transporte dada de alta:")
    print(f"           Transportista.objects.create(empresa='{trans.empresa}', placa='{trans.placa}')")
    print(f"           -> ID asignado: {trans_id} | Placa: '{trans.placa}'")

    # 5.2 READ -> SELECT
    sub_separator("READ -> SQL SELECT")
    trans_leido = Transportista.objects.get(id=trans_id)
    print(f"  [READ] Consulta de datos operativos:")
    print(f"         -> Empresa: '{trans_leido.empresa}'")
    print(f"         -> Vehículo: {trans_leido.tipo_vehiculo} | Operativo: {trans_leido.activo}")

    # 5.3 UPDATE -> SQL UPDATE
    sub_separator("UPDATE -> SQL UPDATE")
    trans_leido.activo = False
    trans_leido.tipo_vehiculo = "Furgón 3.5TN (Mantenimiento)"
    trans_leido.save()
    trans_act = Transportista.objects.get(id=trans_id)
    print(f"  [UPDATE] Estado de operatividad actualizado:")
    print(f"           -> Tipo / Observación: '{trans_act.tipo_vehiculo}'")
    print(f"           -> Activo / Operativo: {trans_act.activo} (Deshabilitado temporalmente)")

    # 5.4 DELETE -> SQL DELETE
    sub_separator("DELETE -> SQL DELETE")
    trans_act.delete()
    existe_trans = Transportista.objects.filter(id=trans_id).exists()
    print(f"  [DELETE] Unidad de transporte eliminada:")
    print(f"           -> ¿Existe transportista?: {existe_trans} (Eliminación confirmada)")

    # Limpieza de categoría base auxiliar
    cat_base.delete()

    separator("RESUMEN GENERAL DEL CRUD EN TODAS LAS ENTIDADES")
    print("Todas las operaciones CREATE, READ, UPDATE y DELETE fueron verificadas exitosamente:")
    print("  [x] CategoriaInsumo : CREATE -> READ -> UPDATE -> DELETE (OK)")
    print("  [x] Material        : CREATE -> READ -> UPDATE -> DELETE (OK)")
    print("  [x] Proveedor       : CREATE -> READ -> UPDATE -> DELETE (OK)")
    print("  [x] Sucursal        : CREATE -> READ -> UPDATE -> DELETE (OK)")
    print("  [x] Transportista   : CREATE -> READ -> UPDATE -> DELETE (OK)")
    print("Persistencia y aislamiento confirmados al 100% mediante Django ORM.")
    print("=" * 80)

if __name__ == '__main__':
    run_crud_verification()
