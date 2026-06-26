from django.contrib import admin
from django.utils.html import format_html
from .models import PersonaReportada, FuenteActualizacion
from .choices import EstadoPaciente

CAMPOS_SOLO_ADMIN = (
    'telefono_reportante', 'nombre_reportante', 'relacion_reportante',
    'canal_reportante', 'consentimiento_datos', 'fuente_informacion',
    'detalle_fuente', 'fecha_fuente', 'validado_por',
    'caso_sensible', 'notas_internas',
)


class FuenteActualizacionInline(admin.TabularInline):
    model           = FuenteActualizacion
    extra           = 0
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'fuente', 'detalle', 'fecha', 'registrado_por')
    can_delete      = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PersonaReportada)
class PersonaReportadaAdmin(admin.ModelAdmin):
    list_display    = ('id_caso', 'nombre_completo', 'cedula_display',
                       'estado_badge', 'hospital', 'estado_ultima_ubicacion',
                       'caso_sensible', 'fecha_actualizacion')
    list_filter     = ('estado_actual', 'hospital', 'estado_ultima_ubicacion',
                       'caso_sensible', 'sexo', 'fuente_informacion')
    search_fields   = ('nombre_completo', 'alias_o_apodos', 'id_caso', 'cedula')
    readonly_fields = ('id_caso', 'fecha_actualizacion')
    inlines         = [FuenteActualizacionInline]
    actions         = ['exportar_csv']

    fieldsets = (
        ('Identificación', {
            'fields': ('id_caso', 'nombre_completo', 'alias_o_apodos',
                       'nacionalidad_cedula', 'cedula', 'edad_aproximada',
                       'sexo', 'tipo_sangre')
        }),
        ('Ubicación', {
            'fields': ('estado_ultima_ubicacion', 'detalle_ultima_ubicacion',
                       'fecha_ultimo_contacto')
        }),
        ('Estado clínico', {
            'fields': ('hospital', 'estado_actual', 'hospital_origen')
        }),
        ('Reportante', {
            'classes': ('collapse',),
            'fields': ('nombre_reportante', 'relacion_reportante',
                       'telefono_reportante', 'canal_reportante', 'consentimiento_datos')
        }),
        ('Gestión interna', {
            'classes': ('collapse',),
            'fields': ('fuente_informacion', 'detalle_fuente', 'fecha_fuente',
                       'validado_por', 'caso_sensible', 'notas_internas',
                       'fecha_actualizacion')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            return qs.filter(hospital=request.user.perfilhospital.hospital)
        except Exception:
            return qs.none()

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f not in CAMPOS_SOLO_ADMIN]
        return fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and 'hospital' in form.base_fields:
            form.base_fields['hospital'].disabled = True
        if not request.user.is_superuser and 'estado_actual' in form.base_fields:
            form.base_fields['estado_actual'].choices = [
                c for c in EstadoPaciente.choices if c[0] != EstadoPaciente.FALLECIDO
            ]
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            try:
                obj.hospital = request.user.perfilhospital.hospital
            except Exception:
                pass
        if change and 'estado_actual' in form.changed_data:
            estado_anterior = PersonaReportada.objects.get(pk=obj.pk).estado_actual
            super().save_model(request, obj, form, change)
            FuenteActualizacion.objects.create(
                persona=obj,
                estado_anterior=estado_anterior,
                estado_nuevo=obj.estado_actual,
                fuente='hospital',
                registrado_por=request.user.get_full_name() or request.user.username,
            )
        else:
            super().save_model(request, obj, form, change)

    @admin.display(description='Cédula')
    def cedula_display(self, obj):
        if obj.cedula:
            return f'{obj.nacionalidad_cedula}-{obj.cedula}'
        return '—'

    @admin.display(description='Estado')
    def estado_badge(self, obj):
        colores = {
            'fallecido':             '#dc2626',
            'hospitalizado_critico': '#ea580c',
            'hospitalizado':         '#2563eb',
            'en_traslado':           '#7c3aed',
            'localizado_con_vida':   '#16a34a',
            'dado_de_alta':          '#15803d',
            'en_centro_acopio':      '#0891b2',
            'reportado':             '#ca8a04',
            'sin_informacion':       '#6b7280',
            'no_confirmado':         '#9ca3af',
        }
        color = colores.get(obj.estado_actual, '#6b7280')
        label = obj.get_estado_actual_display()
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:bold">{}</span>',
            color, label,
        )

    @admin.action(description='Exportar selección a CSV')
    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="personas_reportadas.csv"'
        writer = csv.writer(response)
        writer.writerow(['id_caso', 'nombre_completo', 'cedula', 'estado_actual',
                         'hospital', 'estado_ultima_ubicacion', 'fecha_actualizacion'])
        for p in queryset:
            writer.writerow([
                p.id_caso,
                p.nombre_completo,
                f'{p.nacionalidad_cedula}-{p.cedula}' if p.cedula else '',
                p.estado_actual,
                str(p.hospital),
                p.estado_ultima_ubicacion,
                p.fecha_actualizacion,
            ])
        return response


@admin.register(FuenteActualizacion)
class FuenteActualizacionAdmin(admin.ModelAdmin):
    list_display  = ('persona', 'estado_anterior', 'estado_nuevo', 'fuente', 'fecha', 'registrado_por')
    readonly_fields = ('persona', 'estado_anterior', 'estado_nuevo', 'fuente', 'detalle', 'fecha', 'registrado_por')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
