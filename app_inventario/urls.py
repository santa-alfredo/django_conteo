from django.urls import path
from . import views

urlpatterns = [
    path('<int:id_bodega>/estantes/', views.estantes_por_bodega , name='estantes_por_bodega'),  # Dashboard según rol
]
