from django.db import models
from django.contrib.auth.models import User
from apps.centros.models import Hospital


class PerfilHospital(models.Model):
    user     = models.OneToOneField(User, on_delete=models.CASCADE,
                                    related_name='perfilhospital')
    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT,
                                 null=True, blank=True,
                                 verbose_name='Hospital asignado')

    class Meta:
        verbose_name        = 'Perfil de Usuario Hospital'
        verbose_name_plural = 'Perfiles de Usuarios Hospital'

    def __str__(self):
        return f'{self.user.username} → {self.hospital}'
