from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Solo el superusuario puede gestionar usuarios desde el Admin."""

    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
