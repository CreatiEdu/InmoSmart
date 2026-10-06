from django.db import models

class Usuario(models.Model):
    
    ROLES = (
       (1,'CLIENTE'),
       (2,'GESTOR'),
       (3,'ADMINISTRADOR'),
    )

    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    dni= models.CharField(max_length=9,unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    rol = models.IntegerField(choices=ROLES, default=1, db_column='id_rol')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    class Meta:
        db_table = "Usuarios"

    def __str__(self):
        return self.nombre
