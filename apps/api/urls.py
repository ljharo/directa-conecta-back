from django.urls import path
from .views import BuscarPacienteView, EdificiosView

urlpatterns = [
    path("buscar/", BuscarPacienteView.as_view(), name="api_buscar_paciente"),
    path("edificios/", EdificiosView.as_view(), name="api_edificios"),
]
