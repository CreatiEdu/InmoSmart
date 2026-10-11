from django.contrib import admin
from .models import Contacto

@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'asunto', 'fecha_envio')
    list_filter = ('fecha_envio',)
    search_fields = ('nombre', 'email', 'asunto')
    ordering = ('-fecha_envio',)
