"""
Modelos para el servicio de IA
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.profiles.models import Profile
from apps.candidates.models import Candidate

User = get_user_model()


# =======================
# 1) Historial general (ya lo tenías)
# =======================
class AIAnalysisHistory(models.Model):
    """
    Historial de análisis realizados por IA
    Guarda un registro de todas las interacciones con Claude API
    """
    ANALYSIS_TRANSCRIPTION = 'transcription'
    ANALYSIS_CV_PARSING = 'cv_parsing'
    ANALYSIS_PROFILE_GEN = 'profile_generation'
    ANALYSIS_MATCHING = 'candidate_matching'
    ANALYSIS_EVALUATION = 'evaluation_generation'

    ANALYSIS_TYPE_CHOICES = [
        (ANALYSIS_TRANSCRIPTION, 'Transcripción de Reunión'),
        (ANALYSIS_CV_PARSING, 'Análisis de CV'),
        (ANALYSIS_PROFILE_GEN, 'Generación de Perfil'),
        (ANALYSIS_MATCHING, 'Matching de Candidatos'),
        (ANALYSIS_EVALUATION, 'Generación de Evaluación'),
    ]

    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPE_CHOICES, verbose_name='Tipo de Análisis')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_analyses', verbose_name='Perfil Relacionado')
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_analyses', verbose_name='Candidato Relacionado')
    input_data = models.JSONField(verbose_name='Datos de Entrada', help_text='Datos enviados a Claude API')
    output_data = models.JSONField(verbose_name='Resultado del Análisis', help_text='Respuesta de Claude API')
    tokens_used = models.IntegerField(default=0, verbose_name='Tokens Utilizados')
    processing_time = models.FloatField(default=0, verbose_name='Tiempo de Procesamiento (segundos)', help_text='Tiempo en segundos que tomó el análisis')
    model_used = models.CharField(max_length=100, default='claude-3-opus-20240229', verbose_name='Modelo de IA Utilizado')
    success = models.BooleanField(default=True, verbose_name='Exitoso')
    error_message = models.TextField(blank=True, verbose_name='Mensaje de Error')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        verbose_name = 'Análisis de IA'
        verbose_name_plural = 'Análisis de IA'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis_type']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['profile']),
            models.Index(fields=['candidate']),
        ]

    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def cost_estimate(self):
        # Estimación simple (asumiendo 50/50 input/output)
        input_price_per_1k = 0.015
        output_price_per_1k = 0.075
        estimated_cost = (self.tokens_used / 1000) * (input_price_per_1k + output_price_per_1k) / 2
        return round(estimated_cost, 4)


# =======================
# 2) Análisis de CV (requerido por views/serializers/tasks)
# =======================
class CVAnalysis(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PROCESSING, 'Procesando'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_FAILED, 'Fallido'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='cv_analyses')
    document_file = models.FileField(upload_to='cv_uploads/')
    extracted_text = models.TextField(blank=True, default='')
    parsed_data = models.JSONField(default=dict, blank=True)
    ai_summary = models.TextField(blank=True, default='')
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    recommended_positions = models.JSONField(default=list, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cv_analyses_created')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['candidate']),
        ]

    def __str__(self):
        return f"CVAnalysis #{self.pk} - {self.candidate.full_name if self.candidate_id else ''}"


# =======================
# 3) Matching Candidato–Perfil (requerido por views/serializers/tasks)
# =======================
class CandidateProfileMatching(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='matchings')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='matchings')

    overall_score = models.IntegerField(default=0)
    technical_skills_score = models.IntegerField(default=0)
    soft_skills_score = models.IntegerField(default=0)
    experience_score = models.IntegerField(default=0)
    education_score = models.IntegerField(default=0)
    location_score = models.IntegerField(default=0)
    salary_score = models.IntegerField(default=0)

    matching_analysis = models.TextField(blank=True, default='')
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True, default='')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='matchings_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-overall_score', '-created_at']
        unique_together = [('candidate', 'profile')]
        indexes = [
            models.Index(fields=['-overall_score']),
            models.Index(fields=['candidate']),
            models.Index(fields=['profile']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Matching {self.candidate.full_name if self.candidate_id else ''} → {self.profile.position_title if self.profile_id else ''}"

    @property
    def is_good_match(self):
        # Umbral libre: 70 como “bueno” (coincide con tu vista/serializer)
        return self.overall_score >= 70


# =======================
# 4) Generación de Perfiles (requerido por views/serializers/tasks)
# =======================
class ProfileGeneration(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PROCESSING, 'Procesando'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_FAILED, 'Fallido'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile_generations')
    meeting_transcription = models.TextField()
    additional_notes = models.TextField(blank=True, default='')
    generated_profile_data = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='profile_generations_created')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['profile']),
        ]

    def __str__(self):
        return f"ProfileGeneration #{self.pk}"


# =======================
# 5) Log de IA (requerido por views/serializers/tasks)
# =======================
class AILog(models.Model):
    ACTION_CV_ANALYSIS = 'cv_analysis'
    ACTION_MATCHING = 'matching'
    ACTION_PROFILE_GENERATION = 'profile_generation'
    ACTION_SUMMARIZATION = 'summarization'

    ACTION_CHOICES = [
        (ACTION_CV_ANALYSIS, 'Análisis de CV'),
        (ACTION_MATCHING, 'Matching'),
        (ACTION_PROFILE_GENERATION, 'Generación de Perfil'),
        (ACTION_SUMMARIZATION, 'Resumen de Candidato'),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    prompt = models.TextField(blank=True, default='')
    response = models.TextField(blank=True, default='')
    model_used = models.CharField(max_length=100, blank=True, default='claude-3-sonnet-20240229')

    tokens_input = models.IntegerField(default=0)
    tokens_output = models.IntegerField(default=0)
    execution_time = models.FloatField(default=0)

    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default='')

    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_logs')
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_logs')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ai_logs_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['candidate']),
            models.Index(fields=['profile']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} #{self.pk}"

    @property
    def total_tokens(self):
        return (self.tokens_input or 0) + (self.tokens_output or 0)


# =======================
# 6) Plantillas de Prompt (ya lo tenías)
# =======================
class AIPromptTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre de la Plantilla')
    analysis_type = models.CharField(max_length=50, choices=AIAnalysisHistory.ANALYSIS_TYPE_CHOICES, verbose_name='Tipo de Análisis')
    prompt_template = models.TextField(verbose_name='Plantilla del Prompt', help_text='Use {variables} para valores dinámicos')
    system_message = models.TextField(blank=True, verbose_name='Mensaje del Sistema', help_text='Instrucciones del sistema para Claude')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    description = models.TextField(blank=True, verbose_name='Descripción')
    max_tokens = models.IntegerField(default=4000, verbose_name='Máximo de Tokens')
    temperature = models.FloatField(default=0.7, verbose_name='Temperatura', help_text='0.0 = más determinístico, 1.0 = más creativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Creado por')

    class Meta:
        verbose_name = 'Plantilla de Prompt'
        verbose_name_plural = 'Plantillas de Prompts'
        ordering = ['analysis_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_analysis_type_display()})"


# =======================
# 7) Configuración (ya lo tenías)
# =======================
class AIConfiguration(models.Model):
    api_key_encrypted = models.TextField(verbose_name='API Key (Encriptada)', help_text='Se almacena de forma segura')
    default_model = models.CharField(max_length=100, default='claude-3-opus-20240229', verbose_name='Modelo Predeterminado')
    max_tokens_per_request = models.IntegerField(default=4000, verbose_name='Máximo de Tokens por Solicitud')
    daily_token_limit = models.IntegerField(default=1000000, verbose_name='Límite Diario de Tokens')
    tokens_used_today = models.IntegerField(default=0, verbose_name='Tokens Usados Hoy')
    last_reset_date = models.DateField(auto_now_add=True, verbose_name='Fecha del Último Reset')

    auto_analyze_cvs = models.BooleanField(default=True, verbose_name='Analizar CVs Automáticamente')
    auto_generate_profiles = models.BooleanField(default=False, verbose_name='Generar Perfiles Automáticamente')
    auto_match_candidates = models.BooleanField(default=True, verbose_name='Match Automático de Candidatos')

    enable_async_processing = models.BooleanField(default=True, verbose_name='Procesamiento Asíncrono (Celery)')
    retry_on_failure = models.BooleanField(default=True, verbose_name='Reintentar en Caso de Fallo')
    max_retries = models.IntegerField(default=3, verbose_name='Máximo de Reintentos')

    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Actualización')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Actualizado por')

    class Meta:
        verbose_name = 'Configuración de IA'
        verbose_name_plural = 'Configuración de IA'

    def __str__(self):
        return f"Configuración de IA - {self.updated_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def reset_daily_tokens(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.tokens_used_today = 0
            self.last_reset_date = today
            self.save()

    def can_use_tokens(self, tokens_required):
        self.reset_daily_tokens()
        return self.tokens_used_today + tokens_required <= self.daily_token_limit

    def use_tokens(self, tokens_used):
        self.reset_daily_tokens()
        self.tokens_used_today += tokens_used
        self.save()
