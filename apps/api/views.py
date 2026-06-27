import math
from django.db.models import Q, ProtectedError
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from apps.personas.models import PersonaReportada, ActualizacionEstado
from apps.centros.models import Edificio, Hospital
from .serializers import (
    PersonaReportadaSerializer,
    PersonaReportadaWriteSerializer,
    BusquedaResponseSerializer,
    EdificioSerializer,
    EdificioWriteSerializer,
    EdificiosResponseSerializer,
    HospitalSerializer,
)
from .authentication import APIKeyAuthentication

PAGE_SIZE = 10


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"


# ---------------------------------------------------------------------------
# Búsqueda (endpoint legado — solo lectura, paginación custom)
# ---------------------------------------------------------------------------


class BuscarPacienteView(APIView):
    authentication_classes = [APIKeyAuthentication]

    @extend_schema(
        tags=["Pacientes"],
        summary="Buscar personas reportadas",
        description=(
            "Busca personas reportadas en el sistema por nombre, cédula, ID de caso, "
            "alias o nombre/código del hospital. La búsqueda es insensible a mayúsculas "
            "y devuelve coincidencias parciales. Resultados paginados de 10 en 10."
        ),
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Texto de búsqueda (mínimo 2 caracteres).",
                examples=[
                    OpenApiExample("Por nombre", value="Juan Pérez"),
                    OpenApiExample("Por cédula", value="12345678"),
                    OpenApiExample("Por ID caso", value="DC-00001"),
                ],
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Número de página (default: 1).",
            ),
        ],
        responses={
            200: BusquedaResponseSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request):
        q = request.query_params.get("q", "").strip()

        if q and len(q) < 2:
            return Response(
                {"error": 'El parámetro "q" debe tener al menos 2 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = PersonaReportada.objects.select_related("hospital").order_by("-fecha_actualizacion")

        if q:
            qs = qs.filter(
                Q(nombre_completo__icontains=q)
                | Q(alias_o_apodos__icontains=q)
                | Q(cedula__icontains=q)
                | Q(id_caso__icontains=q)
                | Q(hospital__nombre__icontains=q)
                | Q(hospital__codigo__icontains=q)
            )

        total = qs.count()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        page = min(page, total_pages)
        offset = (page - 1) * PAGE_SIZE
        pagina = qs[offset : offset + PAGE_SIZE]

        base_url = request.build_absolute_uri(request.path)
        next_url = f"{base_url}?q={q}&page={page + 1}" if page < total_pages else None
        prev_url = f"{base_url}?q={q}&page={page - 1}" if page > 1 else None

        serializer = PersonaReportadaSerializer(pagina, many=True)
        return Response(
            {
                "count": total,
                "page": page,
                "total_pages": total_pages,
                "next": next_url,
                "previous": prev_url,
                "results": serializer.data,
            }
        )


# ---------------------------------------------------------------------------
# CRUD ViewSets
# ---------------------------------------------------------------------------

_PERSONA_Q_PARAM = OpenApiParameter(
    "q",
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    required=False,
    description="Filtrar por nombre, cédula, alias o ID caso.",
)


@extend_schema_view(
    list=extend_schema(
        tags=["Pacientes"],
        summary="Listar todas las personas reportadas",
        parameters=[_PERSONA_Q_PARAM],
    ),
    retrieve=extend_schema(
        tags=["Pacientes"],
        summary="Obtener una persona por ID caso (ej: DC-00001)",
    ),
    create=extend_schema(
        tags=["Pacientes"],
        summary="Crear una nueva persona reportada",
        description=(
            "Crea un nuevo caso. `id_caso` se genera automáticamente (DC-XXXXX). "
            "Los campos de tipo choice aceptan tanto el valor interno (`hospitalizado`) "
            "como el label legible (`Hospitalizado — Estable`). "
            "Solo `nombre_completo` es obligatorio."
        ),
    ),
    partial_update=extend_schema(
        tags=["Pacientes"],
        summary="Actualizar campos de una persona (PATCH parcial)",
        description=(
            "Actualiza solo los campos enviados. Si cambia `estado_actual`, "
            "se registra automáticamente en el historial de actualizaciones."
        ),
    ),
    destroy=extend_schema(
        tags=["Pacientes"],
        summary="Eliminar una persona reportada",
    ),
)
class PersonaReportadaViewSet(viewsets.ModelViewSet):
    """CRUD completo para personas reportadas. Lookup por id_caso (ej: DC-00001)."""

    authentication_classes = [APIKeyAuthentication]
    pagination_class = StandardPagination
    lookup_field = "id_caso"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return PersonaReportada.objects.select_related("hospital").order_by("-fecha_actualizacion")

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PersonaReportadaSerializer
        return PersonaReportadaWriteSerializer

    def _read_response(self, instance, http_status):
        """Devuelve la respuesta usando el serializer de lectura completo."""
        serializer = PersonaReportadaSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data, status=http_status)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return self._read_response(instance, status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_estado = instance.estado_actual
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if instance.estado_actual != old_estado:
            ActualizacionEstado.objects.create(
                persona=instance,
                estado_anterior=old_estado,
                estado_nuevo=instance.estado_actual,
                registrado_por="API",
            )
        return self._read_response(instance, status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Hospitales"],
        summary="Listar hospitales y centros de ayuda",
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filtrar por nombre, código o ciudad.",
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Hospitales"],
        summary="Obtener un hospital por código (ej: HV)",
    ),
    create=extend_schema(
        tags=["Hospitales"],
        summary="Registrar un nuevo hospital o centro de ayuda",
        description=(
            "Campos obligatorios: `nombre`, `codigo` (único), `tipo`, `estado`, `ciudad`. "
            "Tipos válidos: hospital_publico, hospital_privado, clinica, centro_acopio, "
            "refugio, proteccion_civil, cruz_roja, otro."
        ),
    ),
    partial_update=extend_schema(
        tags=["Hospitales"],
        summary="Actualizar datos de un hospital (PATCH parcial)",
    ),
    destroy=extend_schema(
        tags=["Hospitales"],
        summary="Eliminar un hospital",
        description="Falla con error 409 si hay pacientes asociados al hospital.",
    ),
)
class HospitalViewSet(viewsets.ModelViewSet):
    """CRUD completo para hospitales y centros de ayuda. Lookup por codigo (ej: HV)."""

    authentication_classes = [APIKeyAuthentication]
    pagination_class = StandardPagination
    serializer_class = HospitalSerializer
    lookup_field = "codigo"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Hospital.objects.order_by("nombre")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q) | Q(ciudad__icontains=q))
        return qs

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "No se puede eliminar: hay pacientes asociados a este hospital."},
                status=status.HTTP_409_CONFLICT,
            )


@extend_schema_view(
    list=extend_schema(
        tags=["Edificios"],
        summary="Listar edificios afectados",
        parameters=[
            OpenApiParameter(
                "q",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description="Filtrar por nombre, ciudad o dirección.",
            ),
            OpenApiParameter(
                "estado_estructural",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Filtrar por estado: derrumbado, parcialmente_danado, "
                    "integridad_delicada, evacuado, en_evaluacion."
                ),
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Edificios"], summary="Obtener un edificio por ID"),
    create=extend_schema(
        tags=["Edificios"],
        summary="Registrar un edificio afectado",
        description=(
            "Estados estructurales válidos: derrumbado, parcialmente_danado, "
            "integridad_delicada, evacuado, en_evaluacion. "
            "También acepta los labels legibles (ej: 'Derrumbado')."
        ),
    ),
    partial_update=extend_schema(
        tags=["Edificios"], summary="Actualizar datos de un edificio (PATCH parcial)"
    ),
    destroy=extend_schema(tags=["Edificios"], summary="Eliminar un edificio del registro"),
)
class EdificioViewSet(viewsets.ModelViewSet):
    """CRUD completo para edificios afectados. Lookup por id numérico."""

    authentication_classes = [APIKeyAuthentication]
    pagination_class = StandardPagination
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = Edificio.objects.order_by("-fecha_registro")
        q = self.request.query_params.get("q", "").strip()
        filtro = self.request.query_params.get("estado_estructural", "").strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(ciudad__icontains=q) | Q(direccion__icontains=q)
            )
        if filtro:
            qs = qs.filter(estado_estructural=filtro)
        return qs

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return EdificioSerializer
        return EdificioWriteSerializer
