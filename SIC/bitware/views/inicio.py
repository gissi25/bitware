from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
@login_required
def inicio(request):
    """
    Vista principal de la aplicación
    Muestra la página de bienvenida con información sobre el sistema
    """
  
    return render(request, 'inicio.html')