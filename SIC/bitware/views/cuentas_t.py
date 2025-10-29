from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Sum
from bitware.models import Cuentas, DetalleTransaccion

class CuentasT(LoginRequiredMixin, View):
    template_name = 'cuentas_t.html'

    def get(self, request):
        cuentas = Cuentas.objects.all().order_by('codigo_cuenta')
        cuentas_con_datos = []

        for cuenta in cuentas:
            # Movimientos donde esta cuenta tiene valor en "debe"
            movimientos_debe = DetalleTransaccion.objects.filter(
                id_cuenta=cuenta,
                debe__gt=0
            ).select_related('id_transaccion')

            # Movimientos donde esta cuenta tiene valor en "haber"
            movimientos_haber = DetalleTransaccion.objects.filter(
                id_cuenta=cuenta,
                haber__gt=0
            ).select_related('id_transaccion')

            # Totales
            total_debe = movimientos_debe.aggregate(total=Sum('debe'))['total'] or 0
            total_haber = movimientos_haber.aggregate(total=Sum('haber'))['total'] or 0

            cuentas_con_datos.append({
                'cuenta': cuenta,
                'movimientos_debe': movimientos_debe,
                'movimientos_haber': movimientos_haber,
                'total_debe': total_debe,
                'total_haber': total_haber,
            })

        return render(request, self.template_name, {
            'cuentas_con_datos': cuentas_con_datos
        })


    

    
