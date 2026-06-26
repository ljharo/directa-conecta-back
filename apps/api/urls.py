from django.urls import path
from .views import BuscarPacienteView

urlpatterns = [
    path('buscar/', BuscarPacienteView.as_view(), name='api_buscar_paciente'),
]
