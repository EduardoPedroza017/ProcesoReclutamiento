"""
Comando para crear usuarios de prueba en el sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuarios de prueba para cada rol del sistema'
    
    def handle(self, *args, **options):
        """Crear usuarios de prueba"""
        
        users_data = [
            {
                'email': 'admin@empresa.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'director@empresa.com', 
                'password': 'admin123',
                'first_name': 'Director',
                'last_name': 'Recursos Humanos',
                'role': 'director',
                'is_staff': True,
            },
            {
                'email': 'supervisor@empresa.com',
                'password': 'admin123', 
                'first_name': 'Supervisor',
                'last_name': 'Reclutamiento',
                'role': 'supervisor',
            }
        ]
        
        created_count = 0
        
        for user_data in users_data:
            email = user_data['email']
            
            # Verificar si el usuario ya existe
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'Usuario {email} ya existe, omitiendo...')
                )
                continue
            
            # Crear el usuario
            password = user_data.pop('password')
            user = User.objects.create(**user_data)
            user.set_password(password)
            user.save()
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario creado: {email} (Rol: {user.get_role_display()})')
            )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n¡Éxito! Se crearon {created_count} usuarios de prueba.')
            )
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.WARNING('CREDENCIALES DE PRUEBA:'))
            self.stdout.write('='*50)
            
            for user_data in users_data:
                # Reconstruir los datos para mostrar
                user = User.objects.get(email=user_data['email'])
                self.stdout.write(f'{user.get_role_display()}:')
                self.stdout.write(f'  Email: {user.email}')
                self.stdout.write(f'  Contraseña: admin123')
                self.stdout.write('')
                
        else:
            self.stdout.write(
                self.style.WARNING('No se crearon usuarios nuevos.')
            )