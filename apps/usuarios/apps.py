from django.apps import AppConfig
from django.db.models.signals import post_migrate

# Permisos que se asignan al grupo "Operador"
OPERADOR_PERMS = [
    # Hospitales y centros de ayuda
    "centros.add_hospital",
    "centros.change_hospital",
    "centros.delete_hospital",
    "centros.view_hospital",
    # Edificios
    "centros.add_edificio",
    "centros.change_edificio",
    "centros.delete_edificio",
    "centros.view_edificio",
    # Pacientes
    "personas.add_personareportada",
    "personas.change_personareportada",
    "personas.delete_personareportada",
    "personas.view_personareportada",
    # Historial de estado (solo lectura — se crea automáticamente)
    "personas.view_actualizacionestado",
]


def _crear_grupo_operador(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission

    try:
        group, _ = Group.objects.get_or_create(name="Operador")
        for perm_str in OPERADOR_PERMS:
            app_label, codename = perm_str.split(".", 1)
            try:
                perm = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename,
                )
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass
    except Exception:
        pass


class UsuariosConfig(AppConfig):
    name = "apps.usuarios"
    verbose_name = "Usuarios"

    def ready(self):
        post_migrate.connect(_crear_grupo_operador)
