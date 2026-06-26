from django.contrib import admin
from .models import Hospital


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'codigo', 'tipo', 'estado', 'ciudad', 'activo')
    list_filter   = ('tipo', 'estado', 'activo')
    search_fields = ('nombre', 'codigo', 'ciudad')
    list_editable = ('activo',)
