"""
Configuración del panel de administración para el sistema de notificaciones
Permite gestionar notificaciones, plantillas y preferencias desde el admin de Django
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    NotificationTemplate,
    Notification,
    NotificationPreference,
    EmailLog
)


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """
    Administración de plantillas de notificación
    """
    list_display = [
        'name',
        'title',
        'category_badge',
        'notification_type_badge',
        'priority_badge',
        'is_active_badge',
        'usage_count',
        'created_at'
    ]
    list_filter = [
        'category',
        'notification_type',
        'is_active',
        'priority',
        'created_at'
    ]
    search_fields = [
        'name',
        'title',
        'description',
        'email_subject'
    ]
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at',
        'usage_count',
        'last_used'
    ]
    fieldsets = (
        ('Información General', {
            'fields': (
                'name',
                'title',
                'description',
                'category',
                'notification_type',
                'priority'
            )
        }),
        ('Contenido de Email', {
            'fields': (
                'email_subject',
                'email_body_html',
                'email_body_text'
            )
        }),
        ('Contenido en App', {
            'fields': (
                'in_app_title',
                'in_app_message'
            )
        }),
        ('Configuración', {
            'fields': (
                'is_active',
                'available_variables'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
                'usage_count',
                'last_used'
            ),
            'classes': ('collapse',)
        })
    )
    actions = ['duplicate_templates', 'activate_templates', 'deactivate_templates']
    
    def save_model(self, request, obj, form, change):
        """Asignar el usuario actual como creador si es nuevo"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def category_badge(self, obj):
        """Badge con color para la categoría"""
        colors = {
            'evaluation': '#3498db',
            'candidate': '#2ecc71',
            'profile': '#9b59b6',
            'system': '#34495e',
            'reminder': '#f39c12',
            'alert': '#e74c3c'
        }
        color = colors.get(obj.category, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Categoría'
    
    def notification_type_badge(self, obj):
        """Badge para el tipo de notificación"""
        colors = {
            'email': '#3498db',
            'in_app': '#2ecc71',
            'both': '#9b59b6'
        }
        color = colors.get(obj.notification_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Tipo'
    
    def priority_badge(self, obj):
        """Badge para la prioridad"""
        colors = {
            'low': '#95a5a6',
            'normal': '#3498db',
            'high': '#f39c12',
            'urgent': '#e74c3c'
        }
        color = colors.get(obj.priority, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    
    def is_active_badge(self, obj):
        """Badge para el estado activo/inactivo"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activa</span>')
        return format_html('<span style="color: red;">✗ Inactiva</span>')
    is_active_badge.short_description = 'Estado'
    
    def usage_count(self, obj):
        """Total de veces que se ha usado la plantilla"""
        return obj.notifications.count()
    usage_count.short_description = 'Usos'
    
    def last_used(self, obj):
        """Última vez que se usó la plantilla"""
        last = obj.notifications.order_by('-created_at').first()
        if last:
            return last.created_at
        return "Nunca"
    last_used.short_description = 'Último uso'
    
    def duplicate_templates(self, request, queryset):
        """Acción para duplicar plantillas seleccionadas"""
        count = 0
        for template in queryset:
            NotificationTemplate.objects.create(
                name=f"{template.name}_copy",
                title=f"{template.title} (Copia)",
                description=template.description,
                category=template.category,
                notification_type=template.notification_type,
                email_subject=template.email_subject,
                email_body_html=template.email_body_html,
                email_body_text=template.email_body_text,
                in_app_title=template.in_app_title,
                in_app_message=template.in_app_message,
                is_active=False,
                priority=template.priority,
                available_variables=template.available_variables,
                created_by=request.user
            )
            count += 1
        
        self.message_user(request, f"{count} plantilla(s) duplicada(s) exitosamente.")
    duplicate_templates.short_description = "Duplicar plantillas seleccionadas"
    
    def activate_templates(self, request, queryset):
        """Activar plantillas seleccionadas"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} plantilla(s) activada(s).")
    activate_templates.short_description = "Activar plantillas seleccionadas"
    
    def deactivate_templates(self, request, queryset):
        """Desactivar plantillas seleccionadas"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} plantilla(s) desactivada(s).")
    deactivate_templates.short_description = "Desactivar plantillas seleccionadas"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Administración de notificaciones
    """
    list_display = [
        'recipient',
        'title_preview',
        'template',
        'status_badge',
        'priority_badge',
        'notification_type',
        'created_at',
        'read_at'
    ]
    list_filter = [
        'status',
        'notification_type',
        'priority',
        'created_at',
        'read_at'
    ]
    search_fields = [
        'recipient__email',
        'recipient__first_name',
        'recipient__last_name',
        'title',
        'message'
    ]
    readonly_fields = [
        'created_at',
        'sent_at',
        'read_at',
        'email_sent',
        'email_error'
    ]
    fieldsets = (
        ('Destinatario', {
            'fields': (
                'recipient',
                'template'
            )
        }),
        ('Contenido', {
            'fields': (
                'title',
                'message',
                'email_subject',
                'email_body'
            )
        }),
        ('Configuración', {
            'fields': (
                'status',
                'notification_type',
                'priority',
                'action_url'
            )
        }),
        ('Datos Adicionales', {
            'fields': (
                'context_data',
                'expires_at'
            )
        }),
        ('Estado de Envío', {
            'fields': (
                'created_at',
                'sent_at',
                'read_at',
                'email_sent',
                'email_error'
            )
        })
    )
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_sent', 'resend_notifications']
    
    def title_preview(self, obj):
        """Vista previa del título"""
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_preview.short_description = 'Título'
    
    def status_badge(self, obj):
        """Badge de color para el estado"""
        colors = {
            'pending': '#f39c12',
            'sent': '#2ecc71',
            'failed': '#e74c3c',
            'read': '#3498db'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def priority_badge(self, obj):
        """Badge para la prioridad"""
        colors = {
            'low': '#95a5a6',
            'normal': '#3498db',
            'high': '#f39c12',
            'urgent': '#e74c3c'
        }
        color = colors.get(obj.priority, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    
    def mark_as_read(self, request, queryset):
        """Marcar notificaciones como leídas"""
        from django.utils import timezone
        updated = queryset.filter(read_at__isnull=True).update(
            read_at=timezone.now(),
            status='read'
        )
        self.message_user(request, f"{updated} notificación(es) marcada(s) como leída(s).")
    mark_as_read.short_description = "Marcar como leídas"
    
    def mark_as_sent(self, request, queryset):
        """Marcar notificaciones como enviadas"""
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            sent_at=timezone.now(),
            status='sent'
        )
        self.message_user(request, f"{updated} notificación(es) marcada(s) como enviada(s).")
    mark_as_sent.short_description = "Marcar como enviadas"
    
    def resend_notifications(self, request, queryset):
        """Reenviar notificaciones seleccionadas"""
        from .services import NotificationService
        count = 0
        for notification in queryset:
            try:
                NotificationService.send_notification(notification)
                count += 1
            except Exception:
                continue
        self.message_user(request, f"{count} notificación(es) reenviada(s).")
    resend_notifications.short_description = "Reenviar notificaciones"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Administración de preferencias de notificación
    """
    list_display = [
        'user',
        'email_enabled_badge',
        'in_app_enabled_badge',
        'digest_enabled_badge',
        'updated_at'
    ]
    list_filter = [
        'email_notifications_enabled',
        'in_app_notifications_enabled',
        'digest_enabled',
        'updated_at'
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Preferencias Generales', {
            'fields': (
                'email_notifications_enabled',
                'in_app_notifications_enabled'
            )
        }),
        ('Preferencias por Categoría', {
            'fields': (
                'notify_evaluations',
                'notify_candidates',
                'notify_profiles',
                'notify_system',
                'notify_reminders',
                'notify_alerts'
            )
        }),
        ('Configuración de Resumen', {
            'fields': (
                'digest_enabled',
                'digest_time'
            )
        }),
        ('Otras Preferencias', {
            'fields': (
                'sound_enabled',
                'desktop_notifications'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def email_enabled_badge(self, obj):
        """Badge para email habilitado"""
        if obj.email_notifications_enabled:
            return format_html('<span style="color: green;">✓ Email</span>')
        return format_html('<span style="color: red;">✗ Email</span>')
    email_enabled_badge.short_description = 'Email'
    
    def in_app_enabled_badge(self, obj):
        """Badge para notificaciones en app habilitadas"""
        if obj.in_app_notifications_enabled:
            return format_html('<span style="color: green;">✓ In-App</span>')
        return format_html('<span style="color: red;">✗ In-App</span>')
    in_app_enabled_badge.short_description = 'In-App'
    
    def digest_enabled_badge(self, obj):
        """Badge para resumen diario"""
        if obj.digest_enabled:
            return format_html('<span style="color: green;">✓ Resumen</span>')
        return format_html('<span style="color: gray;">✗ Resumen</span>')
    digest_enabled_badge.short_description = 'Resumen'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """
    Administración de logs de email
    """
    list_display = [
        'recipient',
        'subject_preview',
        'status_badge',
        'notification',
        'sent_at',
        'opened_at',
        'created_at'
    ]
    list_filter = [
        'status',
        'sent_at',
        'created_at'
    ]
    search_fields = [
        'recipient',
        'subject',
        'body_text'
    ]
    readonly_fields = [
        'created_at',
        'sent_at',
        'opened_at',
        'clicked_at'
    ]
    fieldsets = (
        ('Información del Email', {
            'fields': (
                'recipient',
                'subject',
                'body_text',
                'body_html'
            )
        }),
        ('Notificación Relacionada', {
            'fields': ('notification',)
        }),
        ('Estado', {
            'fields': (
                'status',
                'error_message'
            )
        }),
        ('Tracking', {
            'fields': (
                'sent_at',
                'opened_at',
                'clicked_at'
            )
        }),
        ('Metadatos', {
            'fields': (
                'headers',
                'attachments',
                'created_at'
            ),
            'classes': ('collapse',)
        })
    )
    date_hierarchy = 'created_at'
    
    def subject_preview(self, obj):
        """Vista previa del asunto"""
        if len(obj.subject) > 60:
            return obj.subject[:60] + '...'
        return obj.subject
    subject_preview.short_description = 'Asunto'
    
    def status_badge(self, obj):
        """Badge de color para el estado"""
        colors = {
            'pending': '#f39c12',
            'sent': '#2ecc71',
            'failed': '#e74c3c',
            'bounced': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'