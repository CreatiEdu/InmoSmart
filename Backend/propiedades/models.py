from django.db import models

class Propiedad(models.Model):
    Tipos = [(1, 'Casa'), (2, 'Departamento'), (3, 'Local'), (4, 'Terreno')]
    Estados = [(1, 'Disponible'), (2, 'Reservado'), (3, 'En evaluacion'), (4, 'Alquilado'), (5, 'Vendido')]
    Gestores = [(1, 'Carlos Mendez'), (2, 'Laura Gimenez'), (3, 'Roberto Silva')]
    
    id_propiedad = models.AutoField(primary_key=True)
    

    titulo = models.CharField(max_length=150, verbose_name="Título de la propiedad")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    precio = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio")
    
    OPERACIONES = [("Alquiler", "Alquiler"), ("Venta", "Venta")]

    ciudad = models.CharField(max_length=100, blank=True, default="", verbose_name="Ciudad")
    tipo_operacion = models.CharField(max_length=20, choices=OPERACIONES, default="Venta", verbose_name="Tipo de operación")
    habitaciones = models.IntegerField(verbose_name="Habitaciones")
    baños = models.IntegerField(verbose_name="Baños")
    superficie = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Superficie")
    acepta_mascotas = models.BooleanField(default=False, verbose_name="¿Acepta mascotas?")
    
    id_tipo = models.IntegerField(choices=Tipos, default=1, verbose_name="Tipo de propiedad")
    id_estado = models.IntegerField(choices=Estados, default=1, verbose_name="Estado actual")
    id_Gestor = models.IntegerField(choices=Gestores, default=1, verbose_name="Gestor asignado")

    imagen_1 = models.ImageField(upload_to='propiedades/', null=True, blank=True, verbose_name="Imagen Principal (Fachada)")
    imagen_2 = models.ImageField(upload_to='propiedades/', null=True, blank=True, verbose_name="Imagen Interior 1")
    imagen_3 = models.ImageField(upload_to='propiedades/', null=True, blank=True, verbose_name="Imagen Interior 2")
    

    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de publicación")

    class Meta:
        db_table = "propiedad"

    def __str__(self):
        return self.titulo