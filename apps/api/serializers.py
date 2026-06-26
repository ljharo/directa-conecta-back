from rest_framework import serializers
from apps.personas.models import PersonaReportada
from apps.centros.models import Edificio


class PersonaReportadaSerializer(serializers.ModelSerializer):
    cedula            = serializers.SerializerMethodField()
    sexo              = serializers.SerializerMethodField()
    tipo_sangre       = serializers.SerializerMethodField()
    estado_actual     = serializers.SerializerMethodField()
    hospital          = serializers.SerializerMethodField()
    estado_ultima_ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = PersonaReportada
        fields = [
            'id_caso',
            'nombre_completo',
            'alias_o_apodos',
            'cedula',
            'edad_aproximada',
            'sexo',
            'tipo_sangre',
            'estado_actual',
            'caso_sensible',
            'hospital',
            'hospital_origen',
            'estado_ultima_ubicacion',
            'detalle_ultima_ubicacion',
            'fecha_ultimo_contacto',
            'fecha_actualizacion',
        ]

    def get_cedula(self, obj) -> str | None:
        if obj.cedula:
            return f'{obj.nacionalidad_cedula}-{obj.cedula}'
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
    count       = serializers.IntegerField()
    page        = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    next        = serializers.URLField(allow_null=True)
    previous    = serializers.URLField(allow_null=True)
    results     = PersonaReportadaSerializer(many=True)


class EdificioSerializer(serializers.ModelSerializer):
    estado_estructural = serializers.SerializerMethodField()
    estado             = serializers.SerializerMethodField()

    class Meta:
        model  = Edificio
        fields = [
            'id',
            'nombre',
            'estado',
            'ciudad',
            'direccion',
            'estado_estructural',
            'notas',
            'fecha_registro',
        ]

    def get_estado_estructural(self, obj) -> str:
        return obj.get_estado_estructural_display()

    def get_estado(self, obj) -> str:
        return obj.get_estado_display()


class EdificiosResponseSerializer(serializers.Serializer):
    count       = serializers.IntegerField()
    page        = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    next        = serializers.URLField(allow_null=True)
    previous    = serializers.URLField(allow_null=True)
    results     = EdificioSerializer(many=True)
