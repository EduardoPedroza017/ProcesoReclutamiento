from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser(
        email='admin@example.com',
        password='admin123',
        role='director',
        first_name='Admin',
        last_name='User'
    )
    print('✓ Superusuario creado: admin@example.com / admin123')
else:
    print('⚠ El usuario admin ya existe')
