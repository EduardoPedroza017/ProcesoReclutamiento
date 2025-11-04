"""
URLs para el sistema de notificaciones
Define los endpoints de la API REST
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationTemplateViewSet,
    NotificationViewSet,
    NotificationPreferenceViewSet,
    EmailLogViewSet
)

# Crear router para registrar los viewsets
router = DefaultRouter()

# Registrar viewsets con sus prefijos
router.register(r'templates', NotificationTemplateViewSet, basename='template')
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='preference')
router.register(r'email-logs', EmailLogViewSet, basename='email-log')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
]

"""
ENDPOINTS DISPONIBLES:

═══════════════════════════════════════════════════════════════════
PLANTILLAS DE NOTIFICACIÓN (Templates)
═══════════════════════════════════════════════════════════════════
GET     /api/notifications/templates/                    - Listar plantillas
POST    /api/notifications/templates/                    - Crear plantilla
GET     /api/notifications/templates/{id}/               - Detalle de plantilla
PUT     /api/notifications/templates/{id}/               - Actualizar plantilla
PATCH   /api/notifications/templates/{id}/               - Actualización parcial
DELETE  /api/notifications/templates/{id}/               - Eliminar plantilla

Acciones especiales:
POST    /api/notifications/templates/{id}/duplicate/     - Duplicar plantilla
POST    /api/notifications/templates/{id}/test/          - Probar plantilla

═══════════════════════════════════════════════════════════════════
NOTIFICACIONES (Notifications)
═══════════════════════════════════════════════════════════════════
GET     /api/notifications/                              - Listar notificaciones
POST    /api/notifications/                              - Crear notificación
GET     /api/notifications/{id}/                         - Detalle de notificación
DELETE  /api/notifications/{id}/                         - Eliminar notificación

Acciones especiales:
GET     /api/notifications/unread/                       - Solo no leídas
POST    /api/notifications/{id}/mark_as_read/            - Marcar como leída
POST    /api/notifications/mark_all_as_read/             - Marcar todas como leídas
POST    /api/notifications/send_bulk/                    - Envío masivo (Director+)
GET     /api/notifications/statistics/                   - Estadísticas del usuario
DELETE  /api/notifications/clear_read/                   - Limpiar leídas

═══════════════════════════════════════════════════════════════════
PREFERENCIAS (Preferences)
═══════════════════════════════════════════════════════════════════
GET     /api/notifications/preferences/                  - Listar preferencias
GET     /api/notifications/preferences/{id}/             - Detalle de preferencia
PUT     /api/notifications/preferences/{id}/             - Actualizar preferencia
PATCH   /api/notifications/preferences/{id}/             - Actualización parcial

Acciones especiales:
GET     /api/notifications/preferences/my_preferences/   - Mis preferencias
PUT     /api/notifications/preferences/my_preferences/   - Actualizar mis preferencias
PATCH   /api/notifications/preferences/my_preferences/   - Actualización parcial

═══════════════════════════════════════════════════════════════════
LOGS DE EMAIL (Email Logs) - Solo Lectura
═══════════════════════════════════════════════════════════════════
GET     /api/notifications/email-logs/                   - Listar logs
GET     /api/notifications/email-logs/{id}/              - Detalle de log

═══════════════════════════════════════════════════════════════════
PARÁMETROS DE FILTRADO DISPONIBLES
═══════════════════════════════════════════════════════════════════

Templates:
    ?category=evaluation                - Filtrar por categoría
    ?notification_type=email            - Por tipo
    ?is_active=true                     - Solo activas
    ?priority=high                      - Por prioridad
    ?search=evaluación                  - Buscar en nombre/título

Notifications:
    ?status=unread                      - Por estado
    ?notification_type=in_app           - Por tipo
    ?priority=urgent                    - Por prioridad
    ?search=evaluación                  - Buscar en título/mensaje

Email Logs:
    ?status=sent                        - Por estado
    ?recipient=user@example.com         - Por destinatario
    ?search=evaluation                  - Buscar en asunto

═══════════════════════════════════════════════════════════════════
EJEMPLOS DE USO
═══════════════════════════════════════════════════════════════════

1. Crear una plantilla de notificación:
POST /api/notifications/templates/
{
    "name": "evaluation_assigned",
    "title": "Nueva evaluación asignada",
    "category": "evaluation",
    "notification_type": "both",
    "email_subject": "Se te ha asignado una nueva evaluación",
    "email_body_html": "<p>Hola {user_name}, tienes una nueva evaluación: {evaluation_title}</p>",
    "in_app_title": "Nueva evaluación",
    "in_app_message": "Se te ha asignado: {evaluation_title}",
    "available_variables": ["user_name", "evaluation_title", "expires_at"]
}

2. Enviar notificación a un usuario:
POST /api/notifications/
{
    "template_name": "evaluation_assigned",
    "recipient_id": 5,
    "context": {
        "evaluation_title": "Evaluación Python Senior",
        "expires_at": "2025-11-10"
    },
    "send_immediately": true
}

3. Enviar notificaciones masivas:
POST /api/notifications/send_bulk/
{
    "template_name": "system_announcement",
    "recipient_ids": [1, 2, 3, 4, 5],
    "context": {
        "announcement": "El sistema estará en mantenimiento..."
    },
    "send_immediately": false
}

4. Obtener notificaciones no leídas:
GET /api/notifications/unread/

5. Marcar notificación como leída:
POST /api/notifications/1/mark_as_read/

6. Marcar todas como leídas:
POST /api/notifications/mark_all_as_read/

7. Obtener preferencias del usuario actual:
GET /api/notifications/preferences/my_preferences/

8. Actualizar preferencias:
PUT /api/notifications/preferences/my_preferences/
{
    "email_notifications_enabled": true,
    "in_app_notifications_enabled": true,
    "notify_evaluations": true,
    "notify_reminders": false,
    "digest_enabled": true,
    "digest_time": "08:00:00"
}

9. Ver estadísticas de notificaciones:
GET /api/notifications/statistics/

10. Limpiar notificaciones leídas:
DELETE /api/notifications/clear_read/

11. Ver logs de emails enviados:
GET /api/notifications/email-logs/

12. Filtrar notificaciones urgentes no leídas:
GET /api/notifications/?priority=urgent&status=pending

═══════════════════════════════════════════════════════════════════
USO PROGRAMÁTICO (desde el código)
═══════════════════════════════════════════════════════════════════

# Crear y enviar notificación desde código Python:
from apps.notifications.services import NotificationService

# Notificar evaluación asignada
notification = NotificationService.notify_evaluation_assigned(
    evaluation=evaluation_obj,
    assigned_by=user_obj
)

# Notificar evaluación completada
notification = NotificationService.notify_evaluation_completed(
    evaluation=evaluation_obj
)

# Notificar evaluación revisada
notification = NotificationService.notify_evaluation_reviewed(
    evaluation=evaluation_obj,
    reviewer=user_obj
)

# Envío masivo
result = NotificationService.send_bulk_notification(
    template_name='system_update',
    recipient_ids=[1, 2, 3],
    context={'message': 'Nueva actualización disponible'}
)

═══════════════════════════════════════════════════════════════════
TAREAS ASÍNCRONAS (Celery)
═══════════════════════════════════════════════════════════════════

# Enviar notificación de forma asíncrona:
from apps.notifications.tasks import send_notification_task
send_notification_task.delay(notification_id)

# Envío masivo asíncrono:
from apps.notifications.tasks import send_bulk_notifications_task
send_bulk_notifications_task.delay(
    template_name='announcement',
    recipient_ids=[1, 2, 3],
    context={'message': 'Texto del anuncio'}
)

# Enviar recordatorio de evaluación:
from apps.notifications.tasks import send_evaluation_reminder_task
send_evaluation_reminder_task.delay(evaluation_id)

═══════════════════════════════════════════════════════════════════
CONFIGURACIÓN REQUERIDA EN settings.py
═══════════════════════════════════════════════════════════════════

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña'
DEFAULT_FROM_EMAIL = 'Sistema de Reclutamiento <noreply@tudominio.com>'

# Site settings
SITE_NAME = 'Sistema de Reclutamiento'
SITE_URL = 'http://localhost:8000'
SUPPORT_EMAIL = 'soporte@tudominio.com'

# Celery settings (opcional, para tareas asíncronas)
CELERY_BEAT_SCHEDULE = {
    'send-daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digest_task',
        'schedule': crontab(hour=8, minute=0),
    },
    'clean-old-notifications': {
        'task': 'apps.notifications.tasks.clean_old_notifications_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),
    },
    'process-expired-notifications': {
        'task': 'apps.notifications.tasks.process_expired_notifications_task',
        'schedule': crontab(minute='*/30'),
    },
}
"""