"""
Servicios para el sistema de notificaciones
Lógica de negocio para envío de notificaciones y emails
"""

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import (
    NotificationTemplate,
    Notification,
    NotificationPreference,
    EmailLog
)


class NotificationService:
    """
    Servicio principal para gestión de notificaciones
    """
    
    @staticmethod
    def create_notification(template, recipient, context=None, related_object=None):
        """
        Crear una notificación desde una plantilla
        
        Args:
            template: NotificationTemplate o nombre de plantilla (str)
            recipient: User object
            context: dict con variables para renderizar
            related_object: objeto relacionado (opcional)
        
        Returns:
            Notification object
        """
        # Si template es string, buscar la plantilla
        if isinstance(template, str):
            try:
                template = NotificationTemplate.objects.get(name=template)
            except NotificationTemplate.DoesNotExist:
                raise ValueError(f"Plantilla '{template}' no encontrada")
        
        if not template.is_active:
            raise ValueError(f"Plantilla '{template.name}' no está activa")
        
        # Verificar preferencias del usuario
        preferences, created = NotificationPreference.objects.get_or_create(
            user=recipient
        )
        
        # Verificar si el usuario quiere recibir este tipo de notificación
        if not preferences.should_notify(template.category):
            return None
        
        # Preparar contexto con valores por defecto
        default_context = {
            'user_name': recipient.get_full_name(),
            'user_email': recipient.email,
            'site_name': getattr(settings, 'SITE_NAME', 'Sistema de Reclutamiento'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        if context:
            default_context.update(context)
        
        # Renderizar contenido
        title = template.in_app_title or template.title
        message = template.render_in_app_message(default_context) if template.in_app_message else ''
        
        email_subject = ''
        email_body = ''
        
        if template.notification_type in ['email', 'both']:
            if preferences.email_notifications_enabled:
                email_subject = template.render_email_subject(default_context)
                email_body = template.render_email_body_html(default_context)
        
        # Crear notificación
        notification = Notification.objects.create(
            recipient=recipient,
            template=template,
            title=title,
            message=message,
            email_subject=email_subject,
            email_body=email_body,
            notification_type=template.notification_type,
            priority=template.priority,
            context_data=default_context,
            status='pending'
        )
        
        # Asociar objeto relacionado si existe
        if related_object:
            from django.contrib.contenttypes.models import ContentType
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = related_object.id
            notification.save()
        
        return notification
    
    @staticmethod
    def send_notification(notification):
        """
        Enviar una notificación (email y/o in-app)
        
        Args:
            notification: Notification object
        
        Returns:
            bool: True si se envió exitosamente
        """
        success = True
        
        # Enviar email si es necesario
        if notification.notification_type in ['email', 'both'] and notification.email_subject:
            email_success = NotificationService.send_email(notification)
            if not email_success:
                success = False
        
        # Marcar como enviada si todo fue bien
        if success:
            notification.mark_as_sent()
        
        return success
    
    @staticmethod
    def send_email(notification):
        """
        Enviar email de una notificación
        
        Args:
            notification: Notification object
        
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Crear el email
            email = EmailMultiAlternatives(
                subject=notification.email_subject,
                body=notification.email_body or notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.recipient.email]
            )
            
            # Agregar versión HTML si existe
            if notification.email_body:
                email.attach_alternative(notification.email_body, "text/html")
            
            # Enviar
            email.send(fail_silently=False)
            
            # Registrar en log
            email_log = EmailLog.objects.create(
                recipient=notification.recipient.email,
                subject=notification.email_subject,
                body_text=notification.message,
                body_html=notification.email_body,
                notification=notification,
                status='sent',
                sent_at=timezone.now()
            )
            
            # Actualizar notificación
            notification.email_sent = True
            notification.save(update_fields=['email_sent'])
            
            return True
            
        except Exception as e:
            # Registrar error en log
            EmailLog.objects.create(
                recipient=notification.recipient.email,
                subject=notification.email_subject,
                body_text=notification.message,
                body_html=notification.email_body,
                notification=notification,
                status='failed',
                error_message=str(e)
            )
            
            # Marcar notificación como fallida
            notification.mark_as_failed(str(e))
            
            return False
    
    @staticmethod
    def send_bulk_notification(template_name, recipient_ids, context=None):
        """
        Enviar notificaciones masivas
        
        Args:
            template_name: nombre de la plantilla
            recipient_ids: lista de IDs de usuarios
            context: dict con variables para renderizar
        
        Returns:
            dict con resultados
        """
        from apps.accounts.models import User
        
        try:
            template = NotificationTemplate.objects.get(name=template_name)
        except NotificationTemplate.DoesNotExist:
            return {
                'success': False,
                'error': 'Plantilla no encontrada',
                'created': 0,
                'sent': 0
            }
        
        created_count = 0
        sent_count = 0
        
        for user_id in recipient_ids:
            try:
                recipient = User.objects.get(id=user_id)
                
                # Crear notificación
                notification = NotificationService.create_notification(
                    template=template,
                    recipient=recipient,
                    context=context
                )
                
                if notification:
                    created_count += 1
                    
                    # Enviar
                    if NotificationService.send_notification(notification):
                        sent_count += 1
                        
            except User.DoesNotExist:
                continue
            except Exception as e:
                continue
        
        return {
            'success': True,
            'created': created_count,
            'sent': sent_count,
            'total': len(recipient_ids)
        }
    
    @staticmethod
    def notify_evaluation_assigned(evaluation, assigned_by):
        """
        Notificar cuando se asigna una evaluación
        
        Args:
            evaluation: CandidateEvaluation object
            assigned_by: User que asignó la evaluación
        """
        context = {
            'evaluation_title': evaluation.template.title,
            'evaluation_id': evaluation.id,
            'candidate_name': evaluation.candidate.full_name,
            'assigned_by_name': assigned_by.get_full_name(),
            'expires_at': evaluation.expires_at.strftime('%d/%m/%Y %H:%M') if evaluation.expires_at else 'Sin fecha límite',
            'evaluation_url': f"{settings.SITE_URL}/evaluations/{evaluation.id}/"
        }
        
        # Notificar al candidato
        notification = NotificationService.create_notification(
            template='evaluation_assigned',
            recipient=evaluation.candidate.user if hasattr(evaluation.candidate, 'user') else assigned_by,
            context=context,
            related_object=evaluation
        )
        
        if notification:
            NotificationService.send_notification(notification)
        
        return notification
    
    @staticmethod
    def notify_evaluation_completed(evaluation):
        """
        Notificar cuando se completa una evaluación
        """
        context = {
            'evaluation_title': evaluation.template.title,
            'candidate_name': evaluation.candidate.full_name,
            'final_score': evaluation.final_score,
            'passed': 'Aprobada' if evaluation.passed else 'No aprobada',
            'evaluation_url': f"{settings.SITE_URL}/evaluations/{evaluation.id}/"
        }
        
        # Notificar al que asignó la evaluación
        if evaluation.assigned_by:
            notification = NotificationService.create_notification(
                template='evaluation_completed',
                recipient=evaluation.assigned_by,
                context=context,
                related_object=evaluation
            )
            
            if notification:
                NotificationService.send_notification(notification)
        
        return notification
    
    @staticmethod
    def notify_evaluation_reviewed(evaluation, reviewer):
        """
        Notificar cuando se revisa una evaluación
        """
        context = {
            'evaluation_title': evaluation.template.title,
            'candidate_name': evaluation.candidate.full_name,
            'reviewer_name': reviewer.get_full_name(),
            'final_score': evaluation.final_score,
            'passed': 'Aprobada' if evaluation.passed else 'No aprobada',
            'evaluator_comments': evaluation.evaluator_comments,
            'evaluation_url': f"{settings.SITE_URL}/evaluations/{evaluation.id}/"
        }
        
        # Notificar al candidato (si tiene usuario)
        if hasattr(evaluation.candidate, 'user'):
            notification = NotificationService.create_notification(
                template='evaluation_reviewed',
                recipient=evaluation.candidate.user,
                context=context,
                related_object=evaluation
            )
            
            if notification:
                NotificationService.send_notification(notification)
        
        return notification


class EmailTemplateService:
    """
    Servicio para renderizar plantillas de email HTML
    """
    
    @staticmethod
    def render_template(template_name, context):
        """
        Renderizar una plantilla de email
        
        Args:
            template_name: nombre del archivo de plantilla
            context: dict con variables
        
        Returns:
            str: HTML renderizado
        """
        return render_to_string(f'notifications/emails/{template_name}.html', context)
    
    @staticmethod
    def get_base_context():
        """
        Obtener contexto base para todas las plantillas
        """
        return {
            'site_name': getattr(settings, 'SITE_NAME', 'Sistema de Reclutamiento'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'year': timezone.now().year
        }