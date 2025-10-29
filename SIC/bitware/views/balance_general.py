from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@login_required
def balance_general(request):
    
    context = {
        'titulo': 'Balance General',
    }
    return render(request, 'balance_general.html')

