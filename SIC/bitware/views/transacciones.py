from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db import transaction
from django.db.models import Q
from bitware.models import (
    Cuentas, 
    Configuracion, 
    Transacciones, 
    DetalleTransaccion, 
    PeriodosContables
)
from django.contrib import messages
from decimal import Decimal


class transacciones(LoginRequiredMixin, View):
    template_name = 'transacciones.html'

    def get(self, request):
        # Obtener configuraciones (IVA, ISR, etc.)
        try:
            iva_config = Configuracion.objects.get(clave='tasa_iva')
            tasa_iva = float(iva_config.valor)
        except Configuracion.DoesNotExist:
            tasa_iva = 0.13  # valor por defecto

        try:
            isr_config = Configuracion.objects.get(clave='tasa_isr')
            tasa_isr = float(isr_config.valor)
        except Configuracion.DoesNotExist:
            tasa_isr = 0.10  # valor por defecto

        # Obtener tipos únicos para el filtro de "Cuentas de estado"
        tipos_estado = Cuentas.objects.values_list('tipo', flat=True).distinct().order_by('tipo')

        # Obtener todas las cuentas que permiten movimientos
        cuentas_contables = Cuentas.objects.filter(
            permite_movimientos=True
        ).order_by('codigo_cuenta')

        # Obtener cuentas específicas de IVA
        cuenta_iva_credito = Cuentas.objects.filter(
            Q(nombre_cuenta__icontains='IVA Crédito') | 
            Q(nombre_cuenta__icontains='IVA CF')
        ).first()
        
        cuenta_iva_debito = Cuentas.objects.filter(
            Q(nombre_cuenta__icontains='IVA Débito') | 
            Q(nombre_cuenta__icontains='IVA DF')
        ).first()

        context = {
            'tipos_estado': tipos_estado,
            'cuentas_contables': cuentas_contables,
            'tasa_iva': tasa_iva,
            'tasa_isr': tasa_isr,
            'cuenta_iva_credito': cuenta_iva_credito,
            'cuenta_iva_debito': cuenta_iva_debito,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. Obtener datos del encabezado
                fecha = request.POST.get('fecha')
                concepto = request.POST.get('concepto', '').strip()
                numero_documento = request.POST.get('numero_documento', '').strip()
                
                if not fecha or not concepto:
                    messages.error(request, "Fecha y concepto son obligatorios.")
                    return self.get(request)
                
                # 2. Obtener datos de las partidas
                tipos_estado = request.POST.getlist('tipo_estado[]')
                cuentas_contables_ids = request.POST.getlist('cuenta_contable[]')
                montos = request.POST.getlist('monto[]')
                es_debe_list = request.POST.getlist('es_debe[]')
                es_haber_list = request.POST.getlist('es_haber[]')

                if not cuentas_contables_ids:
                    messages.error(request, "Debe agregar al menos una partida.")
                    return self.get(request)

                # 3. Validar y calcular totales
                total_debe = Decimal('0.00')
                total_haber = Decimal('0.00')
                movimientos = []

                for i in range(len(cuentas_contables_ids)):
                    id_cuenta = cuentas_contables_ids[i]
                    monto_str = montos[i] if i < len(montos) else '0'
                    monto = Decimal(monto_str) if monto_str else Decimal('0.00')
                    
                    # Los checkboxes envían su índice como valor
                    es_debe = str(i) in es_debe_list
                    es_haber = str(i) in es_haber_list

                    if not id_cuenta or monto <= 0:
                        continue

                    # Validar que no sea debe y haber al mismo tiempo
                    if es_debe and es_haber:
                        messages.error(request, "Una partida no puede ser Debe y Haber al mismo tiempo.")
                        return self.get(request)
                    
                    if not es_debe and not es_haber:
                        messages.error(request, "Cada partida debe ser Debe o Haber.")
                        return self.get(request)

                    # Acumular totales
                    if es_debe:
                        total_debe += monto
                        movimientos.append({
                            'id_cuenta': id_cuenta,
                            'debe': monto,
                            'haber': Decimal('0.00'),
                        })
                    else:  # es_haber
                        total_haber += monto
                        movimientos.append({
                            'id_cuenta': id_cuenta,
                            'debe': Decimal('0.00'),
                            'haber': monto,
                        })

                # 4. Procesar IVA si aplica
                aplica_iva = request.POST.get('aplica_iva') == 'on'
                if aplica_iva:
                    cuenta_base_iva = request.POST.get('cuenta_base_iva', '')
                    cuenta_iva_id = request.POST.get('cuenta_iva')
                    monto_iva_str = request.POST.get('monto_iva', '0')
                    iva_tipo_movimiento = request.POST.get('iva_tipo_movimiento', 'debe')
                    
                    if cuenta_base_iva and cuenta_iva_id:
                        try:
                            # Obtener el monto de la cuenta base (índice en la lista)
                            index_base = int(cuenta_base_iva)
                            if index_base < len(montos):
                                monto_base = Decimal(montos[index_base]) if montos[index_base] else Decimal('0.00')
                                
                                # Calcular IVA
                                tasa_iva_decimal = Decimal(str(request.POST.get('tasa_iva', '0.13')))
                                monto_iva = monto_base * tasa_iva_decimal
                                
                                # Agregar movimiento del IVA
                                if iva_tipo_movimiento == 'debe':
                                    total_debe += monto_iva
                                    movimientos.append({
                                        'id_cuenta': cuenta_iva_id,
                                        'debe': monto_iva,
                                        'haber': Decimal('0.00'),
                                    })
                                else:  # haber
                                    total_haber += monto_iva
                                    movimientos.append({
                                        'id_cuenta': cuenta_iva_id,
                                        'debe': Decimal('0.00'),
                                        'haber': monto_iva,
                                    })
                        except (ValueError, IndexError) as e:
                            messages.error(request, f"Error al procesar el IVA: {str(e)}")
                            return self.get(request)

                # 5. Validar que cuadre la partida doble
            
           #     diferencia = abs(total_debe - total_haber)
            #    if diferencia > Decimal('0.01'):  # Tolerancia de 1 centavo
           #         messages.error(
           #             request, 
          #              f"Los totales no cuadran. Debe: ${total_debe:.2f}, Haber: ${total_haber:.2f}, Diferencia: ${diferencia:.2f}"
          #          )
          #          return self.get(request)
#
        #        # 6. Verificar que existe un período activo
       #         periodo_activo = PeriodosContables.objects.filter(estado='activo').first()
        #        if not periodo_activo:
        #            messages.error(request, "No hay un período contable activo.")
        #            return self.get(request)
            

                # 7. Crear la transacción principal
                transaccion = Transacciones.objects.create(
                    fecha=fecha,
                    descripcion=concepto,
                    numero_documento=numero_documento,
                    id_usuario_creador=request.user,
                    id_periodo=None
                )

                # 8. Guardar los detalles
                for mov in movimientos:
                    DetalleTransaccion.objects.create(
                        id_transaccion=transaccion,
                        id_cuenta_id=mov['id_cuenta'],
                        debe=mov['debe'],
                        haber=mov['haber']
                    )

                messages.success(
                    request, 
                    f"Transacción #{transaccion.id_transaccion} registrada correctamente. Total: ${total_debe:.2f}"
                )
                return redirect('transacciones')

        except ValueError as e:
            messages.error(request, f"Error en los datos ingresados: {str(e)}")
            return self.get(request)
        except Exception as e:
            messages.error(request, f"Error al registrar la transacción: {str(e)}")
            return self.get(request)