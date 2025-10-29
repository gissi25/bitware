from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
@login_required
def estado_resultados(request):
    """
    Vista para mostrar el estado de resultados
    """
    
    return render(request, 'estado_resultados.html')
