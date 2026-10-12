from rest_framework import serializers
from .models import Propiedad

class PropiedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propiedad
        fields = ['id_propiedad', 'titulo', 'descripcion', 'precio', 'ciudad', 'tipo_operacion',
          'habitaciones', 'baños', 'superficie', 'acepta_mascotas', 'id_tipo', 'id_estado',
           'id_Gestor', 'fecha_creacion', 'imagen_1', 'imagen_2', 'imagen_3']