from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from bitware.models import Cuentas

class CatalogoCuentasView(LoginRequiredMixin, View):
    template_name = 'catalogo_cuentas.html'

    def get(self, request):
        cuentas = Cuentas.objects.all().order_by('codigo_cuenta')

        # ¿Nos piden editar?
        id_editar = request.GET.get('editar')
        cuenta_editar = None
        if id_editar:
            cuenta_editar = Cuentas.objects.filter(id_cuenta=id_editar).first()

        return render(request, self.template_name,
                      {'cuentas': cuentas, 'cuenta_editar': cuenta_editar})

    def post(self, request):
        accion = 'editar' if request.POST.get('id_cuenta') else 'crear'
        id_cuenta = request.POST.get('id_cuenta')

        nombre = request.POST.get('nombre_cuenta', '').strip()
        codigo = request.POST.get('codigo_cuenta', '').strip()
        tipo   = request.POST.get('tipo', '')
        permite = bool(request.POST.get('permite_movimientos'))

        if not all([nombre, codigo, tipo]):
            messages.error(request, 'Faltan campos obligatorios.')
            return redirect('catalogo_cuentas')

        try:
            if accion == 'editar':
                cuenta = Cuentas.objects.get(id_cuenta=id_cuenta)
                # evitar duplicado de código si cambia
                if Cuentas.objects.exclude(id_cuenta=id_cuenta).filter(codigo_cuenta=codigo).exists():
                    messages.error(request, 'El código ya existe.')
                    return redirect('catalogo_cuentas')

                cuenta.nombre_cuenta = nombre
                cuenta.codigo_cuenta = codigo
                cuenta.tipo = tipo
                cuenta.permite_movimientos = permite
                cuenta.save()
                messages.success(request, 'Cuenta actualizada.')
            else:
                if Cuentas.objects.filter(codigo_cuenta=codigo).exists():
                    messages.error(request, 'El código ya existe.')
                    return redirect('catalogo_cuentas')

                Cuentas.objects.create(
                    nombre_cuenta=nombre,
                    codigo_cuenta=codigo,
                    tipo=tipo,
                    permite_movimientos=permite
                )
                messages.success(request, 'Cuenta creada.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

        return redirect('catalogo_cuentas')