from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Sum
# --- ¡CAMBIO! Importamos el modelo de Periodos ---
from bitware.models import Cuentas, DetalleTransaccion, PeriodosContables

class CuentasT(LoginRequiredMixin, View):
    template_name = 'cuentas_t.html'

    def get(self, request):
        
        # --- ¡CAMBIO! 1. Buscamos el periodo activo ---
        try:
            periodo_activo = PeriodosContables.objects.get(estado='Activo')
        except PeriodosContables.DoesNotExist:
            # Si no hay periodo activo, no podemos mostrar nada
            return render(request, self.template_name, {
                'cuentas_con_datos': [], 
                'error': 'No se encontró un periodo contable activo.'
            })

        # 2. Obtenemos todas las cuentas
        cuentas = Cuentas.objects.all().order_by('codigo_cuenta')
        cuentas_con_datos = []

        for cuenta in cuentas:
            
            # --- ¡CAMBIO! 3. Filtramos TODOS los movimientos de esta cuenta EN ESTE PERIODO ---
            movimientos_periodo = DetalleTransaccion.objects.filter(
                id_cuenta=cuenta,
                id_transaccion__fecha__range=[periodo_activo.fecha_inicio, periodo_activo.fecha_fin]
            )

            # 4. De esos movimientos, separamos para las listas del "Debe" y "Haber"
            # (select_related optimiza la consulta para no golpear la DB por cada transacción)
            movimientos_debe = movimientos_periodo.filter(debe__gt=0).select_related('id_transaccion')
            movimientos_haber = movimientos_periodo.filter(haber__gt=0).select_related('id_transaccion')

            # --- ¡CAMBIO! 5. Calculamos los totales usando TODOS los movimientos del periodo ---
            # (Tu código anterior solo sumaba los > 0, lo cual era incorrecto)
            totales = movimientos_periodo.aggregate(
                total_debe=Sum('debe'),
                total_haber=Sum('haber')
            )

            cuentas_con_datos.append({
                'cuenta': cuenta,
                'movimientos_debe': movimientos_debe,
                'movimientos_haber': movimientos_haber,
                'total_debe': totales['total_debe'] or 0,
                'total_haber': totales['total_haber'] or 0,
            })

        return render(request, self.template_name, {
            'cuentas_con_datos': cuentas_con_datos,
            'periodo_activo': periodo_activo, # Enviamos el periodo para mostrarlo (ej. "Octubre 2025")
            'total_cuentas': cuentas.count()
        })