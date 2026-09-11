from django.shortcuts import render, redirect
from django.http import Http404
from django.db.models import Q
from .models import Prenda, ResenaPrenda
from .forms import PrendaForm, ResenaPrendaForm



def prenda_list(request):
    query = request.GET.get('q', '').strip().lower()
    tipo = request.GET.get('tipo', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    prendas = Prenda.objects.filter(activo=True)

    if query:
        prendas = prendas.filter(
            Q(nombre__icontains=query) |
            Q(marca__icontains=query) |
            Q(descripcion__icontains=query)
        )

    if tipo:
        prendas = prendas.filter(tipo=tipo)

    if categoria:
        prendas = prendas.filter(categoria=categoria)

    total_catalogo = Prenda.objects.filter(activo=True).count()
    total_stock_global = sum(p.stock for p in Prenda.objects.filter(activo=True))
    total_activas = Prenda.objects.filter(activo=True, disponible=True).count()

    contexto = {
        'titulo': 'Catálogo de Ropa Streetwear',
        'prendas': prendas,
        'query': request.GET.get('q', ''),
        'tipo_seleccionado': tipo,
        'categoria_seleccionada': categoria,
        'total_resultados': prendas.count(),
        'total_catalogo': total_catalogo,
        'total_stock_global': total_stock_global,
        'total_activas': total_activas,
    }
    return render(request, 'store/prenda_list.html', contexto)


def prenda_detail(request, prenda_id):
    try:
        prenda = Prenda.objects.get(id=prenda_id, activo=True)
    except Prenda.DoesNotExist:
        raise Http404(f"La prenda con ID #{prenda_id} no existe o no está activa.")

    resena_form = ResenaPrendaForm()

    if request.method == 'POST' and 'submit_resena' in request.POST:
        resena_form = ResenaPrendaForm(request.POST)
        if resena_form.is_valid():
            ResenaPrenda.objects.create(
                prenda=prenda,
                cliente_nombre=resena_form.cleaned_data['cliente_nombre'],
                calificacion=int(resena_form.cleaned_data['calificacion']),
                comentario=resena_form.cleaned_data['comentario'],
            )
            return redirect('store:detail', prenda_id=prenda.id)

    resenas = prenda.resenas.all()
    total_resenas = resenas.count()
    promedio_calificacion = round(sum(r.calificacion for r in resenas) / total_resenas, 1) if total_resenas > 0 else None

    return render(request, 'store/prenda_detail.html', {
        'prenda': prenda,
        'titulo': f"Detalle: {prenda.nombre}",
        'resenas': resenas,
        'total_resenas': total_resenas,
        'promedio_calificacion': promedio_calificacion,
        'resena_form': resena_form,
    })



def prenda_create(request):
    if request.method == 'POST':
        form = PrendaForm(request.POST)
        if form.is_valid():
            Prenda.objects.create(
                nombre=form.cleaned_data['nombre'],
                marca=form.cleaned_data['marca'],
                tipo=form.cleaned_data['tipo'],
                categoria=form.cleaned_data['categoria'],
                talla=form.cleaned_data['talla'],
                precio=form.cleaned_data['precio'],
                stock=form.cleaned_data['stock'],
                disponible=form.cleaned_data['disponible'],
                activo=form.cleaned_data.get('activo', True),
                descripcion=form.cleaned_data['descripcion'],
            )
            return redirect('store:list')
    else:
        form = PrendaForm()

    return render(request, 'store/prenda_form.html', {
        'titulo': 'Registrar Nueva Prenda',
        'form': form,
    })