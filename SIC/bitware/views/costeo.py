from django.shortcuts import render, redirect
<<<<<<< Updated upstream
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
@login_required
def costeo(request):
   
   
    return render(request, 'costeo.html')
=======
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.http import JsonResponse
import json
import datetime

# IMPORTANTE: Usamos los nombres de modelo EXACTOS de tu models.py
from bitware.models import Cuentas, DetalleTransaccion, Empleados, RegistroActividades

def get_saldo_gasto(codigo_cuenta):
    """
    Calcula el saldo (Debe - Haber) de una cuenta de gasto 
    usando la tabla de transacciones.
    """
    try:
        cuenta = Cuentas.objects.get(codigo_cuenta=codigo_cuenta)
        
        balance = DetalleTransaccion.objects.filter(id_cuenta=cuenta).aggregate(
            total_debe=Coalesce(Sum('debe'), Decimal('0.00')),
            total_haber=Coalesce(Sum('haber'), Decimal('0.00'))
        )
        
        # Para cuentas de Gasto, el saldo es (Debe - Haber)
        saldo = balance['total_debe'] - balance['total_haber']
        return saldo

    except Cuentas.DoesNotExist:
        return Decimal('0.00')


class CosteoABC(LoginRequiredMixin, View):
    template_name = 'costeo.html'
    
    # --- FACTORES DE PRORRATEO (Tu lógica de cuentas) ---
    FACTOR_ALQUILER = Decimal('0.35')      # 35%
    FACTOR_EMPLEADOS = Decimal(6) / Decimal(35)  # 17.14%
    FACTOR_PUBLICIDAD = Decimal('0.40')    # 40%

    # --- ¡CAMBIO! ---
    # La variable BASE_TOTAL_HORAS_MES ya no se usa con tu nueva lógica de CIF.
    # La hemos eliminado.

    def _calcular_total_cif(self):
        """
        Función helper privada para calcular el CIF Total del Mes.
        Esta función no cambia, sigue sumando tus cuentas de gasto.
        """
        # A. CIF 100% Directos
        cif_directo_1 = get_saldo_gasto('4110')   # Gastos Indirectos Soporte
        cif_directo_2 = get_saldo_gasto('411201') # Gasto depreciación equipo taller
        total_cif_directo = cif_directo_1 + cif_directo_2

        # B. CIF Prorrateados
        cif_prorrateo_alquiler = get_saldo_gasto('411302') * self.FACTOR_ALQUILER
        cif_prorrateo_admin = get_saldo_gasto('4109') * self.FACTOR_EMPLEADOS
        cif_prorrateo_depre_mob = get_saldo_gasto('411101') * self.FACTOR_EMPLEADOS
        cif_prorrateo_suministros = get_saldo_gasto('411301') * self.FACTOR_EMPLEADOS
        cif_prorrateo_publicidad = get_saldo_gasto('411303') * self.FACTOR_PUBLICIDAD

        total_cif_prorrateo = (
            cif_prorrateo_alquiler +
            cif_prorrateo_admin +
            cif_prorrateo_depre_mob +
            cif_prorrateo_suministros +
            cif_prorrateo_publicidad
        )
        
        return total_cif_directo + total_cif_prorrateo

    # --- ¡NUEVA FUNCIÓN! ---
    def _get_proxima_orden(self):
        """
        Calcula el siguiente número de orden automático.
        Ej: "ORD-00001"
        """
        proxima_orden_num = 1
        try:
            # Busca el último registro por su ID
            ultimo_registro = RegistroActividades.objects.latest('id_actividad_registro')
            proxima_orden_num = ultimo_registro.id_actividad_registro + 1
        except RegistroActividades.DoesNotExist:
            # Si no hay registros, empezamos en 1
            proxima_orden_num = 1
        
        # Formatea el número (ej: ORD-00001)
        return f"ORD-{proxima_orden_num:05d}"

    def get(self, request):
        """
        Maneja la carga inicial de la página.
        """
        # 1. Calcular el CIF del Mes
        total_cif_mes = self._calcular_total_cif()

        # 2. Obtener lista de Técnicos
        lista_tecnicos = Empleados.objects.filter(
            Q(puesto__icontains='Técnico') | Q(puesto__icontains='Soporte')
        ).order_by('nombre_completo')

        # 3. Obtener los servicios ya registrados
        hoy = datetime.date.today()
        servicios_registrados = RegistroActividades.objects.filter(
            fecha__year=hoy.year, 
            fecha__month=hoy.month
        ).order_by('-fecha')

        # 4. Calcular los totales para la tabla
        totales = servicios_registrados.aggregate(
            total_mod=Coalesce(Sum('costo_mod'), Decimal('0.00')),
            total_cif=Coalesce(Sum('costo_cif'), Decimal('0.00')),
            total_costo=Coalesce(Sum('costo_total'), Decimal('0.00'))
        )
        
        # --- ¡CAMBIO! ---
        # 5. Obtener el próximo número de orden para mostrarlo
        proxima_orden = self._get_proxima_orden()

        context = {
            'total_cif_mes': total_cif_mes,
            'tecnicos': lista_tecnicos,
            'servicios_registrados': servicios_registrados,
            'totales': totales,
            'proxima_orden': proxima_orden, # <-- ¡CAMBIO! Lo pasamos al HTML
        }
        
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Maneja el envío del formulario "Registrar Servicio".
        """
        
        # --- 1. Obtener datos del Formulario ---
        # ¡CAMBIO! 'orden_servicio' ya no se lee del POST, se calcula.
        fecha = request.POST.get('fecha')
        id_empleado_form = request.POST.get('id_empleado')
        actividad = request.POST.get('tipo_actividad')
        horas_str = request.POST.get('horas_dedicadas', '0')
        
        try:
            # ¡CAMBIO! Convertimos a Decimal y luego a int (para horas enteras)
            horas = int(Decimal(horas_str))
        except:
            horas = 0 # Seguridad

        # --- 2. Realizar Cálculos ---
        
        # A. Calcular MOD (Mano de Obra Directa)
        try:
            empleado = Empleados.objects.get(id_empleado=id_empleado_form)
            
            # ¡OJO AQUÍ!
            # Si tu campo en models.py se llama 'costo_realh', cambia 'tasa_horaria' por 'costo_realh'.
            costo_mod = (empleado.costo_realh or Decimal('0.00')) * horas
    
        except Empleados.DoesNotExist:
            costo_mod = Decimal('0.00')
            empleado = None
        
        # B. Calcular CIF (Costos Indirectos) - ¡TU NUEVA LÓGICA!
        total_cif_mes = self._calcular_total_cif()
        costo_cif_aplicado = Decimal('0.00')
# --- CÓDIGO CORREGIDO ---
        if actividad == 'Instalación': # <-- ¡Con acento!
            # (horas * ((Total_CIF * 40%) / 20))
            tasa_instalacion = (total_cif_mes * Decimal('0.40')) / Decimal('20')
            costo_cif_aplicado = horas * tasa_instalacion
        elif actividad == 'Diagnóstico': # <-- ¡Con acento!
            # (horas * ((Total_CIF * 60%) / 30))
            tasa_diagnostico = (total_cif_mes * Decimal('0.60')) / Decimal('30')
            costo_cif_aplicado = horas * tasa_diagnostico

        # C. Calcular Costo Total
        costo_total = costo_mod + costo_cif_aplicado

        # --- 3. Guardar en la Base de Datos ---
        # Solo guarda si el empleado existe y se registraron horas
        if empleado and horas > 0:
            
            # ¡CAMBIO! Calculamos la orden aquí para evitar duplicados
            orden_a_guardar = self._get_proxima_orden()

            nuevo_servicio = RegistroActividades(
                orden_servicio=orden_a_guardar, # <-- ¡CAMBIO!
                fecha=fecha,
                id_empleado=empleado, 
                tipo_actividad=actividad,
                horas_dedicadas=horas, # <-- Ahora es un entero
                costo_mod=costo_mod,
                costo_cif=costo_cif_aplicado, # <-- Nuevo cálculo
                costo_total=costo_total
            )
            nuevo_servicio.save()

        # --- 4. Redirigir a la misma página ---
        return redirect('costeo_abc')
    
# --- ¡NUEVA VISTA PARA EL MODAL! ---
# (Pega esto AFUERA de la clase CosteoABC)
def calcular_preview_costo(request):
    """
    Recibe datos por AJAX (POST) y devuelve los cálculos
    de MOD, CIF y Total sin guardar.
    """
    if request.method == 'POST':
        try:
            # Leemos los datos JSON que envía JavaScript
            data = json.loads(request.body)
            id_empleado = int(data.get('id_empleado'))
            horas = Decimal(data.get('horas', '0'))
            actividad = data.get('actividad')

            # --- 1. Calcular MOD ---
            empleado = Empleados.objects.get(id_empleado=id_empleado)
            # (Usamos tu nombre de campo 'costo_realh')
            costo_mod = (empleado.costo_realh or Decimal('0.00')) * horas

            # --- 2. Calcular CIF (Re-usamos la lógica de la clase) ---
            cif_calculator = CosteoABC()
            total_cif_mes = cif_calculator._calcular_total_cif() # Llama al helper

            costo_cif_aplicado = Decimal('0.00')

            # (¡Con acentos, como corregimos!)
            if actividad == 'Instalación':
                tasa_instalacion = (total_cif_mes * Decimal('0.40')) / Decimal('20')
                costo_cif_aplicado = horas * tasa_instalacion
            elif actividad == 'Diagnóstico':
                tasa_diagnostico = (total_cif_mes * Decimal('0.60')) / Decimal('30')
                costo_cif_aplicado = horas * tasa_diagnostico
            
            # --- CORRECCIÓN DE TABULACIÓN ---
            # 'costo_total' debe estar aquí, fuera del 'elif'
            costo_total = costo_mod + costo_cif_aplicado

            # --- 3. Devolver los datos como JSON ---
            return JsonResponse({
                'status': 'ok',
                'tecnico_nombre': empleado.nombre_completo,
                'mod': f"{costo_mod:.2f}",
                'cif': f"{costo_cif_aplicado:.2f}",
                'total': f"{costo_total:.2f}"
            })

        # --- CORRECCIÓN DE TABULACIÓN ---
        # 'except' debe estar alineado con 'try'
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # --- CORRECCIÓN DE TABULACIÓN ---
    # 'return' debe estar alineado con 'if request.method'
    return JsonResponse({'status': 'error', 'message': 'Solo se permite POST'}, status=405)

>>>>>>> Stashed changes
