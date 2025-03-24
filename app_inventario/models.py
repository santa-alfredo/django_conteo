from django.db import models

# Create your models here.
from django.db import models


# Modelo para Bodegas
class Bodega(models.Model):
    id_bodega = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    ubicacion = models.CharField(max_length=150, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'bodegas'  # Nombre exacto de la tabla en la BD

    def __str__(self):
        return self.nombre


# Modelo para Estantes
class Estante(models.Model):
    id_estante = models.AutoField(primary_key=True)
    id_bodega = models.ForeignKey(Bodega, on_delete=models.RESTRICT, db_column='id_bodega')
    nombre = models.CharField(max_length=50, null=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'estantes'

    def __str__(self):
        return f"{self.nombre} ({self.id_bodega.nombre})"


# Modelo para Empleados
class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=False)
    apellido = models.CharField(max_length=100, null=False)
    documento = models.CharField(max_length=20, unique=True, null=True, blank=True)
    cargo = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=150, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    fecha_contratacion = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# Modelo para Ciclos
class Ciclo(models.Model):
    ESTADO_CHOICES = [
        ('Conteo', 'Conteo'),
        ('Reconteo', 'Reconteo'),
    ]
    id_ciclo = models.AutoField(primary_key=True)
    id_bodega = models.ForeignKey(Bodega, on_delete=models.RESTRICT, db_column='id_bodega')
    nombre = models.CharField(max_length=50, null=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Conteo')
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_fin = models.DateField(null=True, blank=True)
    completado = models.BooleanField(default=False)

    class Meta:
        db_table = 'ciclos'

    def __str__(self):
        return f"{self.nombre} - {self.id_bodega.nombre}"


# Modelo para Asignaciones
class Asignacion(models.Model):
    ESTADO_CHOICES = [
        ('Conteo', 'Conteo'),
        ('Reconteo', 'Reconteo'),
    ]
    id_asignacion = models.AutoField(primary_key=True)
    id_estante = models.ForeignKey(Estante, on_delete=models.RESTRICT, db_column='id_estante')
    id_empleado = models.ForeignKey(Empleado, on_delete=models.RESTRICT, db_column='id_empleado')
    id_ciclo = models.ForeignKey(Ciclo, on_delete=models.RESTRICT, db_column='id_ciclo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Conteo')
    fecha_asignacion = models.DateField(auto_now_add=True)
    completada = models.BooleanField(default=False)

    class Meta:
        db_table = 'asignaciones'

    def __str__(self):
        return f"{self.id_empleado} - {self.id_estante} ({self.id_ciclo})"


# Modelo para Inventario Inicial
class InventarioInicial(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, null=False)
    nombre = models.CharField(max_length=100, null=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    unidad_medida = models.CharField(max_length=20, null=False)
    cantidad_total = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_compra = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventario_inicial'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


# Modelo para Reporte Inventario
class ReporteInventario(models.Model):
    ESTADO_PRODUCTO_CHOICES = [
        ('Bueno', 'Bueno'),
        ('Dañado', 'Dañado'),
        ('Faltante', 'Faltante'),
    ]
    id_reporte = models.AutoField(primary_key=True)
    id_asignacion = models.ForeignKey(Asignacion, on_delete=models.RESTRICT, db_column='id_asignacion')
    id_inventario = models.ForeignKey(InventarioInicial, on_delete=models.RESTRICT, db_column='id_inventario')
    cantidad_reportada = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    estado_producto = models.CharField(max_length=20, choices=ESTADO_PRODUCTO_CHOICES, default='Bueno')
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    notas = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'reporte_inventario'

    def __str__(self):
        return f"{self.id_inventario.nombre} - {self.cantidad_reportada}"


# Modelo para Consolidado
class Consolidado(models.Model):
    ESTADO_CHOICES = [
        ('Validado', 'Validado'),
        ('Inconsistente', 'Inconsistente'),
    ]
    id_consolidado = models.AutoField(primary_key=True)
    id_ciclo = models.ForeignKey(Ciclo, on_delete=models.RESTRICT, db_column='id_ciclo')
    id_inventario = models.ForeignKey(InventarioInicial, on_delete=models.RESTRICT, db_column='id_inventario')
    cantidad_total_confirmada = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Validado')
    fecha_consolidado = models.DateField(auto_now_add=True)
    notas = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'consolidado'

    def __str__(self):
        return f"{self.id_inventario.nombre} - {self.id_ciclo.nombre}"