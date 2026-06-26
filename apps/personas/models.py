import datetime
from django.db import models
from django.core.exceptions import ValidationError
from apps.centros.models import Hospital
from .choices import (
    NacionalidadCedula, Sexo, TipoSangre, EstadoVenezolano,
    EstadoPaciente, FuenteInformacion,
)


class PersonaReportada(models.Model):
    # Identificación
    id_caso             = models.CharField('ID Caso', max_length=10, unique=True,
                                           blank=True, editable=False)
    cedula              = models.CharField('Cédula', max_length=10, blank=True,
                                           help_text='Solo números, sin puntos ni prefijo V/E')
    nacionalidad_cedula = models.CharField('Tipo cédula', max_length=2, blank=True,
                                           choices=NacionalidadCedula.choices)
    nombre_completo     = models.CharField('Nombre completo', max_length=200)
    alias_o_apodos      = models.CharField('Alias / Apodos', max_length=200, blank=True,
                                           help_text='Separados por coma')
    edad_aproximada     = models.IntegerField('Edad aproximada', null=True, blank=True)
    sexo                = models.CharField('Sexo', max_length=15, blank=True,
                                           choices=Sexo.choices)
    tipo_sangre         = models.CharField('Tipo de sangre', max_length=3, blank=True,
                                           choices=TipoSangre.choices)

    # Ubicación
    estado_ultima_ubicacion  = models.CharField('Estado (última ubicación)', max_length=30,
                                                blank=True, choices=EstadoVenezolano.choices)
    detalle_ultima_ubicacion = models.CharField('Detalle ubicación', max_length=200, blank=True,
                                                help_text='Sector, parroquia, referencia')
    fecha_ultimo_contacto   = models.DateField('Fecha último contacto',
                                               default=datetime.date.today)

    # Estado clínico
    hospital        = models.ForeignKey(Hospital, on_delete=models.PROTECT,
                                        verbose_name='Hospital / Centro')
    estado_actual   = models.CharField('Estado actual', max_length=30,
                                       choices=EstadoPaciente.choices,
                                       default=EstadoPaciente.REPORTADO)
    hospital_origen = models.CharField('Hospital de origen', max_length=200, blank=True,
                                       help_text='Si fue trasladada, centro anterior')

    # Gestión interna (solo Admin)
    fuente_informacion = models.CharField('Fuente', max_length=30, blank=True,
                                          choices=FuenteInformacion.choices)
    detalle_fuente     = models.CharField('Detalle fuente', max_length=200, blank=True)
    fecha_fuente       = models.DateField('Fecha fuente', null=True, blank=True)
    validado_por       = models.CharField('Validado por', max_length=100, blank=True)
    caso_sensible      = models.BooleanField('Caso sensible', default=False)
    notas_internas     = models.TextField('Notas internas', blank=True)

    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    class Meta:
        verbose_name        = 'Persona Reportada'
        verbose_name_plural = 'Personas Reportadas'
        ordering            = ['-fecha_actualizacion']

    def __str__(self):
        return f'{self.id_caso} — {self.nombre_completo}'

    def _generar_id_caso(self):
        ultimo = PersonaReportada.objects.order_by('-id').first()
        numero = (ultimo.pk if ultimo else 0) + 1
        return f'DC-{numero:05d}'

    def clean(self):
        if self.cedula and self.nacionalidad_cedula:
            qs = PersonaReportada.objects.filter(
                cedula=self.cedula,
                nacionalidad_cedula=self.nacionalidad_cedula,
            ).exclude(pk=self.pk)
            if qs.exists():
                caso = qs.first()
                raise ValidationError(
                    f'Ya existe un caso con esta cédula: {caso.id_caso} — {caso.nombre_completo}'
                )

    def save(self, *args, **kwargs):
        if not self.id_caso:
            self.id_caso = self._generar_id_caso()
        if self.estado_actual == EstadoPaciente.FALLECIDO:
            self.caso_sensible = True
        super().save(*args, **kwargs)


class FuenteActualizacion(models.Model):
    persona         = models.ForeignKey(PersonaReportada, on_delete=models.CASCADE,
                                        related_name='historial', verbose_name='Caso')
    estado_anterior = models.CharField('Estado anterior', max_length=30,
                                       choices=EstadoPaciente.choices, blank=True)
    estado_nuevo    = models.CharField('Estado nuevo', max_length=30,
                                       choices=EstadoPaciente.choices)
    fuente          = models.CharField('Fuente', max_length=30,
                                       choices=FuenteInformacion.choices)
    detalle         = models.CharField('Detalle', max_length=200, blank=True)
    fecha           = models.DateTimeField('Fecha', auto_now_add=True)
    registrado_por  = models.CharField('Registrado por', max_length=100)

    class Meta:
        verbose_name        = 'Actualización de Estado'
        verbose_name_plural = 'Historial de Actualizaciones'
        ordering            = ['-fecha']

    def __str__(self):
        return f'{self.persona.id_caso} | {self.estado_anterior} → {self.estado_nuevo}'
