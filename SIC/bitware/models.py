# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Configuracion(models.Model):
    clave = models.CharField(primary_key=True, max_length=50)
    valor = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'configuracion'


class Cuentas(models.Model):
    id_cuenta = models.AutoField(primary_key=True)
    codigo_cuenta = models.CharField(unique=True, max_length=20)
    nombre_cuenta = models.CharField(max_length=255)
    tipo = models.CharField(max_length=50)
    cuenta_padre = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    permite_movimientos = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'cuentas'


class DetalleTransaccion(models.Model):
    id_detalle_transaccion = models.AutoField(primary_key=True)
    id_transaccion = models.ForeignKey('Transacciones', models.DO_NOTHING, db_column='id_transaccion')
    id_cuenta = models.ForeignKey(Cuentas, models.DO_NOTHING, db_column='id_cuenta')
    debe = models.DecimalField(max_digits=12, decimal_places=2)
    haber = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'detalle_transaccion'


class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=255)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    salario_mensual = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'empleados'


class MaterialesDirectos(models.Model):
    id_material = models.AutoField(primary_key=True)
    nombre_material = models.CharField(max_length=255)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'materiales_directos'


class PeriodosContables(models.Model):
    id_periodo = models.AutoField(primary_key=True)
    nombre_periodo = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'periodos_contables'


class RegistroActividades(models.Model):
    id_actividad_registro = models.AutoField(primary_key=True)
    id_empleado = models.ForeignKey(Empleados, models.DO_NOTHING, db_column='id_empleado')
    fecha = models.DateField()
    orden_servicio = models.CharField(max_length=100, blank=True, null=True)
    tipo_actividad = models.CharField(max_length=50)
    horas_dedicadas = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'registro_actividades'


class ResultadosCierre(models.Model):
    id_resultado = models.AutoField(primary_key=True)
    id_periodo = models.OneToOneField(PeriodosContables, models.DO_NOTHING, db_column='id_periodo')
    id_usuario_cierre = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='id_usuario_cierre')
    fecha_cierre = models.DateTimeField()
    resultado_del_ejercicio = models.DecimalField(max_digits=20, decimal_places=2)
    total_activos = models.DecimalField(max_digits=20, decimal_places=2)
    total_pasivos = models.DecimalField(max_digits=20, decimal_places=2)
    total_patrimonio = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'resultados_cierre'


class Transacciones(models.Model):
    id_transaccion = models.AutoField(primary_key=True)
    fecha = models.DateField()
    descripcion = models.TextField()
    numero_documento = models.CharField(max_length=100, blank=True, null=True)
    id_usuario_creador = models.ForeignKey('Usuarios', models.DO_NOTHING, db_column='id_usuario_creador', blank=True, null=True)
    id_periodo = models.ForeignKey(PeriodosContables, models.DO_NOTHING, db_column='id_periodo', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transacciones'


class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=255)
    nombre_usuario = models.CharField(unique=True, max_length=50)
    contrasena_hash = models.CharField(max_length=255)
    rol = models.CharField(max_length=50)
    last_login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
