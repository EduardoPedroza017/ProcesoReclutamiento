"""
Configuración de Celery para tareas asíncronas
"""
import os
from celery import Celery
from celery.schedules import crontab

# Configurar el módulo de settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('recruitment')

# Usar una string para el namespace de configuración
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar tareas de todas las apps registradas
app.autodiscover_tasks()

# Configurar tareas programadas (Beat)
app.conf.beat_schedule = {
    # Ejemplo: Enviar resumen diario a las 9 AM
    'send-daily-summary': {
        'task': 'apps.notifications.tasks.send_daily_summary',
        'schedule': crontab(hour=9, minute=0),
    },
    # Ejemplo: Verificar perfiles pendientes cada hora
    'check-pending-profiles': {
        'task': 'apps.profiles.tasks.check_pending_profiles',
        'schedule': crontab(minute=0),  # Cada hora
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de prueba para verificar que Celery funciona"""
    print(f'Request: {self.request!r}')