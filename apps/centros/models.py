from django.db import models
from apps.personas.choices import TipoCentro, EstadoVenezolano


class Hospital(models.Model):
    nombre               = models.CharField('Nombre', max_length=200)
    codigo               = models.CharField('Código', max_length=10, unique=True,
                                            help_text='Siglas cortas, ej: HV, HDL')
    tipo                 = models.CharField('Tipo', max_length=30,
                                            choices=TipoCentro.choices,
                                            default=TipoCentro.HOSPITAL_PUBLICO)
    estado               = models.CharField('Estado venezolano', max_length=30,
                                            choices=EstadoVenezolano.choices)
    ciudad               = models.CharField('Ciudad / Municipio', max_length=100)
    direccion            = models.TextField('Dirección', blank=True)
    telefono_principal   = models.CharField('Teléfono', max_length=20, blank=True)
    capacidad_aproximada = models.IntegerField('Capacidad aprox.', null=True, blank=True)
    activo               = models.BooleanField('Activo', default=True)
    fecha_registro       = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        verbose_name        = 'Hospital / Centro'
        verbose_name_plural = 'Hospitales / Centros'
        ordering            = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo})'
