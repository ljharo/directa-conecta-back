from rest_framework import serializers
from apps.personas.models import PersonaReportada
from apps.centros.models import Edificio, Hospital
from apps.personas.choices import (
    EstadoVenezolano,
    EstadoPaciente,
    NacionalidadCedula,
    Sexo,
    TipoSangre,
    TipoCentro,
    EstadoEstructural,
)
from .utils import _build_map, _resolve


# ---------------------------------------------------------------------------
# Campo flexible: acepta el valor interno ("la_guaira") o el label ("La Guaira")
# ---------------------------------------------------------------------------


class FlexChoiceField(serializers.CharField):
    def __init__(self, choices_class, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_blank", True)
        self._mapping = _build_map(choices_class)
        self._display = dict(choices_class.choices)
        self._valid_values = [v for v, _ in choices_class.choices]
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        raw = super().to_internal_value(data)
        if not raw:
            return raw
        resolved = _resolve(raw, self._mapping)
        if resolved is None:
            raise serializers.ValidationError(
                f'"{raw}" no es válido. Opciones: {", ".join(self._valid_values)}'
            )
        return resolved

    def to_representation(self, value):
        return self._display.get(value, value)


# ---------------------------------------------------------------------------
# Serializers de LECTURA (respuestas GET con labels legibles)
# ---------------------------------------------------------------------------


class PersonaReportadaSerializer(serializers.ModelSerializer):
    cedula = serializers.SerializerMethodField()
    sexo = serializers.SerializerMethodField()
    tipo_sangre = serializers.SerializerMethodField()
    estado_actual = serializers.SerializerMethodField()
    hospital = serializers.SerializerMethodField()
    estado_ultima_ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = PersonaReportada
        fields = [
            "id_caso",
            "nombre_completo",
            "alias_o_apodos",
            "cedula",
            "edad_aproximada",
            "sexo",
            "tipo_sangre",
            "estado_actual",
            "caso_sensible",
            "hospital",
            "hospital_origen",
            "estado_ultima_ubicacion",
            "detalle_ultima_ubicacion",
            "fecha_ultimo_contacto",
            "fecha_actualizacion",
        ]

    def get_cedula(self, obj) -> str | None:
        if obj.cedula:
            return f"{obj.nacionalidad_cedula}-{obj.cedula}"
        return None

    def get_sexo(self, obj) -> str | None:
        return obj.get_sexo_display() if obj.sexo else None

    def get_tipo_sangre(self, obj) -> str | None:
        return obj.tipo_sangre if obj.tipo_sangre else None

    def get_estado_actual(self, obj) -> str:
        return obj.get_estado_actual_display()

    def get_hospital(self, obj) -> str | None:
        return str(obj.hospital) if obj.hospital_id else None

    def get_estado_ultima_ubicacion(self, obj) -> str | None:
        return obj.get_estado_ultima_ubicacion_display() if obj.estado_ultima_ubicacion else None


class BusquedaResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PersonaReportadaSerializer(many=True)


class EdificioSerializer(serializers.ModelSerializer):
    estado_estructural = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Edificio
        fields = [
            "id",
            "nombre",
            "estado",
            "ciudad",
            "direccion",
            "estado_estructural",
            "notas",
            "fecha_registro",
        ]

    def get_estado_estructural(self, obj) -> str:
        return obj.get_estado_estructural_display()

    def get_estado(self, obj) -> str:
        return obj.get_estado_display()


class EdificiosResponseSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EdificioSerializer(many=True)


# ---------------------------------------------------------------------------
# Serializers de ESCRITURA (POST / PATCH)
# ---------------------------------------------------------------------------


class PersonaReportadaWriteSerializer(serializers.ModelSerializer):
    hospital = serializers.SlugRelatedField(
        slug_field="codigo",
        queryset=Hospital.objects.all(),
        required=False,
        allow_null=True,
    )
    nacionalidad_cedula = FlexChoiceField(NacionalidadCedula)
    sexo = FlexChoiceField(Sexo)
    tipo_sangre = FlexChoiceField(TipoSangre)
    estado_ultima_ubicacion = FlexChoiceField(EstadoVenezolano)
    estado_actual = FlexChoiceField(EstadoPaciente, required=False, allow_blank=False)

    class Meta:
        model = PersonaReportada
        fields = [
            "nombre_completo",
            "cedula",
            "nacionalidad_cedula",
            "alias_o_apodos",
            "edad_aproximada",
            "sexo",
            "tipo_sangre",
            "estado_ultima_ubicacion",
            "detalle_ultima_ubicacion",
            "fecha_ultimo_contacto",
            "hospital",
            "estado_actual",
            "hospital_origen",
            "caso_sensible",
            "notas_internas",
        ]

    def validate(self, attrs):
        cedula = attrs.get("cedula", "")
        nac = attrs.get("nacionalidad_cedula", "")
        if cedula and nac:
            qs = PersonaReportada.objects.filter(cedula=cedula, nacionalidad_cedula=nac)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                caso = qs.first()
                raise serializers.ValidationError(
                    {
                        "cedula": f"Ya existe un caso con esta cédula: {caso.id_caso} — {caso.nombre_completo}"
                    }
                )
        return attrs


class HospitalSerializer(serializers.ModelSerializer):
    tipo = FlexChoiceField(TipoCentro, required=True, allow_blank=False)
    estado = FlexChoiceField(EstadoVenezolano, required=True, allow_blank=False)

    class Meta:
        model = Hospital
        fields = [
            "nombre",
            "codigo",
            "tipo",
            "estado",
            "ciudad",
            "direccion",
            "telefono_principal",
            "capacidad_aproximada",
            "activo",
            "fecha_registro",
        ]
        read_only_fields = ["fecha_registro"]


class EdificioWriteSerializer(serializers.ModelSerializer):
    estado = FlexChoiceField(EstadoVenezolano, required=True, allow_blank=False)
    estado_estructural = FlexChoiceField(EstadoEstructural, required=True, allow_blank=False)

    class Meta:
        model = Edificio
        fields = [
            "id",
            "nombre",
            "estado",
            "ciudad",
            "direccion",
            "estado_estructural",
            "notas",
            "fecha_registro",
        ]
        read_only_fields = ["id", "fecha_registro"]
