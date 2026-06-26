from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
import openpyxl
from io import BytesIO
from django.http import HttpResponse
from .models import Hospital
from apps.personas.choices import TipoCentro, EstadoVenezolano

COLUMNAS_HOSPITAL = [
    {'nombre': 'nombre',               'requerido': True,  'ejemplo': 'Hospital Vargas'},
    {'nombre': 'codigo',               'requerido': True,  'ejemplo': 'HV'},
    {'nombre': 'tipo',                 'requerido': True,  'ejemplo': 'hospital_publico'},
    {'nombre': 'estado',               'requerido': True,  'ejemplo': 'distrito_capital'},
    {'nombre': 'ciudad',               'requerido': True,  'ejemplo': 'Caracas'},
    {'nombre': 'direccion',            'requerido': False, 'ejemplo': 'Av. San Martín'},
    {'nombre': 'telefono_principal',   'requerido': False, 'ejemplo': '+58 212 0000000'},
    {'nombre': 'capacidad_aproximada', 'requerido': False, 'ejemplo': '200'},
]

TIPOS_VALIDOS   = {c[0] for c in TipoCentro.choices}
ESTADOS_VALIDOS = {c[0] for c in EstadoVenezolano.choices}


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display              = ('nombre', 'codigo', 'tipo', 'estado', 'ciudad', 'activo')
    list_filter               = ('tipo', 'estado', 'activo')
    search_fields             = ('nombre', 'codigo', 'ciudad')
    list_editable             = ('activo',)
    change_list_template      = 'admin/centros/hospital/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('importar/',         self.admin_site.admin_view(self.importar_view),    name='centros_hospital_importar'),
            path('plantilla-excel/',  self.admin_site.admin_view(self.plantilla_view),   name='centros_hospital_plantilla'),
        ] + urls

    def plantilla_view(self, request):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Hospitales'
        ws.append([c['nombre'] for c in COLUMNAS_HOSPITAL])
        ws.append(['Hospital Ejemplo', 'HE', 'hospital_publico', 'distrito_capital',
                   'Caracas', 'Dirección opcional', '+58 212 0000000', '150'])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        response = HttpResponse(buf, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="plantilla_hospitales.xlsx"'
        return response

    def importar_view(self, request):
        ctx = {
            **self.admin_site.each_context(request),
            'titulo':        'Hospitales / Centros',
            'columnas':      COLUMNAS_HOSPITAL,
            'url_plantilla': '../plantilla-excel/',
            'creados':       None,
            'errores':       [],
        }

        if request.method == 'POST':
            archivo = request.FILES.get('excel_file')
            if not archivo:
                ctx['errores'] = ['No se seleccionó ningún archivo.']
                return render(request, 'admin/import_excel.html', ctx)

            try:
                wb = openpyxl.load_workbook(archivo, data_only=True)
                ws = wb.active
            except Exception:
                ctx['errores'] = ['El archivo no es un Excel válido (.xlsx).']
                return render(request, 'admin/import_excel.html', ctx)

            encabezado = [str(c.value).strip() if c.value else '' for c in ws[1]]
            errores, creados = [], 0

            for i, fila in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(fila):
                    continue
                row = dict(zip(encabezado, fila))

                nombre = str(row.get('nombre', '') or '').strip()
                codigo = str(row.get('codigo', '') or '').strip().upper()
                tipo   = str(row.get('tipo',   '') or '').strip()
                estado = str(row.get('estado', '') or '').strip()
                ciudad = str(row.get('ciudad', '') or '').strip()

                if not nombre:
                    errores.append(f'Fila {i}: "nombre" es obligatorio.')
                    continue
                if not codigo:
                    errores.append(f'Fila {i}: "codigo" es obligatorio.')
                    continue
                if tipo not in TIPOS_VALIDOS:
                    errores.append(f'Fila {i}: tipo "{tipo}" no válido. Opciones: {", ".join(TIPOS_VALIDOS)}')
                    continue
                if estado not in ESTADOS_VALIDOS:
                    errores.append(f'Fila {i}: estado "{estado}" no válido.')
                    continue
                if not ciudad:
                    errores.append(f'Fila {i}: "ciudad" es obligatorio.')
                    continue

                cap = row.get('capacidad_aproximada')
                try:
                    cap = int(cap) if cap not in (None, '') else None
                except (ValueError, TypeError):
                    cap = None

                Hospital.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre':               nombre,
                        'tipo':                 tipo,
                        'estado':               estado,
                        'ciudad':               ciudad,
                        'direccion':            str(row.get('direccion') or '').strip(),
                        'telefono_principal':   str(row.get('telefono_principal') or '').strip(),
                        'capacidad_aproximada': cap,
                    }
                )
                creados += 1

            ctx['creados'] = creados
            ctx['errores'] = errores

        return render(request, 'admin/import_excel.html', ctx)
