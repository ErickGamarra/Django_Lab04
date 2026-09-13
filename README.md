# Laboratorio 04 — Modelado Avanzado de Relaciones, Optimización ORM y Migraciones

**Curso:** Desarrollo de Aplicaciones Empresariales  
**Institución:** Tecsup  
**Sección:** 4 - C24 - Sección CD  
**Docente:** Yunior Bestard Aroche  
**Integrantes del Equipo:**
1. **Erick Arturo Gamarra Mundaca**
2. **Jesús Enrique Rocha Bobadilla**  
**Proyecto:** **UrbanTrend** — Plataforma Textil Streetwear y Sistema Logístico Avanzado con Django ORM y SQLite  
**Repositorio GitHub:** [https://github.com/ErickGamarra/Django_Lab04](https://github.com/ErickGamarra/Django_Lab04)

---

## 🎯 1. Objetivo del Laboratorio 04 (Parte 2)

Ampliar la arquitectura persistente investigada en la Semana 3 para el módulo logístico de **UrbanTrend**, incorporando los tres tipos de relaciones fundamentales que ofrece Django ORM (**1:1**, **1:N** y **N:M con modelo intermedio `through`**) y cumpliendo rigurosamente los 9 criterios de evaluación del laboratorio:
* **Mantenimiento del dominio:** Misma problemática de insumos textiles y distribución a sucursales.
* **Integridad referencial protegida:** `on_delete=models.PROTECT` en la clasificación de catálogo para salvaguardar el inventario físico y contable.
* **Relación 1:1 con automatización:** Extensión técnica (`FichaTecnicaMaterial`) generada automáticamente mediante señales `post_save`.
* **Relación N:M con atributos propios:** Modelo intermedio `DetalleDespacho` con 4 campos transaccionales propios (`cantidad_despachada`, `costo_unitario_historico`, `lote_produccion`, `observaciones`).
* **Optimización ORM:** Resolución del cuello de botella de consultas $N+1$ mediante `select_related()` (uniones SQL JOIN) y `prefetch_related()` (consultas por lotes con cláusula `IN`).
* **CRUD funcional del modelo intermedio:** Capacidad operativa de crear, listar, editar y eliminar registros de la relación intermedia.

---

## 🏗️ 2. Modelo de Datos Ampliado (8 Entidades)

El modelo de datos creció de 5 a **8 entidades** completamente estructuradas en SQLite:

| # | Entidad | Tipo / Rol | Descripción de Negocio |
|---|---------|------------|------------------------|
| 1 | **`Proveedor`** | Independiente | Directorio homologado de socios comerciales (`ruc`, `razon_social`, `telefono`, `correo`). |
| 2 | **`Sucursal`** | Independiente | Puntos de venta y almacenes físicos receptores (`nombre`, `direccion`, `ciudad`, `capacidad_almacen`). |
| 3 | **`Transportista`** | Independiente | Flota de transporte logístico asignada a traslados (`empresa`, `placa`, `tipo_vehiculo`, `activo`). |
| 4 | **`CategoriaInsumo`** | Relacionada (1:N - Lado 1) | Familias maestras de materia prima textil (`nombre`, `descripcion`). |
| 5 | **`Material`** | Relacionada (1:N - Lado N) | Insumos de confección vinculados a categoría mediante `ForeignKey` protegida (`on_delete=models.PROTECT`). |
| 6 | **`FichaTecnicaMaterial`** | **NUEVA (Relación 1:1)** | Especificaciones de calidad e ingeniería textil (`composicion`, `densidad_gramaje`, `encogimiento`, `temperatura_lavado`, `cuidados`). |
| 7 | **`OrdenDespacho`** | **NUEVA (Cabecera N:M)** | Guía de traslado hacia una sucursal con transportista asignado (`codigo`, `estado`, `fecha_emision`, `observaciones`). |
| 8 | **`DetalleDespacho`** | **NUEVA (Modelo Intermedio N:M)** | Modelo intermedio `through` que congela la transacción del envío con atributos propios. |

---

## 📊 3. Diagrama Entidad-Relación (Relaciones 1:1, 1:N y N:M)

```text
┌───────────────────────────┐         ┌───────────────────────────┐
│      CategoriaInsumo      │         │         Proveedor         │
│ ───────────────────────── │         │ ───────────────────────── │
│  PK  id                   │         │  PK  id                   │
│      nombre (UQ)          │         │      ruc (UQ, 11 dígitos) │
│      descripcion          │         │      razon_social         │
└─────────────┬─────────────┘         │      telefono             │
              │ 1                     │      correo               │
              │ (on_delete=PROTECT)   └───────────────────────────┘
              │ 
              │ N
┌─────────────▼─────────────┐         ┌───────────────────────────┐
│         Material          │ 1     1 │   FichaTecnicaMaterial    │
│ ───────────────────────── │─────────│ ───────────────────────── │
│  PK  id                   │(1:1)    │  PK  id                   │
│  FK  categoria_id         │         │  FK  material_id (1:1 UQ) │
│      nombre               │         │      composicion          │
│      unidad_medida        │         │      densidad_gramaje     │
│      precio_unitario      │         │      tolerancia_encogim.  │
│      stock                │         │      temperatura_lavado   │
└─────────────┬─────────────┘         │      cuidados_adicionales │
              │                       │      fecha_emision        │
              │                       └───────────────────────────┘
              │ N
┌─────────────▼─────────────┐
│      DetalleDespacho      │ ◄── MODELO INTERMEDIO (through)
│ ───────────────────────── │     Atributos propios de la relación:
│  PK  id                   │     - cantidad_despachada (int > 0)
│  FK  despacho_id ─────────┐     - costo_unitario_historico (S/)
│  FK  material_id          │     - lote_produccion (trazabilidad)
│      cantidad_despachada  │     - observaciones
│      costo_unitario_hist. │
│      lote_produccion      │
│      observaciones        │
└───────────────────────────┘
              ▲ N
              │
              │ 1
┌─────────────┴─────────────┐         ┌───────────────────────────┐
│       OrdenDespacho       │         │         Sucursal          │
│ ───────────────────────── │ N     1 │ ───────────────────────── │
│  PK  id                   │─────────│  PK  id                   │
│      codigo (UQ)          │         │      nombre               │
│  FK  sucursal_destino_id ─┘         │      direccion            │
│  FK  transportista_id ────┐         │      ciudad               │
│      fecha_emision        │         │      capacidad_almacen    │
│      estado               │         └───────────────────────────┘
│      observaciones        │         ┌───────────────────────────┐
│      materiales (M2M)     │ N     1 │       Transportista       │
└───────────────────────────┘─────────│ ───────────────────────── │
                                      │  PK  id                   │
                                      │      empresa              │
                                      │      placa (UQ)           │
                                      │      tipo_vehiculo        │
                                      │      activo               │
                                      └───────────────────────────┘
```

---

## ⚡ 4. Optimización ORM y Mitigación del Problema $N+1$

El problema de consultas $N+1$ se genera cuando una vista consulta un registro maestro y luego dispara una consulta SQL individual por cada fila hija al renderizar en el template. En **Laboratorio 04** se implementaron dos técnicas avanzadas del ORM:

### 1. `select_related()` (Uniones SQL JOIN en BD)
Utilizado para relaciones directas `ForeignKey` y `OneToOneField`. Ejecuta un solo `INNER JOIN` o `LEFT OUTER JOIN` en el motor SQLite:
```python
# Consulta optimizada en logistics/views.py (material_list):
materiales = Material.objects.select_related('categoria', 'ficha_tecnica').all()
```
* **Medición empírica:** **1 sola consulta SQL** ejecutada para recuperar simultáneamente los 8 materiales, sus categorías y sus fichas técnicas de laboratorio. (Sin optimización: $1 + 8 + 8 = 17$ consultas).

### 2. `prefetch_related()` (Consultas por lotes con cláusula `IN`)
Utilizado para relaciones de conjunto (1:N inversas y N:M con tablas intermedias):
```python
# Consulta optimizada en logistics/views.py (orden_despacho_list):
despachos = OrdenDespacho.objects.select_related(
    'sucursal_destino', 'transportista'
).prefetch_related(
    'detalles__material'
).all()
```
* **Medición empírica:** Exactamente **3 consultas SQL** por lotes para traer la orden completa, sus destinos, transportistas y el desglose de insumos despachados con sus costos históricos.

---

## 🛠️ 5. CRUD del Modelo Intermedio (`DetalleDespacho`)

Cumpliendo el **Criterio 9**, el modelo intermedio dispone de interfaz web completa para gestionar sus atributos:

* **CREATE (`/logistics/detalles-despacho/nuevo/`):** Permite incorporar insumos textiles a una orden de despacho congelando su precio y lote.
* **READ (`/logistics/detalles-despacho/`):** Listado consolidado de despachos intermedios con cálculo de subtotales.
* **UPDATE (`/logistics/detalles-despacho/editar/<id>/`):** Rectificación de cantidades o partidas de tela.
* **DELETE (`/logistics/detalles-despacho/eliminar/<id>/`):** Desvinculación segura con método HTTP `POST`.

---

## 🚀 6. Instalación y Ejecución Local

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/ErickGamarra/Django_Lab04.git
   cd Django_Lab04
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Aplicar migraciones sobre SQLite:**
   ```bash
   cd src
   python manage.py migrate
   python manage.py showmigrations logistics
   ```

5. **Poblar datos iniciales de prueba (Seed):**
   ```bash
   python seed_logistics.py
   ```

6. **Iniciar el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```
   * **Dashboard Logístico:** [http://127.0.0.1:8000/logistics/](http://127.0.0.1:8000/logistics/)
   * **Catálogo de Tienda (Parte 1):** [http://127.0.0.1:8000/store/](http://127.0.0.1:8000/store/)
   * **Panel Administrativo:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
