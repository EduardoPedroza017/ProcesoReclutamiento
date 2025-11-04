"""
Modelos para el sistema de notificaciones
Gestiona notificaciones por email y en la aplicación
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import User


class NotificationTemplate(models.Model):
    """
    Plantilla de notificación reutilizable
    Define el contenido y estructura de los emails y notificaciones
    """
    
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('in_app', 'Notificación en App'),
        ('both', 'Ambos'),
    ]
    
    CATEGORY_CHOICES = [
        ('evaluation', 'Evaluación'),
        ('candidate', 'Candidato'),
        ('profile', 'Perfil'),
        ('system', 'Sistema'),
        ('reminder', 'Recordatorio'),
        ('alert', 'Alerta'),
    ]
    
    # Información básica
    name = models.CharField(
        _('nombre'),
        max_length=200,
        unique=True,
        help_text='Nombre identificador de la plantilla (ej: evaluation_assigned)'
    )
    title = models.CharField(
        _('título'),
        max_length=255,
        help_text='Título descriptivo de la plantilla'
    )
    description = models.TextField(
        _('descripción'),
        blank=True,
        help_text='Descripción del propósito de esta plantilla'
    )
    
    # Categorización
    category = models.CharField(
        _('categoría'),
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='system'
    )
    notification_type = models.CharField(
        _('tipo de notificación'),
        max_length=10,
        choices=TYPE_CHOICES,
        default='both'
    )
    
    # Contenido del email
    email_subject = models.CharField(
        _('asunto del email'),
        max_length=255,
        blank=True,
        help_text='Asunto del correo. Puede usar variables: {user_name}, {evaluation_title}, etc.'
    )
    email_body_html = models.TextField(
        _('cuerpo HTML del email'),
        blank=True,
        help_text='Contenido HTML del email. Puede usar variables.'
    )
    email_body_text = models.TextField(
        _('cuerpo texto plano del email'),
        blank=True,
        help_text='Versión en texto plano del email (fallback)'
    )
    
    # Contenido de la notificación en app
    in_app_title = models.CharField(
        _('título en app'),
        max_length=255,
        blank=True
    )
    in_app_message = models.TextField(
        _('mensaje en app'),
        blank=True
    )
    
    # Configuración
    is_active = models.BooleanField(
        _('activa'),
        default=True,
        help_text='Si la plantilla está disponible para usar'
    )
    priority = models.CharField(
        _('prioridad'),
        max_length=10,
        choices=[
            ('low', 'Baja'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        default='normal'
    )
    
    # Variables disponibles
    available_variables = models.JSONField(
        _('variables disponibles'),
        default=list,
        blank=True,
        help_text='Lista de variables que se pueden usar en esta plantilla'
    )
    
    # Metadatos
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_notification_templates',
        verbose_name=_('creado por')
    )
    
    class Meta:
        verbose_name = _('plantilla de notificación')
        verbose_name_plural = _('plantillas de notificación')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.title}"
    
    def render_email_subject(self, context):
        """Renderiza el asunto del email con el contexto dado"""
        return self.email_subject.format(**context)
    
    def render_email_body_html(self, context):
        """Renderiza el cuerpo HTML del email con el contexto dado"""
        return self.email_body_html.format(**context)
    
    def render_email_body_text(self, context):
        """Renderiza el cuerpo de texto plano con el contexto dado"""
        return self.email_body_text.format(**context)
    
    def render_in_app_message(self, context):
        """Renderiza el mensaje de la notificación en app con el contexto dado"""
        return self.in_app_message.format(**context)


class Notification(models.Model):
    """
    Notificación individual enviada a un usuario
    Puede ser email, notificación en app, o ambas
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Fallida'),
        ('read', 'Leída'),
    ]
    
    # Relación con usuario
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('destinatario')
    )
    
    # Plantilla utilizada
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('plantilla')
    )
    
    # Contenido (guardado después de renderizar)
    title = models.CharField(
        _('título'),
        max_length=255
    )
    message = models.TextField(
        _('mensaje')
    )
    
    # Email relacionado
    email_subject = models.CharField(
        _('asunto del email'),
        max_length=255,
        blank=True
    )
    email_body = models.TextField(
        _('cuerpo del email'),
        blank=True
    )
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notification_type = models.CharField(
        _('tipo'),
        max_length=10,
        choices=[
            ('email', 'Email'),
            ('in_app', 'En App'),
            ('both', 'Ambos'),
        ],
        default='in_app'
    )
    priority = models.CharField(
        _('prioridad'),
        max_length=10,
        choices=[
            ('low', 'Baja'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        default='normal'
    )
    
    # Relación genérica con cualquier objeto
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Datos adicionales
    context_data = models.JSONField(
        _('datos de contexto'),
        default=dict,
        blank=True,
        help_text='Datos adicionales usados para renderizar la notificación'
    )
    
    # Fechas
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    sent_at = models.DateTimeField(_('fecha de envío'), null=True, blank=True)
    read_at = models.DateTimeField(_('fecha de lectura'), null=True, blank=True)
    expires_at = models.DateTimeField(
        _('fecha de expiración'),
        null=True,
        blank=True,
        help_text='Fecha después de la cual la notificación ya no es relevante'
    )
    
    # Información de envío de email
    email_sent = models.BooleanField(_('email enviado'), default=False)
    email_error = models.TextField(_('error de email'), blank=True)
    
    # Acciones
    action_url = models.URLField(
        _('URL de acción'),
        blank=True,
        help_text='URL a la que redirige la notificación al hacer clic'
    )
    
    class Meta:
        verbose_name = _('notificación')
        verbose_name_plural = _('notificaciones')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['recipient', 'read_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """Marca la notificación como leída"""
        if not self.read_at:
            from django.utils import timezone
            self.read_at = timezone.now()
            self.status = 'read'
            self.save(update_fields=['read_at', 'status'])
    
    def mark_as_sent(self):
        """Marca la notificación como enviada"""
        from django.utils import timezone
        self.sent_at = timezone.now()
        self.status = 'sent'
        self.save(update_fields=['sent_at', 'status'])
    
    def mark_as_failed(self, error_message=''):
        """Marca la notificación como fallida"""
        self.status = 'failed'
        self.email_error = error_message
        self.save(update_fields=['status', 'email_error'])
    
    @property
    def is_unread(self):
        """Verifica si la notificación no ha sido leída"""
        return self.read_at is None
    
    @property
    def is_expired(self):
        """Verifica si la notificación ha expirado"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class NotificationPreference(models.Model):
    """
    Preferencias de notificación por usuario
    Permite a los usuarios controlar qué notificaciones reciben y cómo
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('usuario')
    )
    
    # Preferencias generales
    email_notifications_enabled = models.BooleanField(
        _('notificaciones por email'),
        default=True,
        help_text='Habilitar/deshabilitar notificaciones por email'
    )
    in_app_notifications_enabled = models.BooleanField(
        _('notificaciones en app'),
        default=True,
        help_text='Habilitar/deshabilitar notificaciones en la aplicación'
    )
    
    # Preferencias por categoría
    notify_evaluations = models.BooleanField(_('evaluaciones'), default=True)
    notify_candidates = models.BooleanField(_('candidatos'), default=True)
    notify_profiles = models.BooleanField(_('perfiles'), default=True)
    notify_system = models.BooleanField(_('sistema'), default=True)
    notify_reminders = models.BooleanField(_('recordatorios'), default=True)
    notify_alerts = models.BooleanField(_('alertas'), default=True)
    
    # Configuración de frecuencia
    digest_enabled = models.BooleanField(
        _('resumen diario'),
        default=False,
        help_text='Recibir un resumen diario en lugar de notificaciones individuales'
    )
    digest_time = models.TimeField(
        _('hora del resumen'),
        null=True,
        blank=True,
        help_text='Hora a la que se envía el resumen diario'
    )
    
    # Configuración de sonidos y alertas
    sound_enabled = models.BooleanField(_('sonido'), default=True)
    desktop_notifications = models.BooleanField(
        _('notificaciones de escritorio'),
        default=False
    )
    
    # Metadatos
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('preferencia de notificación')
        verbose_name_plural = _('preferencias de notificación')
    
    def __str__(self):
        return f"Preferencias de {self.user.get_full_name()}"
    
    def should_notify(self, category):
        """
        Verifica si el usuario debe recibir notificaciones de una categoría
        """
        category_map = {
            'evaluation': self.notify_evaluations,
            'candidate': self.notify_candidates,
            'profile': self.notify_profiles,
            'system': self.notify_system,
            'reminder': self.notify_reminders,
            'alert': self.notify_alerts,
        }
        return category_map.get(category, True)


class EmailLog(models.Model):
    """
    Registro de emails enviados
    Mantiene un historial de todos los emails enviados por el sistema
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('bounced', 'Rebotado'),
    ]
    
    # Información del email
    recipient = models.EmailField(_('destinatario'))
    subject = models.CharField(_('asunto'), max_length=255)
    body_text = models.TextField(_('cuerpo texto'))
    body_html = models.TextField(_('cuerpo HTML'), blank=True)
    
    # Relación con notificación
    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
        verbose_name=_('notificación')
    )
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Información de envío
    sent_at = models.DateTimeField(_('fecha de envío'), null=True, blank=True)
    error_message = models.TextField(_('mensaje de error'), blank=True)
    
    # Tracking
    opened_at = models.DateTimeField(_('fecha de apertura'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('fecha de clic'), null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    
    # Información adicional
    headers = models.JSONField(
        _('headers'),
        default=dict,
        blank=True,
        help_text='Headers adicionales del email'
    )
    attachments = models.JSONField(
        _('adjuntos'),
        default=list,
        blank=True,
        help_text='Lista de nombres de archivos adjuntos'
    )
    
    class Meta:
        verbose_name = _('log de email')
        verbose_name_plural = _('logs de emails')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.recipient} - {self.subject} ({self.get_status_display()})"
    
    def mark_as_opened(self):
        """Marca el email como abierto"""
        if not self.opened_at:
            from django.utils import timezone
            self.opened_at = timezone.now()
            self.save(update_fields=['opened_at'])
    
    def mark_as_clicked(self):
        """Marca el email como clickeado"""
        if not self.clicked_at:
            from django.utils import timezone
            self.clicked_at = timezone.now()
            self.save(update_fields=['clicked_at'])