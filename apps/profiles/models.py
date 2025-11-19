"""
Modelos para la gestión de Perfiles de Reclutamiento
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.clients.models import Client

User = get_user_model()


class Profile(models.Model):
    """
    Modelo principal para Perfiles de Reclutamiento
    Representa una vacante/posición a reclutar
    """
    
    # Estados del perfil según el diagrama
    STATUS_DRAFT = 'draft'  # Borrador
    STATUS_PENDING = 'pending'  # Pendiente de aprobación
    STATUS_APPROVED = 'approved'  # Aprobado por cliente
    STATUS_IN_PROGRESS = 'in_progress'  # En proceso de búsqueda
    STATUS_CANDIDATES_FOUND = 'candidates_found'  # Candidatos encontrados
    STATUS_IN_EVALUATION = 'in_evaluation'  # En evaluación
    STATUS_IN_INTERVIEW = 'in_interview'  # En entrevistas
    STATUS_FINALISTS = 'finalists'  # Finalistas seleccionados
    STATUS_COMPLETED = 'completed'  # Completado
    STATUS_CANCELLED = 'cancelled'  # Cancelado
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_PENDING, 'Pendiente de Aprobación'),
        (STATUS_APPROVED, 'Aprobado'),
        (STATUS_IN_PROGRESS, 'En Proceso'),
        (STATUS_CANDIDATES_FOUND, 'Candidatos Encontrados'),
        (STATUS_IN_EVALUATION, 'En Evaluación'),
        (STATUS_IN_INTERVIEW, 'En Entrevistas'),
        (STATUS_FINALISTS, 'Finalistas'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_CANCELLED, 'Cancelado'),
    ]
    
    # Tipo de servicio
    SERVICE_NORMAL = 'normal'
    SERVICE_SPECIALIZED = 'specialized'
    
    SERVICE_CHOICES = [
        (SERVICE_NORMAL, 'Servicio Normal'),
        (SERVICE_SPECIALIZED, 'Servicio Especializado'),
    ]
    
    # Relaciones
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='profiles',
        verbose_name='Cliente'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_profiles',
        verbose_name='Asignado a'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_profiles',
        verbose_name='Creado por'
    )
    
    # Información de la posición
    position_title = models.CharField(
        max_length=200,
        verbose_name='Título de la Posición'
    )
    position_description = models.TextField(
        verbose_name='Descripción de la Posición'
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Departamento'
    )
    
    # Ubicación
    location_city = models.CharField(
        max_length=100,
        verbose_name='Ciudad'
    )
    location_state = models.CharField(
        max_length=100,
        verbose_name='Estado'
    )
    is_remote = models.BooleanField(
        default=False,
        verbose_name='Trabajo Remoto'
    )
    is_hybrid = models.BooleanField(
        default=False,
        verbose_name='Trabajo Híbrido'
    )
    
    # Salario
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Salario Mínimo'
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Salario Máximo'
    )
    salary_currency = models.CharField(
        max_length=3,
        default='MXN',
        verbose_name='Moneda'
    )
    salary_period = models.CharField(
        max_length=20,
        default='mensual',
        choices=[
            ('mensual', 'Mensual'),
            ('anual', 'Anual'),
        ],
        verbose_name='Periodo de Pago'
    )
    
    # Requisitos
    education_level = models.CharField(
        max_length=100,
        verbose_name='Nivel de Estudios'
    )
    years_experience = models.IntegerField(
        verbose_name='Años de Experiencia Requeridos'
    )
    age_min = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Edad Mínima'
    )
    age_max = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Edad Máxima'
    )
    
    # Habilidades y competencias (JSON field para flexibilidad)
    technical_skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Habilidades Técnicas',
        help_text='Lista de habilidades técnicas requeridas'
    )
    soft_skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Habilidades Blandas',
        help_text='Lista de competencias blandas requeridas'
    )
    languages = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Idiomas',
        help_text='Lista de idiomas requeridos con nivel'
    )
    
    # Beneficios y otros
    benefits = models.TextField(
        blank=True,
        verbose_name='Beneficios'
    )
    additional_requirements = models.TextField(
        blank=True,
        verbose_name='Requisitos Adicionales'
    )
    
    # Gestión del proceso
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name='Estado'
    )
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_CHOICES,
        default=SERVICE_NORMAL,
        verbose_name='Tipo de Servicio'
    )
    number_of_positions = models.IntegerField(
        default=1,
        verbose_name='Número de Posiciones'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        default='medium',
        verbose_name='Prioridad'
    )
    
    # Fechas importantes
    desired_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Deseada de Inicio'
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Límite'
    )
    
    # Transcripción de la reunión (generada por IA)
    meeting_transcription = models.TextField(
        blank=True,
        verbose_name='Transcripción de la Reunión'
    )
    
    # Notas internas
    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas Internas'
    )
    
    # Aprobación del cliente
    client_approved = models.BooleanField(
        default=False,
        verbose_name='Aprobado por Cliente'
    )
    client_approval_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Aprobación del Cliente'
    )
    client_feedback = models.TextField(
        blank=True,
        verbose_name='Retroalimentación del Cliente'
    )
    
    # Metadatos
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Completado'
    )
    
    class Meta:
        verbose_name = 'Perfil de Reclutamiento'
        verbose_name_plural = 'Perfiles de Reclutamiento'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['position_title']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.position_title} - {self.client.company_name}"
    
    @property
    def salary_range(self):
        # Verificar si los campos necesarios tienen valores
        if self.salary_min is None or self.salary_max is None:
            return "No especificado"
        
        # Si hay valores, formatear normalmente
        currency = self.salary_currency or ""
        period = self.salary_period or ""
        
        return f"${self.salary_min:,.2f} - ${self.salary_max:,.2f} {currency}/{period}"
    
    @property
    def candidates_count(self):
        """Cuenta los candidatos asociados"""
        return self.candidates.count()
    
    @property
    def is_urgent(self):
        """Verifica si el perfil es urgente"""
        return self.priority == 'urgent'


class ProfileStatusHistory(models.Model):
    """
    Modelo para registrar el historial de cambios de estado de un perfil
    """
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Perfil'
    )
    from_status = models.CharField(
        max_length=30,
        choices=Profile.STATUS_CHOICES,
        verbose_name='Estado Anterior'
    )
    to_status = models.CharField(
        max_length=30,
        choices=Profile.STATUS_CHOICES,
        verbose_name='Estado Nuevo'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Cambiado por'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Cambio'
    )
    
    class Meta:
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historial de Estados'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.profile} - {self.from_status} → {self.to_status}"


class ProfileDocument(models.Model):
    """
    Modelo para documentos asociados a un perfil
    """
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Perfil'
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('profile_pdf', 'PDF del Perfil'),
            ('client_approval', 'Aprobación del Cliente'),
            ('meeting_notes', 'Notas de Reunión'),
            ('other', 'Otro'),
        ],
        verbose_name='Tipo de Documento'
    )
    file = models.FileField(
        upload_to='profiles/%Y/%m/',
        verbose_name='Archivo'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Subido por'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Subida'
    )
    
    class Meta:
        verbose_name = 'Documento del Perfil'
        verbose_name_plural = 'Documentos de Perfiles'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.profile}"