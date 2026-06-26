from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilHospital


class PerfilHospitalInline(admin.StackedInline):
    model               = PerfilHospital
    can_delete          = False
    verbose_name_plural = 'Hospital asignado'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilHospitalInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
