import csv
import sys
from django.core.management.base import BaseCommand
from apps.personas.models import PersonaReportada
from apps.personas.choices import EstadoPaciente


class Command(BaseCommand):
    help = 'Exporta el knowledge source para respond.io (excluye fallecidos y casos sensibles)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Ruta del archivo de salida. Si se omite, escribe a stdout.',
        )

    def handle(self, *args, **options):
        qs = PersonaReportada.objects.filter(
            caso_sensible=False,
        ).exclude(
            estado_actual=EstadoPaciente.FALLECIDO,
        ).select_related('hospital')

        columnas = [
            'id_caso', 'nombre_completo', 'alias_o_apodos', 'edad_aproximada',
            'estado_ultima_ubicacion', 'estado_actual', 'hospital', 'fecha_actualizacion',
        ]

        output = options.get('output')
        if output:
            f = open(output, 'w', newline='', encoding='utf-8')
        else:
            f = sys.stdout

        try:
            writer = csv.writer(f)
            writer.writerow(columnas)
            for p in qs:
                writer.writerow([
                    p.id_caso,
                    p.nombre_completo,
                    p.alias_o_apodos,
                    p.edad_aproximada or '',
                    p.get_estado_ultima_ubicacion_display() if p.estado_ultima_ubicacion else '',
                    p.get_estado_actual_display(),
                    str(p.hospital),
                    p.fecha_actualizacion.strftime('%Y-%m-%d %H:%M'),
                ])
        finally:
            if output:
                f.close()

        total = qs.count()
        if output:
            self.stdout.write(self.style.SUCCESS(f'{total} registros exportados a {output}'))
        else:
            self.stderr.write(self.style.SUCCESS(f'{total} registros exportados.'))
