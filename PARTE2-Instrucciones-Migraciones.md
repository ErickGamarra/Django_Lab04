##Contexto

En el laboratorio anterior se logró la persistencia básica de la entidad Prenda en SQLite. Sin embargo, un catálogo comercial real requiere modelar relaciones complejas: especificaciones técnicas textiles de confección (1:1), valoraciones y comentarios de compradores (1:N) y órdenes de compra con congelamiento de precios históricos (N:M).

El problema técnico crítico que surge al trabajar con entidades relacionadas en un ORM es el problema de consultas N+1: cuando el sistema ejecuta una consulta inicial para obtener un listado de N registros y, al iterar sobre ellos en el template, dispara una consulta adicional por cada registro para recuperar su entidad vinculada (N+1 llamadas I/O).

En este laboratorio (Laboratorio 04) resolvemos esta problemática estructurando:

    Modelado relacional completo: 1:1 (DetallePrenda), 1:N (ResenaPrenda) y N:M con modelo intermedio (Pedido ↔ DetallePedido ↔ Prenda).

    Automatización de integridad mediante Señales: creación automática de la ficha técnica al registrar una prenda.

    Optimización de consultas en Views: uso estricto de select_related (uniones JOIN en BD) y prefetch_related (consultas por lotes con IN).

    Recorrido de relaciones en Templates: acceso directo, inverso y sobre atributos propios del modelo intermedio.

    Auditoría y verificación empírica: medición en tiempo real de sentencias SQL ejecutadas frente a los valores esperados.

Sigue los pasos en orden. No avances al siguiente ejercicio sin terminar y verificar el anterior.

##Ejercicio 1 — Modelar las relaciones avanzadas y señales

Edita store/models.py para agregar las tres relaciones sobre la entidad Prenda y la señal post_save para la creación automática de la ficha técnica:

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# ============================================================
# Entidad Base: Prenda
# ============================================================
class Prenda(models.Model):
    nombre = models.CharField(max_length=120)
    marca = models.CharField(max_length=80)
    tipo = models.CharField(max_length=20)
    categoria = models.CharField(max_length=40)
    talla = models.CharField(max_length=10)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    disponible = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.talla})"


# ============================================================
# Relación 1:1 — Ficha Técnica Textil (DetallePrenda)
# ============================================================
class DetallePrenda(models.Model):
    prenda = models.OneToOneField(
        Prenda, 
        on_delete=models.CASCADE, 
        related_name='detalle'
    )
    composicion = models.CharField(max_length=150, default='100% Algodón Peruano')
    cuidados = models.CharField(max_length=200, default='Lavar con agua fría')
    pais_origen = models.CharField(max_length=50, default='Perú')
    guia_medidas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ficha Técnica - {self.prenda.nombre}"


# ============================================================
# Relación 1:N — Opiniones de Clientes (ResenaPrenda)
# ============================================================
class ResenaPrenda(models.Model):
    prenda = models.ForeignKey(
        Prenda, 
        on_delete=models.CASCADE, 
        related_name='resenas'
    )
    cliente_nombre = models.CharField(max_length=100)
    calificacion = models.PositiveSmallIntegerField(default=5)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.cliente_nombre} - {self.prenda.nombre} ({self.calificacion}★)"


# ============================================================
# Relación N:M con Modelo Intermedio — Pedidos y Detalles
# ============================================================
class Pedido(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Enviado', 'Enviado'),
        ('Cancelado', 'Cancelado'),
    ]
    codigo = models.CharField(max_length=20, unique=True)
    cliente_nombre = models.CharField(max_length=120)
    cliente_email = models.EmailField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    prendas = models.ManyToManyField(
        Prenda, 
        through='DetallePedido', 
        related_name='pedidos'
    )

    def __str__(self):
        return f"Pedido {self.codigo} - {self.cliente_nombre}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.detalles.all())


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        related_name='detalles'
    )
    prenda = models.ForeignKey(
        Prenda, 
        on_delete=models.CASCADE, 
        related_name='detalles_pedido'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.prenda.nombre} en {self.pedido.codigo}"


# ============================================================
# Automatización por Señales (Signals)
# ============================================================
@receiver(post_save, sender=Prenda)
def asegurar_detalle_prenda(sender, instance, created, **kwargs):
    """Crea automáticamente la ficha técnica al persistir una nueva Prenda."""
    if created:
        DetallePrenda.objects.get_or_create(
            prenda=instance,
            defaults={
                'composicion': '100% Algodón Peruano 24/1',
                'cuidados': 'Lavar con agua fría, secar a la sombra',
                'pais_origen': 'Perú'
            }
        )

Ejercicio 2 — Crear la estructura persistente de datos

Con el entorno virtual activado, ejecuta en tu terminal:
Bash

python manage.py makemigrations store
python manage.py migrate
python manage.py showmigrations store

Toma captura de pantalla de la salida de los comandos. Confirma que se crearon las siguientes cuatro tablas en db.sqlite3:

    store_detalleprenda

    store_resenaprenda

    store_pedido

    store_detallepedido

Comando opcional para confirmar visualmente el esquema de la tabla intermedia:
Bash

python manage.py dbshell
.schema store_detallepedido
.quit

Ejercicio 3 — Implementar consultas optimizadas en Views

Edita store/views.py para implementar las dos vistas de auditoría técnica, utilizando reset_queries() y connection.queries para contabilizar las sentencias SQL reales ejecutadas contra la base de datos:
Python

from django.shortcuts import render, get_object_or_404
from django.db import connection, reset_queries
from .models import Prenda, Pedido

def prenda_detail_list(request):
    """Demostración de select_related (1:1): Resuelve en 1 sola consulta SQL con JOIN."""
    reset_queries()

    prendas = Prenda.objects.filter(activo=True).select_related('detalle')
    total_prendas = list(prendas)  # Forzar evaluación inmediata del QuerySet

    total_queries = len(connection.queries)

    return render(request, 'store/prenda_detail_list.html', {
        'titulo': 'Catálogo con Ficha Técnica (select_related)',
        'prendas': total_prendas,
        'total_queries': total_queries,
    })


def pedido_list(request):
    """Demostración de prefetch_related (N:M): Resuelve en 3 consultas SQL fijas."""
    reset_queries()

    pedidos = Pedido.objects.all().prefetch_related('detalles__prenda')
    total_pedidos = list(pedidos)  # Forzar evaluación inmediata del QuerySet

    total_queries = len(connection.queries)

    return render(request, 'store/pedido_list.html', {
        'titulo': 'Listado de Pedidos y Detalles (prefetch_related)',
        'pedidos': total_pedidos,
        'total_queries': total_queries,
    })

Registra las nuevas rutas en store/urls.py:
Python

from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.prenda_list, name='list'),
    path('<int:pk>/', views.prenda_detail, name='detail'),
    path('details/', views.prenda_detail_list, name='details'),
    path('orders/', views.pedido_list, name='orders'),
]

Ejercicio 4 — Implementar el recorrido de relaciones en Templates
1. Acceso Directo 1:1 (templates/store/prenda_detail_list.html)

El template accede a los datos de la ficha técnica directamente a través del atributo prenda.detalle.*:
Django

{% for prenda in prendas %}
<tr>
    <td>{{ prenda.nombre }}</td>
    <td>{{ prenda.marca }}</td>
    <td>S/ {{ prenda.precio|floatformat:2 }}</td>
    <!-- Acceso Directo 1:1 -->
    <td>{{ prenda.detalle.composicion|default:"Sin ficha" }}</td>
    <td>{{ prenda.detalle.cuidados|default:"Sin especificación" }}</td>
    <td>{{ prenda.detalle.pais_origen|default:"No definido" }}</td>
</tr>
{% endfor %}


2. Acceso Inverso 1:N (templates/store/prenda_detail.html)

El template recorre las opiniones de clientes usando el descriptor inverso administrado por el ORM (prenda.resenas.all):
Django

<!-- Acceso Inverso 1:N mediante related_name -->
<div class="list-group">
    {% for r in prenda.resenas.all %}
        <div class="list-group-item">
            <strong>{{ r.cliente_nombre }}</strong> ({{ r.calificacion }}/5★)
            <p>{{ r.comentario }}</p>
        </div>
    {% empty %}
        <p class="text-muted">Esta prenda aún no tiene opiniones registradas.</p>
    {% endfor %}
</div>

3. Recorrido del Modelo Intermedio N:M (templates/store/pedido_list.html)

El template itera sobre la relación intermedia pedido.detalles.all, accediendo tanto a los atributos propios de la compra como a los atributos de la prenda vinculada:
Django

{% for pedido in pedidos %}
<div class="card mb-3">
    <div class="card-header">
        <strong>Pedido {{ pedido.codigo }}</strong> — {{ pedido.cliente_nombre }}
    </div>
    <div class="card-body">
        <table class="table">
            <thead>
                <tr>
                    <th>Artículo</th>
                    <th>Talla</th>
                    <th>Cantidad</th>
                    <th>Precio Unit.</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {% for item in pedido.detalles.all %}
                <tr>
                    <!-- Acceso a la entidad final vinculada -->
                    <td>{{ item.prenda.nombre }}</td>
                    <td>{{ item.prenda.talla }}</td>
                    <!-- Acceso a los atributos propios del modelo intermedio -->
                    <td>{{ item.cantidad }}</td>
                    <td>S/ {{ item.precio_unitario|floatformat:2 }}</td>
                    <td>S/ {{ item.subtotal|floatformat:2 }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="text-end fw-bold">Total: S/ {{ pedido.total|floatformat:2 }}</div>
    </div>
</div>
{% endfor %}

Ejercicio 5 — Carga de datos y verificación empírica

Antes de validar en el navegador, ejecuta en tu terminal los siguientes comandos para poblar las especificaciones técnicas y los pedidos de prueba:
Bash

# 1. Poblar / Actualizar fichas técnicas para todas las prendas existentes
python manage.py shell -c "from store.models import Prenda, DetallePrenda; [DetallePrenda.objects.update_or_create(prenda=p, defaults={'composicion': '100% Algodón Peruano 24/1', 'cuidados': 'Lavar con agua fría, secar a la sombra', 'pais_origen': 'Perú'}) for p in Prenda.objects.filter(activo=True)]; print('Fichas técnicas vinculadas.')"

# 2. Poblar pedidos de prueba con detalles asociados
python manage.py shell -c "from store.models import Prenda, Pedido, DetallePedido; p1 = Prenda.objects.filter(activo=True).first(); p2 = Prenda.objects.filter(activo=True).last(); ped1, _ = Pedido.objects.get_or_create(codigo='PED-001', defaults={'cliente_nombre': 'Carlos Mendoza', 'cliente_email': 'carlos@example.com', 'estado': 'Pagado'}); DetallePedido.objects.get_or_create(pedido=ped1, prenda=p1, defaults={'cantidad': 2, 'precio_unitario': p1.precio}); DetallePedido.objects.get_or_create(pedido=ped1, prenda=p2, defaults={'cantidad': 1, 'precio_unitario': p2.precio}); ped2, _ = Pedido.objects.get_or_create(codigo='PED-002', defaults={'cliente_nombre': 'Valeria Rios', 'cliente_email': 'valeria@example.com', 'estado': 'Pendiente'}); DetallePedido.objects.get_or_create(pedido=ped2, prenda=p2, defaults={'cantidad': 3, 'precio_unitario': p2.precio}); print('Pedidos creados con éxito.')"

Prueba y verificación visual:

    Ingresa a [http://127.0.0.1:8000/ropa/details/](http://127.0.0.1:8000/ropa/details/). Confirma que las 10 prendas muestran su composición textil y que el indicador marca Consultas SQL: 1 (Esperado: 1).
Ejercicio 2 — Crear la estructura persistente de datos

Con el entorno virtual activado, ejecuta en tu terminal:
Bash

python manage.py makemigrations store
python manage.py migrate
python manage.py showmigrations store

Toma captura de pantalla de la salida de los comandos. Confirma que se crearon las siguientes cuatro tablas en db.sqlite3:

    store_detalleprenda

    store_resenaprenda

    store_pedido

    store_detallepedido

Comando opcional para confirmar visualmente el esquema de la tabla intermedia:
Bash

python manage.py dbshell
.schema store_detallepedido
.quit

Ejercicio 3 — Implementar consultas optimizadas en Views

Edita store/views.py para implementar las dos vistas de auditoría técnica, utilizando reset_queries() y connection.queries para contabilizar las sentencias SQL reales ejecutadas contra la base de datos:
Python

from django.shortcuts import render, get_object_or_404
from django.db import connection, reset_queries
from .models import Prenda, Pedido

def prenda_detail_list(request):
    """Demostración de select_related (1:1): Resuelve en 1 sola consulta SQL con JOIN."""
    reset_queries()

    prendas = Prenda.objects.filter(activo=True).select_related('detalle')
    total_prendas = list(prendas)  # Forzar evaluación inmediata del QuerySet

    total_queries = len(connection.queries)

    return render(request, 'store/prenda_detail_list.html', {
        'titulo': 'Catálogo con Ficha Técnica (select_related)',
        'prendas': total_prendas,
        'total_queries': total_queries,
    })


def pedido_list(request):
    """Demostración de prefetch_related (N:M): Resuelve en 3 consultas SQL fijas."""
    reset_queries()

    pedidos = Pedido.objects.all().prefetch_related('detalles__prenda')
    total_pedidos = list(pedidos)  # Forzar evaluación inmediata del QuerySet

    total_queries = len(connection.queries)

    return render(request, 'store/pedido_list.html', {
        'titulo': 'Listado de Pedidos y Detalles (prefetch_related)',
        'pedidos': total_pedidos,
        'total_queries': total_queries,
    })

Registra las nuevas rutas en store/urls.py:
Python

from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.prenda_list, name='list'),
    path('<int:pk>/', views.prenda_detail, name='detail'),
    path('details/', views.prenda_detail_list, name='details'),
    path('orders/', views.pedido_list, name='orders'),
]

Ejercicio 4 — Implementar el recorrido de relaciones en Templates
1. Acceso Directo 1:1 (templates/store/prenda_detail_list.html)

El template accede a los datos de la ficha técnica directamente a través del atributo prenda.detalle.*:
Django

{% for prenda in prendas %}
<tr>
    <td>{{ prenda.nombre }}</td>
    <td>{{ prenda.marca }}</td>
    <td>S/ {{ prenda.precio|floatformat:2 }}</td>
    <!-- Acceso Directo 1:1 -->
    <td>{{ prenda.detalle.composicion|default:"Sin ficha" }}</td>
    <td>{{ prenda.detalle.cuidados|default:"Sin especificación" }}</td>
    <td>{{ prenda.detalle.pais_origen|default:"No definido" }}</td>
</tr>
{% endfor %}

2. Acceso Inverso 1:N (templates/store/prenda_detail.html)

El template recorre las opiniones de clientes usando el descriptor inverso administrado por el ORM (prenda.resenas.all):
Django

<!-- Acceso Inverso 1:N mediante related_name -->
<div class="list-group">
    {% for r in prenda.resenas.all %}
        <div class="list-group-item">
            <strong>{{ r.cliente_nombre }}</strong> ({{ r.calificacion }}/5★)
            <p>{{ r.comentario }}</p>
        </div>
    {% empty %}
        <p class="text-muted">Esta prenda aún no tiene opiniones registradas.</p>
    {% endfor %}
</div>

3. Recorrido del Modelo Intermedio N:M (templates/store/pedido_list.html)

El template itera sobre la relación intermedia pedido.detalles.all, accediendo tanto a los atributos propios de la compra como a los atributos de la prenda vinculada:
Django

{% for pedido in pedidos %}
<div class="card mb-3">
    <div class="card-header">
        <strong>Pedido {{ pedido.codigo }}</strong> — {{ pedido.cliente_nombre }}
    </div>
    <div class="card-body">
        <table class="table">
            <thead>
                <tr>
                    <th>Artículo</th>
                    <th>Talla</th>
                    <th>Cantidad</th>
                    <th>Precio Unit.</th>
                    <th>Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {% for item in pedido.detalles.all %}
                <tr>
                    <!-- Acceso a la entidad final vinculada -->
                    <td>{{ item.prenda.nombre }}</td>
                    <td>{{ item.prenda.talla }}</td>
                    <!-- Acceso a los atributos propios del modelo intermedio -->
                    <td>{{ item.cantidad }}</td>
                    <td>S/ {{ item.precio_unitario|floatformat:2 }}</td>
                    <td>S/ {{ item.subtotal|floatformat:2 }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <div class="text-end fw-bold">Total: S/ {{ pedido.total|floatformat:2 }}</div>
    </div>
</div>
{% endfor %}

Ejercicio 5 — Carga de datos y verificación empírica

Antes de validar en el navegador, ejecuta en tu terminal los siguientes comandos para poblar las especificaciones técnicas y los pedidos de prueba:
Bash

# 1. Poblar / Actualizar fichas técnicas para todas las prendas existentes
python manage.py shell -c "from store.models import Prenda, DetallePrenda; [DetallePrenda.objects.update_or_create(prenda=p, defaults={'composicion': '100% Algodón Peruano 24/1', 'cuidados': 'Lavar con agua fría, secar a la sombra', 'pais_origen': 'Perú'}) for p in Prenda.objects.filter(activo=True)]; print('Fichas técnicas vinculadas.')"

# 2. Poblar pedidos de prueba con detalles asociados
python manage.py shell -c "from store.models import Prenda, Pedido, DetallePedido; p1 = Prenda.objects.filter(activo=True).first(); p2 = Prenda.objects.filter(activo=True).last(); ped1, _ = Pedido.objects.get_or_create(codigo='PED-001', defaults={'cliente_nombre': 'Carlos Mendoza', 'cliente_email': 'carlos@example.com', 'estado': 'Pagado'}); DetallePedido.objects.get_or_create(pedido=ped1, prenda=p1, defaults={'cantidad': 2, 'precio_unitario': p1.precio}); DetallePedido.objects.get_or_create(pedido=ped1, prenda=p2, defaults={'cantidad': 1, 'precio_unitario': p2.precio}); ped2, _ = Pedido.objects.get_or_create(codigo='PED-002', defaults={'cliente_nombre': 'Valeria Rios', 'cliente_email': 'valeria@example.com', 'estado': 'Pendiente'}); DetallePedido.objects.get_or_create(pedido=ped2, prenda=p2, defaults={'cantidad': 3, 'precio_unitario': p2.precio}); print('Pedidos creados con éxito.')"

Prueba y verificación visual:

    Ingresa a [http://127.0.0.1:8000/ropa/details/](http://127.0.0.1:8000/ropa/details/). Confirma que las 10 prendas muestran su composición textil y que el indicador marca Consultas SQL: 1 (Esperado: 1).

    Ingresa a [http://127.0.0.1:8000/ropa/orders/](http://127.0.0.1:8000/ropa/orders/). Confirma que los pedidos muestran sus subtotales calculados y que el indicador marca Consultas SQL: 3 (Esperado: 3 fijas).

    Toma captura de pantalla de ambas vistas para el informe final.

Ejercicio 6 — Analizar el flujo de persistencia y equivalencias SQL

Documenta el recorrido arquitectónico completo y la correspondencia con sentencias SQL nativas:

Request → URL → View → Model / QuerySet → Django ORM → SQLite → View → Context → Template → Response

1. Comparativa del Flujo MVT por Tipo de Optimización

Paso	Optimización 1:1 (/ropa/details/)	Optimización N:M (/ropa/orders/)
Request	GET /ropa/details/	GET /ropa/orders/
URL	store:details → prenda_detail_list	store:orders → pedido_list
View	Ejecuta select_related('detalle')	Ejecuta prefetch_related('detalles__prenda')
Model / ORM	Traduce la relación a LEFT OUTER JOIN	Ejecuta 3 sentencias por lotes con IN (...)
SQLite	Resuelve y devuelve 1 consulta con todas las columnas	Ejecuta 3 consultas fijas (pedidos, detalles, prendas)
Context	Inyecta colección de prendas con fichas en memoria	Inyecta colección de pedidos con árbol de objetos precompilado
Template	Evalúa prenda.detalle.* sin consultas secundarias	Evalúa item.prenda.* e item.subtotal sin consultas secundarias
Response	HTML con tabla de fichas técnicas	HTML con pedidos, detalles y subtotales calculados
2. Tabla de Equivalencias: Django ORM vs. SQL Nativo
Relación / Optimización	Expresión Django ORM	Consulta SQL Equivalente (SQLite)	Comportamiento en Servidor / Memoria
Relación 1:1 (select_related)	Prenda.objects.filter(activo=True).select_related('detalle')	sql SELECT store_prenda.id, store_prenda.nombre, store_prenda.precio, store_detalleprenda.composicion, store_detalleprenda.cuidados, store_detalleprenda.pais_origen FROM store_prenda LEFT OUTER JOIN store_detalleprenda ON (store_prenda.id = store_detalleprenda.prenda_id) WHERE store_prenda.activo = 1; 	1 sola consulta SQL. El motor relacional combina las filas en disco y entrega los datos ya asociados.
Relación 1:N Inversa (related_name)	prenda.resenas.all()	sql SELECT id, cliente_nombre, calificacion, comentario, fecha FROM store_resenaprenda WHERE prenda_id = 1 ORDER BY fecha DESC; 	1 consulta por cada producto. El motor busca por el índice de la clave foránea prenda_id.
Relación N:M (prefetch_related)	Pedido.objects.all().prefetch_related('detalles__prenda')	Consulta 1: sql SELECT * FROM store_pedido; Consulta 2: sql SELECT * FROM store_detallepedido WHERE pedido_id IN (1, 2); Consulta 3: sql SELECT * FROM store_prenda WHERE id IN (1, 10); 	3 consultas SQL fijas. Django agrupa los IDs en sentencias IN (...) y conecta los objetos en memoria RAM de Python mediante diccionarios hash. Complejidad O(1).
Checklist de verificación antes de cerrar el Laboratorio 04

    [x] store/models.py contiene los modelos DetallePrenda (1:1), ResenaPrenda (1:N), Pedido y DetallePedido (N:M con modelo intermedio).

    [x] Señal post_save implementada para instanciar automáticamente DetallePrenda al crear una Prenda.

    [x] Migraciones ejecutadas y tablas creadas en db.sqlite3.

    [x] prenda_detail_list utiliza select_related('detalle') y está verificada con Consultas SQL: 1.

    [x] pedido_list utiliza prefetch_related('detalles__prenda') y está verificada con Consultas SQL: 3.

    [x] prenda_detail_list.html muestra acceso directo mediante prenda.detalle.*.

    [x] prenda_detail.html muestra acceso inverso mediante prenda.resenas.all.

    [x] pedido_list.html recorre el modelo intermedio (item.cantidad, item.precio_unitario, item.subtotal) y la entidad vinculada (item.prenda.nombre).

    [x] Barra de navegación con accesos directos al Lab 04 integrada en prenda_list.html.

    [x] Documentado el flujo completo MVT y la tabla comparativa de equivalencias ORM vs SQL.

    [x] Capturas de pantalla guardadas: salida de migraciones, vista /ropa/details/ con 1 consulta y vista /ropa/orders/ con 3 consultas.


    Ingresa a [http://127.0.0.1:8000/ropa/orders/](http://127.0.0.1:8000/ropa/orders/). Confirma que los pedidos muestran sus subtotales calculados y que el indicador marca Consultas SQL: 3 (Esperado: 3 fijas).

    Toma captura de pantalla de ambas vistas para el informe final.

Ejercicio 6 — Analizar el flujo de persistencia y equivalencias SQL

Documenta el recorrido arquitectónico completo y la correspondencia con sentencias SQL nativas:

Request → URL → View → Model / QuerySet → Django ORM → SQLite → View → Context → Template → Response

1. Comparativa del Flujo MVT por Tipo de Optimización
Paso	Optimización 1:1 (/ropa/details/)	Optimización N:M (/ropa/orders/)
Request	GET /ropa/details/	GET /ropa/orders/
URL	store:details → prenda_detail_list	store:orders → pedido_list
View	Ejecuta select_related('detalle')	Ejecuta prefetch_related('detalles__prenda')
Model / ORM	Traduce la relación a LEFT OUTER JOIN	Ejecuta 3 sentencias por lotes con IN (...)
SQLite	Resuelve y devuelve 1 consulta con todas las columnas	Ejecuta 3 consultas fijas (pedidos, detalles, prendas)
Context	Inyecta colección de prendas con fichas en memoria	Inyecta colección de pedidos con árbol de objetos precompilado
Template	Evalúa prenda.detalle.* sin consultas secundarias	Evalúa item.prenda.* e item.subtotal sin consultas secundarias
Response	HTML con tabla de fichas técnicas	HTML con pedidos, detalles y subtotales calculados
2. Tabla de Equivalencias: Django ORM vs. SQL Nativo
Relación / Optimización	Expresión Django ORM	Consulta SQL Equivalente (SQLite)	Comportamiento en Servidor / Memoria
Relación 1:1 (select_related)	Prenda.objects.filter(activo=True).select_related('detalle')	sql SELECT store_prenda.id, store_prenda.nombre, store_prenda.precio, store_detalleprenda.composicion, store_detalleprenda.cuidados, store_detalleprenda.pais_origen FROM store_prenda LEFT OUTER JOIN store_detalleprenda ON (store_prenda.id = store_detalleprenda.prenda_id) WHERE store_prenda.activo = 1; 	1 sola consulta SQL. El motor relacional combina las filas en disco y entrega los datos ya asociados.
Relación 1:N Inversa (related_name)	prenda.resenas.all()	sql SELECT id, cliente_nombre, calificacion, comentario, fecha FROM store_resenaprenda WHERE prenda_id = 1 ORDER BY fecha DESC; 	1 consulta por cada producto. El motor busca por el índice de la clave foránea prenda_id.
Relación N:M (prefetch_related)	Pedido.objects.all().prefetch_related('detalles__prenda')	Consulta 1: sql SELECT * FROM store_pedido; Consulta 2: sql SELECT * FROM store_detallepedido WHERE pedido_id IN (1, 2); Consulta 3: sql SELECT * FROM store_prenda WHERE id IN (1, 10); 	3 consultas SQL fijas. Django agrupa los IDs en sentencias IN (...) y conecta los objetos en memoria RAM de Python mediante diccionarios hash. Complejidad O(1).
Checklist de verificación antes de cerrar el Laboratorio 04

    [x] store/models.py contiene los modelos DetallePrenda (1:1), ResenaPrenda (1:N), Pedido y DetallePedido (N:M con modelo intermedio).

    [x] Señal post_save implementada para instanciar automáticamente DetallePrenda al crear una Prenda.

    [x] Migraciones ejecutadas y tablas creadas en db.sqlite3.

    [x] prenda_detail_list utiliza select_related('detalle') y está verificada con Consultas SQL: 1.

    [x] pedido_list utiliza prefetch_related('detalles__prenda') y está verificada con Consultas SQL: 3.

    [x] prenda_detail_list.html muestra acceso directo mediante prenda.detalle.*.

    [x] prenda_detail.html muestra acceso inverso mediante prenda.resenas.all.

    [x] pedido_list.html recorre el modelo intermedio (item.cantidad, item.precio_unitario, item.subtotal) y la entidad vinculada (item.prenda.nombre).

    [x] Barra de navegación con accesos directos al Lab 04 integrada en prenda_list.html.

    [x] Documentado el flujo completo MVT y la tabla comparativa de equivalencias ORM vs SQL.

    [x] Capturas de pantalla guardadas: salida de migraciones, vista /ropa/details/ con 1 consulta y vista /ropa/orders/ con 3 consultas.