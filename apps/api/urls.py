from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BuscarPacienteView, PersonaReportadaViewSet, HospitalViewSet, EdificioViewSet

router = DefaultRouter()
router.register("personas", PersonaReportadaViewSet, basename="persona")
router.register("hospitales", HospitalViewSet, basename="hospital")
router.register("edificios", EdificioViewSet, basename="edificio")

urlpatterns = [
    path("buscar/", BuscarPacienteView.as_view(), name="api_buscar_paciente"),
    path("", include(router.urls)),
]
