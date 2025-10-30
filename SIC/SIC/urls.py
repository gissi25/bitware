"""
URL configuration for SIC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bitware import views

from django.conf import settings
from django.conf.urls.static import static
from bitware.views.catalogo_cuentas import CatalogoCuentasView
from bitware.views.cuentas_t import CuentasT
from bitware.views.transacciones import transacciones
<<<<<<< Updated upstream
=======
from bitware.views.costeo import CosteoABC
from bitware.views import costeo
>>>>>>> Stashed changes



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),

    # Rutas del menú
    path('transacciones/', transacciones.as_view() , name='transacciones'),
<<<<<<< Updated upstream
    path('costeo/', views.costeo, name='costeo'),
=======
    path('costeo/', CosteoABC.as_view(), name='costeo_abc'),
    path('api/calcular-preview/', costeo.calcular_preview_costo, name='api_calcular_preview'),
>>>>>>> Stashed changes
    path('catalogo-cuentas/', CatalogoCuentasView.as_view(), name='catalogo_cuentas'),
    path('cuentas-t/', CuentasT.as_view(), name='cuentas_t'),
    path('balance-general/', views.balance_general, name='balance_general'),
    path('estado-resultados/', views.estado_resultados, name='estado_resultados'),
    
    
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)