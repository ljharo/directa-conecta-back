from django.contrib import admin
from django.urls import path

admin.site.site_header = 'Directa Conecta — Panel de Gestión'
admin.site.site_title = 'Directa Conecta'
admin.site.index_title = 'Sistema de Gestión de Personas Reportadas'

urlpatterns = [
    path('admin/', admin.site.urls),
]
