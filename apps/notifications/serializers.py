"""
Serializers para el sistema de notificaciones
Maneja la serialización/deserialización de datos para la API REST
"""

from rest_framework import serializers
from django.utils import timezone
from .models import (
    NotificationTemplate,
    Notification,
    NotificationPreference,
    EmailLog
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer completo para plantillas de notificación
    """
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'name',
            'title',
            'description',
            'category',
            'category_display',
            'notification_type',
            'notification_type_display',
            'email_subject',
            'email_body_html',
            'email_body_text',
            'in_app_title',
            'in_app_message',
            'is_active',
            'priority',
            'priority_display',
            'available_variables',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Asignar el usuario actual como creador"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NotificationTemplateListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar plantillas
    """
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'name',
            'title',
            'category',
            'category_display',
            'notification_type',
            'is_active',
            'priority',
            'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer completo para notificaciones
    """
    recipient_name = serializers.CharField(
        source='recipient.get_full_name',
        read_only=True
    )
    recipient_email = serializers.EmailField(
        source='recipient.email',
        read_only=True
    )
    template_name = serializers.CharField(
        source='template.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    is_unread = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'recipient_name',
            'recipient_email',
            'template',
            'template_name',
            'title',
            'message',
            'email_subject',
            'email_body',
            'status',
            'status_display',
            'notification_type',
            'notification_type_display',
            'priority',
            'priority_display',
            'context_data',
            'created_at',
            'sent_at',
            'read_at',
            'expires_at',
            'email_sent',
            'email_error',
            'action_url',
            'is_unread',
            'is_expired'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'sent_at',
            'read_at',
            'email_sent',
            'email_error'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar notificaciones
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_unread = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'status',
            'status_display',
            'priority',
            'created_at',
            'read_at',
            'is_unread',
            'action_url'
        ]


class NotificationCreateSerializer(serializers.Serializer):
    """
    Serializer para crear notificaciones desde una plantilla
    """
    template_name = serializers.CharField()
    recipient_id = serializers.IntegerField(required=False)
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    context = serializers.DictField(default=dict)
    send_immediately = serializers.BooleanField(default=True)
    
    def validate(self, data):
        """Validar que se proporcione al menos un destinatario"""
        if not data.get('recipient_id') and not data.get('recipient_ids'):
            raise serializers.ValidationError(
                "Debe proporcionar recipient_id o recipient_ids"
            )
        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer para preferencias de notificación
    """
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'user',
            'user_name',
            'email_notifications_enabled',
            'in_app_notifications_enabled',
            'notify_evaluations',
            'notify_candidates',
            'notify_profiles',
            'notify_system',
            'notify_reminders',
            'notify_alerts',
            'digest_enabled',
            'digest_time',
            'sound_enabled',
            'desktop_notifications',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class EmailLogSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de email
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    notification_id = serializers.IntegerField(
        source='notification.id',
        read_only=True
    )
    
    class Meta:
        model = EmailLog
        fields = [
            'id',
            'recipient',
            'subject',
            'body_text',
            'body_html',
            'notification',
            'notification_id',
            'status',
            'status_display',
            'sent_at',
            'error_message',
            'opened_at',
            'clicked_at',
            'created_at',
            'headers',
            'attachments'
        ]
        read_only_fields = ['id', 'created_at']


class EmailLogListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar logs de email
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = [
            'id',
            'recipient',
            'subject',
            'status',
            'status_display',
            'sent_at',
            'created_at'
        ]


class BulkNotificationSerializer(serializers.Serializer):
    """
    Serializer para envío masivo de notificaciones
    """
    template_name = serializers.CharField()
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    context = serializers.DictField(default=dict)
    send_immediately = serializers.BooleanField(default=False)


class MarkAsReadSerializer(serializers.Serializer):
    """
    Serializer para marcar notificaciones como leídas
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de notificaciones
    """
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    read_notifications = serializers.IntegerField()
    pending_notifications = serializers.IntegerField()
    failed_notifications = serializers.IntegerField()
    total_emails_sent = serializers.IntegerField()
    emails_opened = serializers.IntegerField()
    emails_clicked = serializers.IntegerField()
    email_delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    email_open_rate = serializers.DecimalField(max_digits=5, decimal_places=2)