from django.urls import path
from . import views

urlpatterns = [
    path('<int:id_bodega>/estantes/', views.estantes_por_bodega , name='estantes_por_bodega'),  # Dashboard según rol
    path('estantes_bodegas', views.estantes_bodegas, name='estantes_bodegas'),
    path('empleados', views.empleados, name='empleados'), 
    path('asignar_empleado', views.asignar_empleado, name='asignar_empleado'), 
]
