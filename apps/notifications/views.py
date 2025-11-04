"""
Views para el sistema de notificaciones
Maneja la lógica de negocio y endpoints de la API
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    NotificationTemplate,
    Notification,
    NotificationPreference,
    EmailLog
)
from .serializers import (
    NotificationTemplateSerializer,
    NotificationTemplateListSerializer,
    NotificationSerializer,
    NotificationListSerializer,
    NotificationCreateSerializer,
    NotificationPreferenceSerializer,
    EmailLogSerializer,
    EmailLogListSerializer,
    BulkNotificationSerializer,
    MarkAsReadSerializer,
    NotificationStatsSerializer
)
from apps.accounts.permissions import IsAdminUser, IsDirectorOrAbove, IsSupervisorOrAbove


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de plantillas de notificación
    
    Endpoints:
    - GET /api/notifications/templates/ - Listar plantillas
    - POST /api/notifications/templates/ - Crear plantilla
    - GET /api/notifications/templates/{id}/ - Detalle de plantilla
    - PUT /api/notifications/templates/{id}/ - Actualizar plantilla
    - DELETE /api/notifications/templates/{id}/ - Eliminar plantilla
    - POST /api/notifications/templates/{id}/duplicate/ - Duplicar plantilla
    - POST /api/notifications/templates/{id}/test/ - Probar plantilla
    """
    
    queryset = NotificationTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsDirectorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'notification_type', 'is_active', 'priority']
    search_fields = ['name', 'title', 'description']
    ordering_fields = ['created_at', 'name', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return NotificationTemplateListSerializer
        return NotificationTemplateSerializer
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicar una plantilla de notificación
        """
        template = self.get_object()
        
        new_template = NotificationTemplate.objects.create(
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
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Probar una plantilla enviando una notificación de prueba
        Body: {"recipient_id": 1, "context": {...}}
        """
        template = self.get_object()
        
        recipient_id = request.data.get('recipient_id')
        context = request.data.get('context', {})
        
        if not recipient_id:
            return Response(
                {'error': 'recipient_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.accounts.models import User
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear notificación de prueba
        from .services import NotificationService
        notification = NotificationService.create_notification(
            template=template,
            recipient=recipient,
            context=context
        )
        
        # Enviar inmediatamente
        NotificationService.send_notification(notification)
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de notificaciones
    
    Endpoints principales:
    - GET /api/notifications/ - Listar notificaciones
    - POST /api/notifications/ - Crear notificación
    - GET /api/notifications/{id}/ - Detalle de notificación
    - DELETE /api/notifications/{id}/ - Eliminar notificación
    
    Acciones especiales:
    - GET /api/notifications/unread/ - Notificaciones no leídas
    - POST /api/notifications/{id}/mark_as_read/ - Marcar como leída
    - POST /api/notifications/mark_all_as_read/ - Marcar todas como leídas
    - POST /api/notifications/send_bulk/ - Envío masivo
    - GET /api/notifications/statistics/ - Estadísticas
    - DELETE /api/notifications/clear_read/ - Limpiar leídas
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'notification_type', 'priority']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority', 'read_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        """
        Usuarios ven solo sus propias notificaciones
        Admin y Director pueden ver todas
        """
        user = self.request.user
        
        if user.is_admin or user.is_director:
            return Notification.objects.all()
        
        return Notification.objects.filter(recipient=user)
    
    def create(self, request, *args, **kwargs):
        """
        Crear notificación desde plantilla
        Body: {
            "template_name": "evaluation_assigned",
            "recipient_id": 5,
            "context": {...}
        }
        """
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_name = serializer.validated_data['template_name']
        recipient_id = serializer.validated_data.get('recipient_id')
        recipient_ids = serializer.validated_data.get('recipient_ids', [])
        context = serializer.validated_data['context']
        send_immediately = serializer.validated_data['send_immediately']
        
        # Obtener plantilla
        try:
            template = NotificationTemplate.objects.get(name=template_name)
        except NotificationTemplate.DoesNotExist:
            return Response(
                {'error': 'Plantilla no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear notificaciones
        from .services import NotificationService
        notifications = []
        
        if recipient_id:
            recipient_ids = [recipient_id]
        
        from apps.accounts.models import User
        for uid in recipient_ids:
            try:
                recipient = User.objects.get(id=uid)
                notification = NotificationService.create_notification(
                    template=template,
                    recipient=recipient,
                    context=context
                )
                
                if send_immediately:
                    NotificationService.send_notification(notification)
                
                notifications.append(notification)
            except User.DoesNotExist:
                continue
        
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Obtener solo notificaciones no leídas del usuario actual
        """
        notifications = self.get_queryset().filter(
            recipient=request.user,
            read_at__isnull=True
        )
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marcar una notificación como leída
        """
        notification = self.get_object()
        notification.mark_as_read()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Marcar todas las notificaciones del usuario como leídas
        """
        updated = self.get_queryset().filter(
            recipient=request.user,
            read_at__isnull=True
        ).update(
            read_at=timezone.now(),
            status='read'
        )
        
        return Response({'marked_as_read': updated})
    
    @action(detail=False, methods=['post'], permission_classes=[IsDirectorOrAbove])
    def send_bulk(self, request):
        """
        Enviar notificaciones masivas
        Body: {
            "template_name": "...",
            "recipient_ids": [1, 2, 3],
            "context": {...}
        }
        """
        serializer = BulkNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_name = serializer.validated_data['template_name']
        recipient_ids = serializer.validated_data['recipient_ids']
        context = serializer.validated_data['context']
        send_immediately = serializer.validated_data['send_immediately']
        
        # Obtener plantilla
        try:
            template = NotificationTemplate.objects.get(name=template_name)
        except NotificationTemplate.DoesNotExist:
            return Response(
                {'error': 'Plantilla no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear notificaciones
        from .services import NotificationService
        from apps.accounts.models import User
        
        created_count = 0
        sent_count = 0
        
        for recipient_id in recipient_ids:
            try:
                recipient = User.objects.get(id=recipient_id)
                notification = NotificationService.create_notification(
                    template=template,
                    recipient=recipient,
                    context=context
                )
                created_count += 1
                
                if send_immediately:
                    success = NotificationService.send_notification(notification)
                    if success:
                        sent_count += 1
            except User.DoesNotExist:
                continue
        
        return Response({
            'created': created_count,
            'sent': sent_count,
            'total_recipients': len(recipient_ids)
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Obtener estadísticas de notificaciones del usuario
        """
        user_notifications = self.get_queryset().filter(recipient=request.user)
        
        total = user_notifications.count()
        unread = user_notifications.filter(read_at__isnull=True).count()
        read = user_notifications.filter(read_at__isnull=False).count()
        pending = user_notifications.filter(status='pending').count()
        failed = user_notifications.filter(status='failed').count()
        
        # Estadísticas de emails
        email_logs = EmailLog.objects.filter(
            notification__recipient=request.user
        )
        total_emails = email_logs.count()
        emails_sent = email_logs.filter(status='sent').count()
        emails_opened = email_logs.filter(opened_at__isnull=False).count()
        emails_clicked = email_logs.filter(clicked_at__isnull=False).count()
        
        email_delivery_rate = (emails_sent / total_emails * 100) if total_emails > 0 else 0
        email_open_rate = (emails_opened / emails_sent * 100) if emails_sent > 0 else 0
        
        stats = {
            'total_notifications': total,
            'unread_notifications': unread,
            'read_notifications': read,
            'pending_notifications': pending,
            'failed_notifications': failed,
            'total_emails_sent': total_emails,
            'emails_opened': emails_opened,
            'emails_clicked': emails_clicked,
            'email_delivery_rate': round(email_delivery_rate, 2),
            'email_open_rate': round(email_open_rate, 2)
        }
        
        serializer = NotificationStatsSerializer(data=stats)
        serializer.is_valid()
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """
        Eliminar todas las notificaciones leídas del usuario
        """
        deleted = self.get_queryset().filter(
            recipient=request.user,
            read_at__isnull=False
        ).delete()
        
        return Response({'deleted': deleted[0]})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de preferencias de notificación
    
    Endpoints:
    - GET /api/notifications/preferences/ - Obtener preferencias
    - PUT /api/notifications/preferences/{id}/ - Actualizar preferencias
    - GET /api/notifications/preferences/my_preferences/ - Mis preferencias
    """
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Usuarios solo ven sus propias preferencias"""
        user = self.request.user
        
        if user.is_admin:
            return NotificationPreference.objects.all()
        
        return NotificationPreference.objects.filter(user=user)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def my_preferences(self, request):
        """
        Obtener o actualizar las preferencias del usuario actual
        """
        # Crear preferencias si no existen
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        
        # PUT o PATCH
        serializer = self.get_serializer(
            preferences,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualización de logs de email
    Solo lectura
    
    Endpoints:
    - GET /api/notifications/email-logs/ - Listar logs
    - GET /api/notifications/email-logs/{id}/ - Detalle de log
    """
    
    permission_classes = [IsAuthenticated, IsDirectorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'recipient']
    search_fields = ['recipient', 'subject']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return EmailLogListSerializer
        return EmailLogSerializer
    
    def get_queryset(self):
        """Admins ven todos los logs, otros solo logs relacionados con ellos"""
        user = self.request.user
        
        if user.is_admin:
            return EmailLog.objects.all()
        
        # Directors ven logs de sus notificaciones
        return EmailLog.objects.filter(
            notification__recipient=user
        )