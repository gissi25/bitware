from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
@login_required
def costeo(request):
   
   
    return render(request, 'costeo.html')
