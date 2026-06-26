from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.html import format_html
from django.http import HttpResponse
from io import BytesIO
import openpyxl
import datetime

from .models import PersonaReportada, ActualizacionEstado
from .choices import EstadoPaciente, EstadoVenezolano, NacionalidadCedula, Sexo, TipoSangre
from apps.centros.models import Hospital

CAMPOS_SOLO_ADMIN = ("caso_sensible", "notas_internas")

COLUMNAS_PERSONA = [
    {"nombre": "nombre_completo", "requerido": True, "ejemplo": "María Pérez"},
    {"nombre": "cedula", "requerido": False, "ejemplo": "18485859"},
    {"nombre": "nacionalidad_cedula", "requerido": False, "ejemplo": "V"},
    {"nombre": "alias_o_apodos", "requerido": False, "ejemplo": "Marita"},
    {"nombre": "edad_aproximada", "requerido": False, "ejemplo": "37"},
    {"nombre": "sexo", "requerido": False, "ejemplo": "F"},
    {"nombre": "tipo_sangre", "requerido": False, "ejemplo": "O+"},
    {"nombre": "estado_ultima_ubicacion", "requerido": False, "ejemplo": "la_guaira"},
    {"nombre": "detalle_ultima_ubicacion", "requerido": False, "ejemplo": "Residencia Miramar"},
    {"nombre": "estado_actual", "requerido": False, "ejemplo": "hospitalizado"},
    {"nombre": "hospital_origen", "requerido": False, "ejemplo": "Hospital Militar"},
    {"nombre": "hospital_codigo", "requerido": False, "ejemplo": "HV"},
]

from apps.api.utils import _build_map, _resolve

_MAP_ESTADO_VEN = _build_map(EstadoVenezolano)
_MAP_ESTADO_PAC = _build_map(EstadoPaciente)
_MAP_NAC = _build_map(NacionalidadCedula)
_MAP_SEXO = _build_map(Sexo)
_MAP_SANGRE = _build_map(TipoSangre)


def _parse_fecha(valor):
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor if isinstance(valor, datetime.date) else valor.date()
    if valor:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.datetime.strptime(str(valor).strip(), fmt).date()
            except ValueError:
                pass
    return None


class ActualizacionEstadoInline(admin.TabularInline):
    model = ActualizacionEstado
    extra = 0
    readonly_fields = ("estado_anterior", "estado_nuevo", "notas", "fecha", "registrado_por")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PersonaReportada)
class PersonaReportadaAdmin(admin.ModelAdmin):
    list_display = (
        "id_caso",
        "nombre_completo",
        "cedula_display",
        "estado_badge",
        "hospital",
        "estado_ultima_ubicacion",
        "caso_sensible",
        "fecha_actualizacion",
    )
    list_filter = ("estado_actual", "hospital", "estado_ultima_ubicacion", "caso_sensible", "sexo")
    search_fields = ("nombre_completo", "alias_o_apodos", "id_caso", "cedula")
    readonly_fields = ("id_caso", "fecha_actualizacion")
    inlines = [ActualizacionEstadoInline]
    actions = ["exportar_csv"]
    change_list_template = "admin/personas/personareportada/change_list.html"

    fieldsets = (
        (
            "Identificación",
            {
                "fields": (
                    "id_caso",
                    "nombre_completo",
                    "alias_o_apodos",
                    "nacionalidad_cedula",
                    "cedula",
                    "edad_aproximada",
                    "sexo",
                    "tipo_sangre",
                )
            },
        ),
        (
            "Ubicación",
            {
                "fields": (
                    "estado_ultima_ubicacion",
                    "detalle_ultima_ubicacion",
                    "fecha_ultimo_contacto",
                )
            },
        ),
        (
            "Estado clínico",
            {"fields": ("hospital", "estado_actual", "hospital_origen")},
        ),
        (
            "Gestión interna",
            {
                "classes": ("collapse",),
                "fields": ("caso_sensible", "notas_internas", "fecha_actualizacion"),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "importar/",
                self.admin_site.admin_view(self.importar_view),
                name="personas_personareportada_importar",
            ),
            path(
                "plantilla-excel/",
                self.admin_site.admin_view(self.plantilla_view),
                name="personas_personareportada_plantilla",
            ),
        ] + urls

    def plantilla_view(self, request):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Personas"
        ws.append([c["nombre"] for c in COLUMNAS_PERSONA])
        ws.append([c["ejemplo"] for c in COLUMNAS_PERSONA])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        response = HttpResponse(
            buf,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="plantilla_personas.xlsx"'
        return response

    def importar_view(self, request):
        ctx = {
            **self.admin_site.each_context(request),
            "titulo": "Personas Reportadas",
            "columnas": COLUMNAS_PERSONA,
            "url_plantilla": "../plantilla-excel/",
            "creados": None,
            "errores": [],
        }

        if request.method == "POST":
            archivo = request.FILES.get("excel_file")
            if not archivo:
                ctx["errores"] = ["No se seleccionó ningún archivo."]
                return render(request, "admin/import_excel.html", ctx)

            try:
                wb = openpyxl.load_workbook(archivo, data_only=True)
                ws = wb.active
            except Exception:
                ctx["errores"] = ["El archivo no es un Excel válido (.xlsx)."]
                return render(request, "admin/import_excel.html", ctx)

            def _col(val):
                return str(val or "").strip().rstrip("*").strip()

            COLS_CONOCIDAS = {"nombre_completo", "cedula", "estado_actual"}
            fila_enc = 1
            for ri in range(1, 6):
                vals = {_col(c.value).lower() for c in ws[ri] if c.value}
                if vals & COLS_CONOCIDAS:
                    fila_enc = ri
                    break
            encabezado = [_col(c.value) for c in ws[fila_enc]]
            errores, creados = [], 0

            for i, fila in enumerate(
                ws.iter_rows(min_row=fila_enc + 1, values_only=True), start=fila_enc + 1
            ):
                if not any(fila):
                    continue
                row = dict(zip(encabezado, fila))

                nombre = str(row.get("nombre_completo", "") or "").strip()
                if not nombre:
                    errores.append(f'Fila {i}: "nombre_completo" es obligatorio.')
                    continue

                nac_raw = str(row.get("nacionalidad_cedula", "") or "").strip()
                sexo_raw = str(row.get("sexo", "") or "").strip()
                sangre_raw = str(row.get("tipo_sangre", "") or "").strip()
                ub_est_raw = str(row.get("estado_ultima_ubicacion", "") or "").strip()
                estado_p_raw = str(row.get("estado_actual", "") or "").strip()

                nac = _resolve(nac_raw, _MAP_NAC) if nac_raw else ""
                sexo = _resolve(sexo_raw, _MAP_SEXO) if sexo_raw else ""
                sangre = _resolve(sangre_raw, _MAP_SANGRE) if sangre_raw else ""
                ub_est = _resolve(ub_est_raw, _MAP_ESTADO_VEN) if ub_est_raw else ""
                estado_p = _resolve(estado_p_raw, _MAP_ESTADO_PAC) if estado_p_raw else EstadoPaciente.REPORTADO

                if nac_raw and nac is None:
                    errores.append(f'Fila {i}: nacionalidad_cedula "{nac_raw}" inválida (V, E o P).')
                    continue
                if sexo_raw and sexo is None:
                    errores.append(f'Fila {i}: sexo "{sexo_raw}" inválido.')
                    continue
                if sangre_raw and sangre is None:
                    errores.append(f'Fila {i}: tipo_sangre "{sangre_raw}" inválido.')
                    continue
                if ub_est_raw and ub_est is None:
                    errores.append(f'Fila {i}: estado_ultima_ubicacion "{ub_est_raw}" inválido.')
                    continue
                if estado_p is None:
                    errores.append(f'Fila {i}: estado_actual "{estado_p_raw}" inválido.')
                    continue

                # Hospital opcional — se asigna solo si el código existe en el catálogo
                hospital = None
                codigo_h = str(row.get("hospital_codigo", "") or "").strip().upper()
                if codigo_h:
                    try:
                        hospital = Hospital.objects.get(codigo=codigo_h)
                    except Hospital.DoesNotExist:
                        errores.append(
                            f'Fila {i}: hospital "{codigo_h}" no encontrado — se omite la asignación.'
                        )

                edad = row.get("edad_aproximada")
                try:
                    edad = int(edad) if edad not in (None, "") else None
                except (ValueError, TypeError):
                    edad = None

                try:
                    PersonaReportada.objects.create(
                        nombre_completo=nombre,
                        cedula=str(row.get("cedula", "") or "").strip(),
                        nacionalidad_cedula=nac,
                        alias_o_apodos=str(row.get("alias_o_apodos", "") or "").strip(),
                        edad_aproximada=edad,
                        sexo=sexo,
                        tipo_sangre=sangre,
                        estado_ultima_ubicacion=ub_est,
                        detalle_ultima_ubicacion=str(
                            row.get("detalle_ultima_ubicacion", "") or ""
                        ).strip(),
                        estado_actual=estado_p,
                        hospital=hospital,
                        hospital_origen=str(row.get("hospital_origen", "") or "").strip(),
                    )
                    creados += 1
                except Exception as e:
                    errores.append(f"Fila {i}: {e}")

            ctx["creados"] = creados
            ctx["errores"] = errores

        return render(request, "admin/import_excel.html", ctx)

    # ---- Permisos / campos ----

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not request.user.is_superuser:
            fields = [f for f in fields if f not in CAMPOS_SOLO_ADMIN]
        return fields

    def save_model(self, request, obj, form, change):
        if change and "estado_actual" in form.changed_data:
            estado_anterior = PersonaReportada.objects.get(pk=obj.pk).estado_actual
            super().save_model(request, obj, form, change)
            ActualizacionEstado.objects.create(
                persona=obj,
                estado_anterior=estado_anterior,
                estado_nuevo=obj.estado_actual,
                registrado_por=request.user.get_full_name() or request.user.username,
            )
        else:
            super().save_model(request, obj, form, change)

    # ---- Columnas visuales ----

    @admin.display(description="Cédula")
    def cedula_display(self, obj):
        if obj.cedula:
            return f"{obj.nacionalidad_cedula}-{obj.cedula}"
        return "—"

    @admin.display(description="Estado")
    def estado_badge(self, obj):
        colores = {
            "fallecido": "#dc2626",
            "hospitalizado_critico": "#ea580c",
            "hospitalizado": "#2563eb",
            "en_traslado": "#7c3aed",
            "localizado_con_vida": "#16a34a",
            "dado_de_alta": "#15803d",
            "en_centro_acopio": "#0891b2",
            "reportado": "#ca8a04",
            "sin_informacion": "#6b7280",
            "no_confirmado": "#9ca3af",
        }
        color = colores.get(obj.estado_actual, "#6b7280")
        label = obj.get_estado_actual_display()
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:bold">{}</span>',
            color,
            label,
        )

    # ---- Acciones ----

    @admin.action(description="Exportar selección a CSV")
    def exportar_csv(self, request, queryset):
        import csv

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="personas_reportadas.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "id_caso",
                "nombre_completo",
                "cedula",
                "estado_actual",
                "hospital",
                "estado_ultima_ubicacion",
                "fecha_actualizacion",
            ]
        )
        for p in queryset:
            writer.writerow(
                [
                    p.id_caso,
                    p.nombre_completo,
                    f"{p.nacionalidad_cedula}-{p.cedula}" if p.cedula else "",
                    p.estado_actual,
                    str(p.hospital) if p.hospital else "",
                    p.estado_ultima_ubicacion,
                    p.fecha_actualizacion,
                ]
            )
        return response


@admin.register(ActualizacionEstado)
class ActualizacionEstadoAdmin(admin.ModelAdmin):
    list_display = ("persona", "estado_anterior", "estado_nuevo", "fecha", "registrado_por")
    readonly_fields = (
        "persona",
        "estado_anterior",
        "estado_nuevo",
        "notas",
        "fecha",
        "registrado_por",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
