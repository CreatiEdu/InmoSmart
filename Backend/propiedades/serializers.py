from rest_framework import serializers
from .models import Favorito, Propiedad, Turno

class PropiedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Propiedad
        fields = [
            'id_propiedad', 'titulo', 'descripcion', 'precio', 'ciudad', 'tipo_operacion',
            'habitaciones', 'baños', 'superficie', 'acepta_mascotas', 'id_tipo', 'id_estado',
            'id_Gestor', 'fecha_creacion', 'imagen_1', 'imagen_2', 'imagen_3'
        ]

class FavoritoSerializer(serializers.ModelSerializer):
    propiedad_detalle = PropiedadSerializer(source='propiedad', read_only=True)

    class Meta:
        model = Favorito
        fields = ['id_favorito', 'usuario', 'propiedad', 'propiedad_detalle']
        read_only_fields = ['id_favorito', 'usuario']

class TurnoSerializer(serializers.ModelSerializer):
    propiedad_detalle = PropiedadSerializer(source='propiedad', read_only=True)

    class Meta:
        model = Turno
        fields = ['id_turno', 'usuario', 'propiedad', 'propiedad_detalle', 'fecha_hora', 'estado', 'fecha_creacion']
        read_only_fields = ['id_turno', 'usuario', 'estado', 'fecha_creacion']