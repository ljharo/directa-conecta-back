import math
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.personas.models import PersonaReportada
from apps.centros.models import Edificio
from .serializers import PersonaReportadaSerializer, BusquedaResponseSerializer, EdificioSerializer, EdificiosResponseSerializer
from .authentication import APIKeyAuthentication

PAGE_SIZE = 10


class BuscarPacienteView(APIView):
    authentication_classes = [APIKeyAuthentication]

    @extend_schema(
        tags=['Pacientes'],
        summary='Buscar personas reportadas',
        description=(
            'Busca personas reportadas en el sistema por nombre, cédula, ID de caso, '
            'alias o nombre/código del hospital. La búsqueda es insensible a mayúsculas '
            'y devuelve coincidencias parciales. Resultados paginados de 10 en 10.'
        ),
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Texto de búsqueda (mínimo 2 caracteres). Busca en: nombre completo, alias, cédula, ID caso, nombre y código del hospital.',
                examples=[
                    OpenApiExample('Por nombre',   value='Juan Pérez'),
                    OpenApiExample('Por cédula',   value='12345678'),
                    OpenApiExample('Por ID caso',  value='DC-00001'),
                    OpenApiExample('Por hospital', value='Hospital Vargas'),
                ],
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Número de página (default: 1).',
            ),
        ],
        responses={
            200: BusquedaResponseSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    'count': 1,
                    'page': 1,
                    'total_pages': 1,
                    'next': None,
                    'previous': None,
                    'results': [{
                        'id_caso': 'DC-00001',
                        'nombre_completo': 'Juan Pérez',
                        'alias_o_apodos': 'Juanito',
                        'cedula': 'V-12345678',
                        'edad_aproximada': 35,
                        'sexo': 'Masculino',
                        'tipo_sangre': 'O+',
                        'estado_actual': 'Hospitalizado — Estable',
                        'caso_sensible': False,
                        'hospital': 'Hospital Vargas (HV)',
                        'hospital_origen': '',
                        'estado_ultima_ubicacion': 'Distrito Capital',
                        'detalle_ultima_ubicacion': 'El Valle',
                        'fecha_ultimo_contacto': '2026-06-26',
                        'fecha_actualizacion': '2026-06-26T14:30:00',
                    }],
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Error — q con solo 1 caracter',
                value={'error': 'El parámetro "q" debe tener al menos 2 caracteres.'},
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Error — sin autenticación',
                value={'detail': 'API key requerida. Header: Authorization: Bearer <key>'},
                response_only=True,
                status_codes=['401'],
            ),
        ],
    )
    def get(self, request):
        q = request.query_params.get('q', '').strip()

        if q and len(q) < 2:
            return Response(
                {'error': 'El parámetro "q" debe tener al menos 2 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = PersonaReportada.objects.select_related('hospital').order_by('-fecha_actualizacion')

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
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1

        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        page = min(page, total_pages)
        offset = (page - 1) * PAGE_SIZE
        pagina = qs[offset: offset + PAGE_SIZE]

        base_url = request.build_absolute_uri(request.path)
        next_url = f'{base_url}?q={q}&page={page + 1}' if page < total_pages else None
        prev_url = f'{base_url}?q={q}&page={page - 1}' if page > 1 else None

        serializer = PersonaReportadaSerializer(pagina, many=True)
        return Response({
            'count':       total,
            'page':        page,
            'total_pages': total_pages,
            'next':        next_url,
            'previous':    prev_url,
            'results':     serializer.data,
        })


class EdificiosView(APIView):
    authentication_classes = [APIKeyAuthentication]

    @extend_schema(
        tags=['Edificios'],
        summary='Listar edificios afectados',
        description=(
            'Devuelve el listado de edificios colapsados o con integridad estructural comprometida. '
            'Opcionalmente filtra por estado estructural o busca por texto. '
            'Resultados paginados de 10 en 10.'
        ),
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Búsqueda parcial por nombre, ciudad o dirección.',
            ),
            OpenApiParameter(
                name='estado_estructural',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    'Filtrar por estado estructural. Valores: '
                    'derrumbado, parcialmente_danado, integridad_delicada, evacuado, en_evaluacion'
                ),
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Número de página (default: 1).',
            ),
        ],
        responses={200: EdificiosResponseSerializer, 401: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        q                 = request.query_params.get('q', '').strip()
        filtro_estructural = request.query_params.get('estado_estructural', '').strip()

        qs = Edificio.objects.order_by('-fecha_registro')

        if q:
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(ciudad__icontains=q)
                | Q(direccion__icontains=q)
            )

        if filtro_estructural:
            qs = qs.filter(estado_estructural=filtro_estructural)

        total = qs.count()

        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1

        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        page        = min(page, total_pages)
        offset      = (page - 1) * PAGE_SIZE
        pagina      = qs[offset: offset + PAGE_SIZE]

        base_url = request.build_absolute_uri(request.path)
        qs_extra = f'&q={q}' if q else ''
        qs_extra += f'&estado_estructural={filtro_estructural}' if filtro_estructural else ''
        next_url = f'{base_url}?page={page + 1}{qs_extra}' if page < total_pages else None
        prev_url = f'{base_url}?page={page - 1}{qs_extra}' if page > 1 else None

        serializer = EdificioSerializer(pagina, many=True)
        return Response({
            'count':       total,
            'page':        page,
            'total_pages': total_pages,
            'next':        next_url,
            'previous':    prev_url,
            'results':     serializer.data,
        })
