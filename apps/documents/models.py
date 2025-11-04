"""
Modelos para la gestión de Documentos y Generación de PDFs
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.profiles.models import Profile
from apps.candidates.models import Candidate

User = get_user_model()


class DocumentTemplate(models.Model):
    """
    Plantillas para generar diferentes tipos de documentos PDF
    """
    
    # Tipos de documento
    TYPE_PROFILE = 'profile'  # Perfil de reclutamiento
    TYPE_CANDIDATE_REPORT = 'candidate_report'  # Reporte de candidato
    TYPE_COMPARISON = 'comparison'  # Comparación de candidatos
    TYPE_FINAL_REPORT = 'final_report'  # Reporte final
    TYPE_CLIENT_REPORT = 'client_report'  # Reporte para cliente
    TYPE_CUSTOM = 'custom'  # Personalizado
    
    TYPE_CHOICES = [
        (TYPE_PROFILE, 'Perfil de Reclutamiento'),
        (TYPE_CANDIDATE_REPORT, 'Reporte de Candidato'),
        (TYPE_COMPARISON, 'Comparación de Candidatos'),
        (TYPE_FINAL_REPORT, 'Reporte Final'),
        (TYPE_CLIENT_REPORT, 'Reporte para Cliente'),
        (TYPE_CUSTOM, 'Personalizado'),
    ]
    
    # Campos básicos
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Plantilla'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    document_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default=TYPE_CUSTOM,
        verbose_name='Tipo de Documento'
    )
    
    # Configuración de la plantilla
    header_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Texto del Encabezado'
    )
    footer_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Texto del Pie de Página'
    )
    logo = models.ImageField(
        upload_to='templates/logos/',
        blank=True,
        null=True,
        verbose_name='Logo de la Empresa'
    )
    
    # Configuración de estilo (JSON)
    # Ejemplo: {"font": "Helvetica", "color": "#333333", "margins": {"top": 50, "bottom": 50}}
    style_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configuración de Estilo'
    )
    
    # Secciones a incluir (JSON)
    # Ejemplo: ["company_info", "position_details", "requirements", "skills"]
    sections = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Secciones del Documento'
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='Plantilla por Defecto'
    )
    
    # Auditoría
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates',
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Plantilla de Documento'
        verbose_name_plural = 'Plantillas de Documentos'
        ordering = ['document_type', 'name']
        indexes = [
            models.Index(fields=['document_type', 'is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Si se marca como default, desmarcar las otras del mismo tipo
        if self.is_default:
            DocumentTemplate.objects.filter(
                document_type=self.document_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class GeneratedDocument(models.Model):
    """
    Documentos PDF generados por el sistema
    """
    
    # Estados del documento
    STATUS_PENDING = 'pending'
    STATUS_GENERATING = 'generating'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_GENERATING, 'Generando'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_FAILED, 'Fallido'),
    ]
    
    # Campos básicos
    title = models.CharField(
        max_length=200,
        verbose_name='Título del Documento'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    # Plantilla utilizada
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_documents',
        verbose_name='Plantilla'
    )
    
    # Relaciones opcionales
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generated_documents',  # Cambiado para evitar conflicto con ProfileDocument
        verbose_name='Perfil Relacionado'
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='generated_documents',  # Cambiado para evitar conflicto con CandidateDocument
        verbose_name='Candidato Relacionado'
    )
    
    # Datos personalizados para el documento (JSON)
    # Contiene toda la información que se usará para generar el PDF
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos Personalizados'
    )
    
    # Archivo generado
    file = models.FileField(
        upload_to='generated_documents/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Archivo PDF'
    )
    file_size = models.IntegerField(
        default=0,
        verbose_name='Tamaño del Archivo (bytes)'
    )
    
    # Estado y control
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Estado'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error'
    )
    
    # Estadísticas
    generation_time = models.FloatField(
        default=0,
        verbose_name='Tiempo de Generación (segundos)'
    )
    download_count = models.IntegerField(
        default=0,
        verbose_name='Número de Descargas'
    )
    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Descarga'
    )
    
    # Versionamiento
    version = models.IntegerField(
        default=1,
        verbose_name='Versión'
    )
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        verbose_name='Documento Padre'
    )
    
    # Auditoría
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_documents',
        verbose_name='Generado por'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Generación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Documento Generado'
        verbose_name_plural = 'Documentos Generados'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['profile']),
            models.Index(fields=['candidate']),
            models.Index(fields=['generated_by', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def increment_download_count(self):
        """Incrementa el contador de descargas"""
        from django.utils import timezone
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded_at'])
    
    def create_new_version(self, user):
        """Crea una nueva versión del documento"""
        new_version = GeneratedDocument.objects.create(
            title=self.title,
            description=self.description,
            template=self.template,
            profile=self.profile,
            candidate=self.candidate,
            custom_data=self.custom_data,
            version=self.version + 1,
            parent_document=self.parent_document or self,
            generated_by=user
        )
        return new_version


class DocumentSection(models.Model):
    """
    Secciones reutilizables para documentos
    Permite crear bloques de contenido predefinidos
    """
    
    # Campos básicos
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Sección'
    )
    code = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name='Código'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    
    # Contenido de la sección (puede ser HTML o Markdown)
    content = models.TextField(
        verbose_name='Contenido'
    )
    
    # Configuración
    order = models.IntegerField(
        default=0,
        verbose_name='Orden'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    # Variables disponibles en esta sección (JSON)
    # Ejemplo: ["company_name", "position_title", "salary_range"]
    available_variables = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Variables Disponibles'
    )
    
    # Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )
    
    class Meta:
        verbose_name = 'Sección de Documento'
        verbose_name_plural = 'Secciones de Documentos'
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class DocumentLog(models.Model):
    """
    Log de actividades relacionadas con documentos
    """
    
    # Tipos de acción
    ACTION_GENERATED = 'generated'
    ACTION_DOWNLOADED = 'downloaded'
    ACTION_SHARED = 'shared'
    ACTION_DELETED = 'deleted'
    ACTION_REGENERATED = 'regenerated'
    
    ACTION_CHOICES = [
        (ACTION_GENERATED, 'Generado'),
        (ACTION_DOWNLOADED, 'Descargado'),
        (ACTION_SHARED, 'Compartido'),
        (ACTION_DELETED, 'Eliminado'),
        (ACTION_REGENERATED, 'Regenerado'),
    ]
    
    # Campos
    document = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Documento'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Acción'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario'
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Detalles'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    
    class Meta:
        verbose_name = 'Log de Documento'
        verbose_name_plural = 'Logs de Documentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document', '-created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.document.title} - {self.get_action_display()} por {self.user}"