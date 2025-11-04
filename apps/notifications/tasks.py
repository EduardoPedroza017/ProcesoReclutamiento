"""
Tareas asíncronas de Celery para el sistema de notificaciones
Maneja el envío de notificaciones en segundo plano
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3)
def send_notification_task(self, notification_id):
    """
    Tarea para enviar una notificación de forma asíncrona
    
    Args:
        notification_id: ID de la notificación a enviar
    """
    from .models import Notification
    from .services import NotificationService
    
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Enviar notificación
        success = NotificationService.send_notification(notification)
        
        if not success:
            # Reintentar si falla
            raise Exception("Error al enviar notificación")
        
        return f"Notificación {notification_id} enviada exitosamente"
        
    except Notification.DoesNotExist:
        return f"Notificación {notification_id} no encontrada"
        
    except Exception as exc:
        # Reintentar con backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_bulk_notifications_task(template_name, recipient_ids, context=None):
    """
    Tarea para enviar notificaciones masivas de forma asíncrona
    
    Args:
        template_name: nombre de la plantilla
        recipient_ids: lista de IDs de usuarios
        context: dict con variables para renderizar
    """
    from .services import NotificationService
    
    result = NotificationService.send_bulk_notification(
        template_name=template_name,
        recipient_ids=recipient_ids,
        context=context or {}
    )
    
    return result


@shared_task
def send_daily_digest_task():
    """
    Tarea programada para enviar resúmenes diarios de notificaciones
    Se ejecuta una vez al día
    """
    from .models import NotificationPreference, Notification
    from apps.accounts.models import User
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    
    # Obtener usuarios con resumen diario habilitado
    preferences = NotificationPreference.objects.filter(
        digest_enabled=True,
        email_notifications_enabled=True
    )
    
    sent_count = 0
    
    for pref in preferences:
        user = pref.user
        
        # Obtener notificaciones no leídas de las últimas 24 horas
        yesterday = timezone.now() - timedelta(days=1)
        unread_notifications = Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
            created_at__gte=yesterday
        ).order_by('-priority', '-created_at')
        
        if not unread_notifications.exists():
            continue
        
        # Preparar email
        context = {
            'user_name': user.get_full_name(),
            'notifications': unread_notifications,
            'notification_count': unread_notifications.count(),
            'site_name': getattr(settings, 'SITE_NAME', 'Sistema de Reclutamiento'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
        }
        
        # Renderizar plantilla
        from django.template.loader import render_to_string
        html_content = render_to_string('notifications/emails/daily_digest.html', context)
        text_content = f"Tienes {unread_notifications.count()} notificaciones sin leer."
        
        # Enviar email
        try:
            email = EmailMultiAlternatives(
                subject=f"Resumen diario - {unread_notifications.count()} notificaciones",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            sent_count += 1
            
        except Exception as e:
            print(f"Error enviando resumen a {user.email}: {e}")
            continue
    
    return f"Resúmenes enviados: {sent_count}"


@shared_task
def clean_old_notifications_task():
    """
    Tarea programada para limpiar notificaciones antiguas leídas
    Se ejecuta semanalmente
    """
    from .models import Notification
    
    # Eliminar notificaciones leídas de más de 30 días
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted = Notification.objects.filter(
        read_at__isnull=False,
        read_at__lt=cutoff_date
    ).delete()
    
    return f"Notificaciones eliminadas: {deleted[0]}"


@shared_task
def process_expired_notifications_task():
    """
    Tarea programada para procesar notificaciones expiradas
    Marca como expiradas las notificaciones que pasaron su fecha límite
    """
    from .models import Notification
    
    updated = Notification.objects.filter(
        expires_at__lt=timezone.now(),
        status__in=['pending', 'sent']
    ).update(status='read')
    
    return f"Notificaciones expiradas procesadas: {updated}"


@shared_task
def retry_failed_notifications_task():
    """
    Tarea programada para reintentar envío de notificaciones fallidas
    Se ejecuta cada hora
    """
    from .models import Notification
    from .services import NotificationService
    
    # Obtener notificaciones fallidas de las últimas 24 horas
    yesterday = timezone.now() - timedelta(days=1)
    failed_notifications = Notification.objects.filter(
        status='failed',
        created_at__gte=yesterday
    )[:50]  # Limitar a 50 para no sobrecargar
    
    retried = 0
    success = 0
    
    for notification in failed_notifications:
        try:
            if NotificationService.send_notification(notification):
                success += 1
            retried += 1
        except Exception:
            continue
    
    return f"Reintentos: {retried}, Exitosos: {success}"


@shared_task
def send_evaluation_reminder_task(evaluation_id):
    """
    Tarea para enviar recordatorio de evaluación pendiente
    
    Args:
        evaluation_id: ID de la evaluación
    """
    from apps.evaluations.models import CandidateEvaluation
    from .services import NotificationService
    from django.conf import settings
    
    try:
        evaluation = CandidateEvaluation.objects.get(id=evaluation_id)
        
        # Solo enviar si está pendiente o en progreso
        if evaluation.status not in ['pending', 'in_progress']:
            return "Evaluación ya completada"
        
        # Verificar si no ha expirado
        if evaluation.expires_at and evaluation.expires_at < timezone.now():
            return "Evaluación expirada"
        
        context = {
            'evaluation_title': evaluation.template.title,
            'candidate_name': evaluation.candidate.full_name,
            'expires_at': evaluation.expires_at.strftime('%d/%m/%Y %H:%M') if evaluation.expires_at else 'Sin fecha límite',
            'evaluation_url': f"{settings.SITE_URL}/evaluations/{evaluation.id}/"
        }
        
        # Crear y enviar notificación
        if hasattr(evaluation.candidate, 'user'):
            notification = NotificationService.create_notification(
                template='evaluation_reminder',
                recipient=evaluation.candidate.user,
                context=context,
                related_object=evaluation
            )
            
            if notification:
                NotificationService.send_notification(notification)
                return "Recordatorio enviado"
        
        return "Candidato sin usuario asociado"
        
    except CandidateEvaluation.DoesNotExist:
        return "Evaluación no encontrada"


@shared_task
def send_evaluation_expiring_soon_task():
    """
    Tarea programada para enviar recordatorios de evaluaciones que expiran pronto
    Se ejecuta diariamente
    """
    from apps.evaluations.models import CandidateEvaluation
    
    # Obtener evaluaciones que expiran en las próximas 24 horas
    tomorrow = timezone.now() + timedelta(days=1)
    expiring_evaluations = CandidateEvaluation.objects.filter(
        status__in=['pending', 'in_progress'],
        expires_at__lte=tomorrow,
        expires_at__gte=timezone.now()
    )
    
    sent_count = 0
    
    for evaluation in expiring_evaluations:
        send_evaluation_reminder_task.delay(evaluation.id)
        sent_count += 1
    
    return f"Recordatorios programados: {sent_count}"