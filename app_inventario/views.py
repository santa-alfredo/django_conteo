from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Asignacion, Consolidado, Estante, Ciclo, InventarioInicial, Bodega, Empleado
from django.contrib import messages

# Create your views here.
@login_required
def home(request):
    if request.user.groups.filter(name='Administrador').exists():
        return admin_dashboard(request)
    elif request.user.groups.filter(name='Empleado').exists():
        return empleado_dashboard(request)
    else:
        return redirect('login')

# Dashboard del Administrador
def admin_dashboard(request):
    bodegas = Bodega.objects.all()
    ciclos = Ciclo.objects.all()
    asignaciones = Asignacion.objects.all()
    consolidados = Consolidado.objects.all()
    inconsistencias = Consolidado.objects.filter(estado='Inconsistente')

    context = {
        'bodegas': bodegas,
        'ciclos': ciclos,
        'asignaciones': asignaciones,
        'consolidados': consolidados,
        'inconsistencias': inconsistencias,
    }
    return render(request, 'admin_dashboard.html', context)

# Dashboard del Empleado
def empleado_dashboard(request):
    asignaciones = Asignacion.objects.filter(
        id_empleado__email=request.user.email, completada=False
    )
    context = {
        'asignaciones': asignaciones,
    }
    return render(request, 'empleado_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.groups.filter(name='Administrador').exists())
def estantes_por_bodega(request, id_bodega):
    # Obtener la bodega o devolver 404 si no existe
    bodega = get_object_or_404(Bodega, id_bodega=id_bodega)
    
    # Filtrar estantes por bodega
    estantes = Estante.objects.filter(id_bodega=bodega)
    
    # Obtener asignaciones para los estantes (solo del ciclo activo, por ejemplo)
    ciclo_activo = Ciclo.objects.filter(id_bodega=bodega, completado=False).first()  # Último ciclo no completado
    asignaciones = Asignacion.objects.filter(id_estante__id_bodega=bodega, id_ciclo=ciclo_activo) if ciclo_activo else []

    # Lista de empleados disponibles para asignar
    empleados = Empleado.objects.filter(activo=True)

    if request.method == 'POST':
        estante_id = request.POST.get('estante_id')
        empleado_id = request.POST.get('empleado_id')
        if estante_id and empleado_id:
            estante = Estante.objects.get(id_estante=estante_id)
            empleado = Empleado.objects.get(id_empleado=empleado_id)
            if ciclo_activo:
                # Verificar si el empleado ya está asignado al estante en este ciclo
                if not Asignacion.objects.filter(id_estante=estante, id_empleado=empleado, id_ciclo=ciclo_activo).exists():
                    Asignacion.objects.create(
                        id_estante=estante,
                        id_empleado=empleado,
                        id_ciclo=ciclo_activo,
                        estado='Conteo'  # Asignación inicial como "Conteo"
                    )
                    messages.success(request, f"Empleado {empleado} asignado a {estante}.")
                else:
                    messages.error(request, "Este empleado ya está asignado a este estante.")
            else:
                messages.error(request, "No hay un ciclo activo para esta bodega.")
            return redirect('estantes_por_bodega', id_bodega=id_bodega)

    context = {
        'bodega': bodega,
        'estantes': estantes,
        'asignaciones': asignaciones,
        'empleados': empleados,
        'ciclo_activo': ciclo_activo,
    }
    return render(request, 'estantes_por_bodega.html', context)