# apps/accounts/management/commands/load_initial_data.py
import os
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Carga los datos iniciales desde el archivo SQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la carga incluso si ya hay datos',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Verificar si ya hay datos (a menos que se use --force)
        if not force:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM clients_client")
                client_count = cursor.fetchone()[0]
                
                if client_count > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Ya existen {client_count} clientes en la base de datos.\n'
                            'Usa --force para recargar los datos de todos modos.'
                        )
                    )
                    return

        # Ruta al archivo SQL
        sql_file_path = os.path.join(
            settings.BASE_DIR,
            'docker',
            'init-db',
            '01-initial-data.sql'
        )

        # Verificar que el archivo existe
        if not os.path.exists(sql_file_path):
            self.stdout.write(
                self.style.ERROR(
                    f'❌ No se encontró el archivo: {sql_file_path}'
                )
            )
            return

        self.stdout.write('📂 Leyendo archivo SQL...')

        # Leer el archivo SQL
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al leer el archivo: {str(e)}')
            )
            return

        # Ejecutar el SQL
        self.stdout.write('⚙️  Ejecutando script SQL...')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_content)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Datos iniciales cargados exitosamente!')
            )
            
            # Mostrar resumen
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM clients_client")
                client_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM profiles_profile")
                profile_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM candidates_candidate")
                candidate_count = cursor.fetchone()[0]
                
            self.stdout.write('\n📊 Resumen de datos cargados:')
            self.stdout.write(f'   • Clientes: {client_count}')
            self.stdout.write(f'   • Perfiles: {profile_count}')
            self.stdout.write(f'   • Candidatos: {candidate_count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al ejecutar el script: {str(e)}')
            )
            return