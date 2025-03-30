from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Asignacion, Consolidado, Estante, Ciclo, InventarioInicial, Bodega, Empleado
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import RestrictedError

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

def estantes_bodegas(request):
    bodega_id = request.GET.get('bodega_id')
    estantes = Estante.objects.filter(id_bodega=bodega_id)
    
    estanterias = []
    # y.id_empleado.nombre for y in Asignacion.objects.filter(id_estante=x)
    for x in estantes:
        estanterias.append({
            "id": x.id_estante,
            "code": x.nombre,
            "status": "assigned",
            "warehouse": x.descripcion,
            "assignedEmployees": [y.id_empleado.nombre for y in Asignacion.objects.filter(id_estante=x)],
            "productCount": "",
            "lastUpdate": ""
        })

    return JsonResponse({'estanterias': estanterias})

def empleados(request):
    empleados = Empleado.objects.all()
    data=[]
    for x in empleados:
        data.append({
            "id": x.id_empleado,
            "name": x.nombre,
            "email": x.email
        })

    return JsonResponse({'empleados': data})

import json
def asignar_empleado(request):
    try:
        datos = json.loads(request.body)
        empleadosId = datos['employeesId']  # Lista de IDs de empleados enviada desde el frontend
        estanteId = datos['currentShelfId']
        bodegaId = datos['bodegaId']

        # Obtener las instancias necesarias
        estante = Estante.objects.get(id_estante=estanteId)
        ciclo = Ciclo.objects.get(id_bodega=bodegaId)

        # Obtener las asignaciones existentes para este estante y ciclo
        asignaciones_existentes = Asignacion.objects.filter(id_estante=estante, id_ciclo=ciclo)
        empleados_asignados_actuales = set(asignaciones_existentes.values_list('id_empleado__id_empleado', flat=True))
        
        # Convertir los IDs de empleados_nuevos a enteros
        empleados_nuevos = set(int(emp_id) for emp_id in empleadosId)

        # Eliminar asignaciones de empleados que ya no están en la lista
        empleados_a_eliminar = empleados_asignados_actuales - empleados_nuevos
        if empleados_a_eliminar:
            asignaciones_a_eliminar = Asignacion.objects.filter(
                id_estante=estante,
                id_ciclo=ciclo,
                id_empleado__id_empleado__in=empleados_a_eliminar
            )
            asignaciones_a_eliminar.delete()

        # Agregar asignaciones para empleados nuevos que no estaban previamente
        empleados_a_agregar = empleados_nuevos - empleados_asignados_actuales
        for empleadoId in empleados_a_agregar:
            empleado = Empleado.objects.get(id_empleado=empleadoId)
            Asignacion.objects.create(
                id_estante=estante,
                id_empleado=empleado,
                id_ciclo=ciclo,
                estado='Conteo'
            )

        # Obtener la lista actualizada de empleados asignados con IDs y nombres
        asignaciones_actualizadas = Asignacion.objects.filter(id_estante=estante, id_ciclo=ciclo)
        empleados_asignados = [
            {'id': asignacion.id_empleado.id_empleado, 'name': asignacion.id_empleado.nombre}
            for asignacion in asignaciones_actualizadas
        ]

        return JsonResponse({
            'message': 'Asignaciones actualizadas exitosamente',
            'eliminados': len(empleados_a_eliminar),
            'agregados': len(empleados_a_agregar),
            'empleados_asignados': empleados_asignados
        })
    except ValueError:
        return JsonResponse({'message': 'Los IDs de empleados deben ser números enteros'}, status=400)
    except Estante.DoesNotExist:
        return JsonResponse({'message': 'El estante no existe'}, status=400)
    except Ciclo.DoesNotExist:
        return JsonResponse({'message': 'El ciclo no existe'}, status=400)
    except Empleado.DoesNotExist:
        return JsonResponse({'message': 'Uno o más empleados no existen'}, status=400)
    except RestrictedError as e:
        return JsonResponse({'message': "No se pueden eliminar las asignaciones de los siguientes empleados porque tienen reportes asociados"}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)