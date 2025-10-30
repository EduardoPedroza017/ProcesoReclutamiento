"""
Modelos para la gestión de Candidatos
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.profiles.models import Profile

User = get_user_model()


class Candidate(models.Model):
    """
    Modelo principal para Candidatos
    Representa una persona que aplica a una o más posiciones
    """
    
    # Estados del candidato
    STATUS_NEW = 'new'  # Nuevo
    STATUS_SCREENING = 'screening'  # En revisión inicial
    STATUS_QUALIFIED = 'qualified'  # Calificado
    STATUS_INTERVIEW = 'interview'  # En entrevista
    STATUS_OFFER = 'offer'  # Oferta extendida
    STATUS_HIRED = 'hired'  # Contratado
    STATUS_REJECTED = 'rejected'  # Rechazado
    STATUS_WITHDRAWN = 'withdrawn'  # Retirado
    
    STATUS_CHOICES = [
        (STATUS_NEW, 'Nuevo'),
        (STATUS_SCREENING, 'En Revisión'),
        (STATUS_QUALIFIED, 'Calificado'),
        (STATUS_INTERVIEW, 'En Entrevista'),
        (STATUS_OFFER, 'Oferta Extendida'),
        (STATUS_HIRED, 'Contratado'),
        (STATUS_REJECTED, 'Rechazado'),
        (STATUS_WITHDRAWN, 'Retirado'),
    ]
    
    # Información personal
    first_name = models.CharField(
        max_length=100,
        verbose_name='Nombre(s)'
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='Apellido(s)'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Correo Electrónico'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    alternative_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono Alternativo'
    )
    
    # Ubicación
    city = models.CharField(
        max_length=100,
        verbose_name='Ciudad'
    )
    state = models.CharField(
        max_length=100,
        verbose_name='Estado'
    )
    country = models.CharField(
        max_length=100,
        default='México',
        verbose_name='País'
    )
    address = models.TextField(
        blank=True,
        verbose_name='Dirección Completa'
    )
    
    # Información profesional
    current_position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Posición Actual'
    )
    current_company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Empresa Actual'
    )
    years_of_experience = models.IntegerField(
        default=0,
        verbose_name='Años de Experiencia'
    )
    education_level = models.CharField(
        max_length=100,
        verbose_name='Nivel de Estudios'
    )
    university = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Universidad'
    )
    degree = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Carrera/Título'
    )
    
    # Habilidades y competencias (JSON field)
    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Habilidades',
        help_text='Lista de habilidades del candidato'
    )
    languages = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Idiomas',
        help_text='Lista de idiomas con nivel'
    )
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Certificaciones',
        help_text='Lista de certificaciones'
    )
    
    # Expectativas salariales
    salary_expectation_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Expectativa Salarial Mínima'
    )
    salary_expectation_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Expectativa Salarial Máxima'
    )
    salary_currency = models.CharField(
        max_length=3,
        default='MXN',
        verbose_name='Moneda'
    )
    
    # Perfiles a los que aplica
    profiles = models.ManyToManyField(
        Profile,
        through='CandidateProfile',
        related_name='candidates',
        verbose_name='Perfiles'
    )
    
    # Gestión
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name='Estado'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_candidates',
        verbose_name='Asignado a'
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Fuente de Reclutamiento',
        help_text='Ej: LinkedIn, Portal de empleo, Referido, etc.'
    )
    
    # Análisis de IA (generado por Claude)
    ai_summary = models.TextField(
        blank=True,
        verbose_name='Resumen generado por IA'
    )
    ai_match_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Puntuación de Coincidencia IA',
        help_text='Puntuación de 0 a 100'
    )
    ai_analysis = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Análisis Completo de IA',
        help_text='Análisis detallado generado por IA'
    )
    
    # Notas internas
    internal_notes = models.TextField(
        blank=True,
        verbose_name='Notas Internas'
    )
    
    # Disponibilidad
    available_from = models.DateField(
        null=True,
        blank=True,
        verbose_name='Disponible desde'
    )
    notice_period_days = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Días de Preaviso'
    )
    
    # Redes sociales
    linkedin_url = models.URLField(
        blank=True,
        verbose_name='LinkedIn'
    )
    portfolio_url = models.URLField(
        blank=True,
        verbose_name='Portafolio'
    )
    github_url = models.URLField(
        blank=True,
        verbose_name='GitHub'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_candidates',
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
        verbose_name = 'Candidato'
        verbose_name_plural = 'Candidatos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['last_name', 'first_name']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Retorna el nombre completo"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def salary_expectation_range(self):
        """Retorna el rango salarial esperado formateado"""
        if self.salary_expectation_min and self.salary_expectation_max:
            return f"${self.salary_expectation_min:,.2f} - ${self.salary_expectation_max:,.2f} {self.salary_currency}"
        return "No especificado"
    
    @property
    def active_applications(self):
        """Cuenta las aplicaciones activas"""
        return self.candidate_profiles.exclude(
            status__in=['rejected', 'withdrawn']
        ).count()


class CandidateProfile(models.Model):
    """
    Modelo intermedio para la relación Candidato-Perfil
    Representa una aplicación específica de un candidato a un perfil
    """
    
    # Estados de la aplicación
    STATUS_APPLIED = 'applied'  # Aplicó
    STATUS_SCREENING = 'screening'  # En revisión
    STATUS_SHORTLISTED = 'shortlisted'  # Pre-seleccionado
    STATUS_INTERVIEW_SCHEDULED = 'interview_scheduled'  # Entrevista agendada
    STATUS_INTERVIEWED = 'interviewed'  # Entrevistado
    STATUS_OFFERED = 'offered'  # Oferta extendida
    STATUS_ACCEPTED = 'accepted'  # Oferta aceptada
    STATUS_REJECTED = 'rejected'  # Rechazado
    STATUS_WITHDRAWN = 'withdrawn'  # Retirado
    
    STATUS_CHOICES = [
        (STATUS_APPLIED, 'Aplicó'),
        (STATUS_SCREENING, 'En Revisión'),
        (STATUS_SHORTLISTED, 'Pre-seleccionado'),
        (STATUS_INTERVIEW_SCHEDULED, 'Entrevista Agendada'),
        (STATUS_INTERVIEWED, 'Entrevistado'),
        (STATUS_OFFERED, 'Oferta Extendida'),
        (STATUS_ACCEPTED, 'Oferta Aceptada'),
        (STATUS_REJECTED, 'Rechazado'),
        (STATUS_WITHDRAWN, 'Retirado'),
    ]
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='candidate_profiles',
        verbose_name='Candidato'
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='profile_candidates',
        verbose_name='Perfil'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_APPLIED,
        verbose_name='Estado de la Aplicación'
    )
    
    # Puntuación y evaluación
    match_percentage = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Porcentaje de Coincidencia',
        help_text='0-100'
    )
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Calificación General',
        help_text='0.00 - 5.00'
    )
    
    # Notas específicas para esta aplicación
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name='Razón de Rechazo'
    )
    
    # Fechas importantes
    applied_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Aplicación'
    )
    interview_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrevista'
    )
    offer_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Oferta'
    )
    
    class Meta:
        verbose_name = 'Aplicación de Candidato'
        verbose_name_plural = 'Aplicaciones de Candidatos'
        unique_together = ['candidate', 'profile']
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.candidate.full_name} → {self.profile.position_title}"


class CandidateDocument(models.Model):
    """
    Modelo para documentos de candidatos (CVs, cartas, etc.)
    """
    
    DOCUMENT_TYPE_CV = 'cv'
    DOCUMENT_TYPE_COVER_LETTER = 'cover_letter'
    DOCUMENT_TYPE_CERTIFICATE = 'certificate'
    DOCUMENT_TYPE_PORTFOLIO = 'portfolio'
    DOCUMENT_TYPE_OTHER = 'other'
    
    DOCUMENT_CHOICES = [
        (DOCUMENT_TYPE_CV, 'Curriculum Vitae'),
        (DOCUMENT_TYPE_COVER_LETTER, 'Carta de Presentación'),
        (DOCUMENT_TYPE_CERTIFICATE, 'Certificado'),
        (DOCUMENT_TYPE_PORTFOLIO, 'Portafolio'),
        (DOCUMENT_TYPE_OTHER, 'Otro'),
    ]
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Candidato'
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_CHOICES,
        default=DOCUMENT_TYPE_CV,
        verbose_name='Tipo de Documento'
    )
    file = models.FileField(
        upload_to='candidates/%Y/%m/',
        verbose_name='Archivo'
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name='Nombre Original del Archivo'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Descripción'
    )
    
    # Análisis de IA (para CVs)
    ai_extracted_text = models.TextField(
        blank=True,
        verbose_name='Texto Extraído por IA'
    )
    ai_parsed_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos Parseados por IA',
        help_text='Información estructurada extraída del CV'
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
        verbose_name = 'Documento del Candidato'
        verbose_name_plural = 'Documentos de Candidatos'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.candidate.full_name}"


class CandidateStatusHistory(models.Model):
    """
    Modelo para registrar el historial de cambios de estado de un candidato
    """
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Candidato'
    )
    from_status = models.CharField(
        max_length=20,
        choices=Candidate.STATUS_CHOICES,
        verbose_name='Estado Anterior'
    )
    to_status = models.CharField(
        max_length=20,
        choices=Candidate.STATUS_CHOICES,
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
        verbose_name = 'Historial de Estado del Candidato'
        verbose_name_plural = 'Historial de Estados de Candidatos'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.from_status} → {self.to_status}"


class CandidateNote(models.Model):
    """
    Modelo para notas y comentarios sobre candidatos
    """
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='Candidato'
    )
    note = models.TextField(
        verbose_name='Nota'
    )
    is_important = models.BooleanField(
        default=False,
        verbose_name='Nota Importante'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Creado por'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    class Meta:
        verbose_name = 'Nota del Candidato'
        verbose_name_plural = 'Notas de Candidatos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Nota de {self.candidate.full_name} - {self.created_at.strftime('%Y-%m-%d')}"