# bitware/backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Usuarios

class UsuariosBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Busca al usuario por nombre_usuario
            user = Usuarios.objects.get(nombre_usuario=username)
        
        except Usuarios.DoesNotExist:
            return None

        # Verifica si la contraseña coincide con el hash almacenado
        if user.contrasena_hash == password or check_password(password, user.contrasena_hash):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuarios.objects.get(pk=user_id)
        except Usuarios.DoesNotExist:
            return None