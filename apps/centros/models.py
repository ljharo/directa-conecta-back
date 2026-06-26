from django.db import models
from apps.personas.choices import TipoCentro, EstadoVenezolano, EstadoEstructural


class Hospital(models.Model):
    nombre = models.CharField("Nombre", max_length=200)
    codigo = models.CharField(
        "Código", max_length=10, unique=True, help_text="Siglas cortas, ej: HV, HDL"
    )
    tipo = models.CharField(
        "Tipo",
        max_length=30,
        choices=TipoCentro.choices,
        default=TipoCentro.HOSPITAL_PUBLICO,
    )
    estado = models.CharField("Estado venezolano", max_length=30, choices=EstadoVenezolano.choices)
    ciudad = models.CharField("Ciudad / Municipio", max_length=100)
    direccion = models.TextField("Dirección", blank=True)
    telefono_principal = models.CharField("Teléfono", max_length=20, blank=True)
    capacidad_aproximada = models.IntegerField("Capacidad aprox.", null=True, blank=True)
    activo = models.BooleanField("Activo", default=True)
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)

    class Meta:
        verbose_name = "Hospital / Centro"
        verbose_name_plural = "Hospitales / Centros"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Edificio(models.Model):
    nombre = models.CharField("Nombre del edificio", max_length=200)
    estado = models.CharField("Estado venezolano", max_length=30, choices=EstadoVenezolano.choices)
    ciudad = models.CharField("Ciudad / Municipio", max_length=100)
    direccion = models.TextField("Dirección")
    estado_estructural = models.CharField(
        "Estado estructural",
        max_length=30,
        choices=EstadoEstructural.choices,
        default=EstadoEstructural.EN_EVALUACION,
    )
    notas = models.TextField("Notas / Observaciones", blank=True)
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)

    class Meta:
        verbose_name = "Edificio afectado"
        verbose_name_plural = "Edificios afectados"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.nombre} — {self.get_estado_estructural_display()}"
