"""
Modelos para el sistema de evaluaciones
Permite crear plantillas de evaluación, aplicarlas a candidatos y gestionar resultados
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.accounts.models import User


class EvaluationTemplate(models.Model):
    """
    Plantilla de evaluación reutilizable
    Ejemplo: "Evaluación Técnica Python", "Evaluación de Liderazgo", etc.
    """
    
    CATEGORY_CHOICES = [
        ('technical', 'Técnica'),
        ('soft_skills', 'Habilidades Blandas'),
        ('leadership', 'Liderazgo'),
        ('cultural_fit', 'Ajuste Cultural'),
        ('language', 'Idiomas'),
        ('other', 'Otro'),
    ]
    
    title = models.CharField(
        _('título'),
        max_length=200,
        help_text='Nombre de la evaluación (ej: "Evaluación Python Senior")'
    )
    description = models.TextField(
        _('descripción'),
        help_text='Descripción detallada del propósito de esta evaluación'
    )
    category = models.CharField(
        _('categoría'),
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='technical'
    )
    
    # Configuración
    duration_minutes = models.PositiveIntegerField(
        _('duración (minutos)'),
        default=60,
        help_text='Tiempo estimado para completar la evaluación'
    )
    passing_score = models.DecimalField(
        _('puntuación mínima'),
        max_digits=5,
        decimal_places=2,
        default=70.00,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text='Puntuación mínima para aprobar (0-100)'
    )
    
    # Configuración de disponibilidad
    is_active = models.BooleanField(
        _('activa'),
        default=True,
        help_text='Si está disponible para ser asignada'
    )
    is_template = models.BooleanField(
        _('es plantilla'),
        default=True,
        help_text='Si es una plantilla reutilizable o evaluación única'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_evaluation_templates',
        verbose_name=_('creado por')
    )
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    
    # Para asociar con perfiles específicos
    profile = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='evaluation_templates',
        verbose_name=_('perfil'),
        help_text='Perfil de reclutamiento asociado (opcional)'
    )
    
    class Meta:
        verbose_name = _('plantilla de evaluación')
        verbose_name_plural = _('plantillas de evaluación')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    @property
    def total_questions(self):
        """Total de preguntas en esta evaluación"""
        return self.questions.count()
    
    @property
    def total_points(self):
        """Total de puntos posibles en esta evaluación"""
        return self.questions.aggregate(
            total=models.Sum('points')
        )['total'] or 0
    
    @property
    def average_score(self):
        """Puntuación promedio de todas las evaluaciones completadas"""
        completed = self.evaluations.filter(status='completed')
        if not completed.exists():
            return None
        return completed.aggregate(
            avg=models.Avg('final_score')
        )['avg']


class EvaluationQuestion(models.Model):
    """
    Pregunta individual dentro de una evaluación
    """
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Opción Múltiple'),
        ('true_false', 'Verdadero/Falso'),
        ('short_text', 'Texto Corto'),
        ('long_text', 'Texto Largo'),
        ('scale', 'Escala (1-10)'),
        ('code', 'Código'),
        ('file_upload', 'Subir Archivo'),
    ]
    
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('plantilla')
    )
    
    # Contenido de la pregunta
    question_text = models.TextField(
        _('pregunta'),
        help_text='El texto de la pregunta'
    )
    question_type = models.CharField(
        _('tipo de pregunta'),
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='multiple_choice'
    )
    
    # Para preguntas de opción múltiple o verdadero/falso
    options = models.JSONField(
        _('opciones'),
        default=list,
        blank=True,
        help_text='Lista de opciones para preguntas de opción múltiple. Ejemplo: ["Opción A", "Opción B"]'
    )
    correct_answer = models.JSONField(
        _('respuesta correcta'),
        null=True,
        blank=True,
        help_text='Respuesta correcta o lista de respuestas correctas para auto-calificación'
    )
    
    # Puntuación
    points = models.DecimalField(
        _('puntos'),
        max_digits=5,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Puntos que vale esta pregunta'
    )
    
    # Configuración
    is_required = models.BooleanField(
        _('obligatoria'),
        default=True
    )
    order = models.PositiveIntegerField(
        _('orden'),
        default=0,
        help_text='Orden de aparición en la evaluación'
    )
    
    # Ayuda adicional
    help_text = models.TextField(
        _('texto de ayuda'),
        blank=True,
        help_text='Instrucciones o aclaraciones adicionales para el candidato'
    )
    
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('pregunta de evaluación')
        verbose_name_plural = _('preguntas de evaluación')
        ordering = ['template', 'order']
        indexes = [
            models.Index(fields=['template', 'order']),
        ]
    
    def __str__(self):
        return f"{self.template.title} - Pregunta {self.order}: {self.question_text[:50]}"
    
    def is_auto_gradable(self):
        """Determina si la pregunta puede calificarse automáticamente"""
        return self.question_type in ['multiple_choice', 'true_false', 'scale']


class CandidateEvaluation(models.Model):
    """
    Instancia de una evaluación asignada a un candidato específico
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('reviewed', 'Revisada'),
        ('expired', 'Expirada'),
    ]
    
    # Relaciones
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.PROTECT,
        related_name='evaluations',
        verbose_name=_('plantilla')
    )
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_('candidato')
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_evaluations',
        verbose_name=_('asignado por')
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_evaluations',
        verbose_name=_('revisado por')
    )
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Fechas
    assigned_at = models.DateTimeField(
        _('fecha de asignación'),
        auto_now_add=True
    )
    started_at = models.DateTimeField(
        _('fecha de inicio'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        _('fecha de finalización'),
        null=True,
        blank=True
    )
    reviewed_at = models.DateTimeField(
        _('fecha de revisión'),
        null=True,
        blank=True
    )
    expires_at = models.DateTimeField(
        _('fecha de expiración'),
        null=True,
        blank=True,
        help_text='Fecha límite para completar la evaluación'
    )
    
    # Puntuación
    auto_score = models.DecimalField(
        _('puntuación automática'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text='Puntuación calculada automáticamente'
    )
    manual_score = models.DecimalField(
        _('puntuación manual'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text='Puntuación ajustada por el evaluador'
    )
    final_score = models.DecimalField(
        _('puntuación final'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    
    # Resultado
    passed = models.BooleanField(
        _('aprobado'),
        null=True,
        blank=True
    )
    
    # Feedback
    evaluator_comments = models.TextField(
        _('comentarios del evaluador'),
        blank=True,
        help_text='Comentarios y retroalimentación para el candidato'
    )
    internal_notes = models.TextField(
        _('notas internas'),
        blank=True,
        help_text='Notas internas no visibles para el candidato'
    )
    
    # Tiempo de completado
    time_taken_minutes = models.PositiveIntegerField(
        _('tiempo tomado (minutos)'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('evaluación de candidato')
        verbose_name_plural = _('evaluaciones de candidatos')
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['status', 'assigned_at']),
            models.Index(fields=['candidate', 'status']),
            models.Index(fields=['template']),
        ]
        unique_together = [['candidate', 'template', 'assigned_at']]
    
    def __str__(self):
        return f"{self.candidate} - {self.template.title} ({self.get_status_display()})"
    
    def calculate_score(self):
        """
        Calcula la puntuación automática basada en respuestas correctas
        """
        if self.status != 'completed':
            return None
        
        total_points = 0
        earned_points = 0
        
        for answer in self.answers.all():
            question = answer.question
            total_points += float(question.points)
            
            # Solo preguntas auto-calificables
            if question.is_auto_gradable():
                if answer.is_correct:
                    earned_points += float(question.points)
        
        if total_points > 0:
            score = (earned_points / total_points) * 100
            self.auto_score = round(score, 2)
            self.final_score = self.manual_score if self.manual_score else self.auto_score
            self.passed = self.final_score >= float(self.template.passing_score)
            self.save(update_fields=['auto_score', 'final_score', 'passed'])
            return self.final_score
        
        return None
    
    @property
    def progress_percentage(self):
        """Porcentaje de progreso en la evaluación"""
        total = self.template.total_questions
        answered = self.answers.filter(answer_text__isnull=False).count()
        return (answered / total * 100) if total > 0 else 0


class EvaluationAnswer(models.Model):
    """
    Respuesta de un candidato a una pregunta específica
    """
    
    evaluation = models.ForeignKey(
        CandidateEvaluation,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('evaluación')
    )
    question = models.ForeignKey(
        EvaluationQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('pregunta')
    )
    
    # Respuesta del candidato
    answer_text = models.TextField(
        _('respuesta'),
        blank=True,
        help_text='Respuesta en texto del candidato'
    )
    selected_option = models.CharField(
        _('opción seleccionada'),
        max_length=500,
        blank=True,
        help_text='Para preguntas de opción múltiple'
    )
    scale_value = models.PositiveIntegerField(
        _('valor de escala'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Para preguntas de escala 1-10'
    )
    file_upload = models.FileField(
        _('archivo subido'),
        upload_to='evaluations/answers/%Y/%m/',
        null=True,
        blank=True
    )
    
    # Calificación
    is_correct = models.BooleanField(
        _('es correcta'),
        null=True,
        blank=True,
        help_text='Si la respuesta es correcta (para auto-calificación)'
    )
    points_earned = models.DecimalField(
        _('puntos obtenidos'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Feedback
    feedback = models.TextField(
        _('retroalimentación'),
        blank=True,
        help_text='Comentarios del evaluador sobre esta respuesta'
    )
    
    answered_at = models.DateTimeField(
        _('fecha de respuesta'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('respuesta de evaluación')
        verbose_name_plural = _('respuestas de evaluación')
        ordering = ['evaluation', 'question__order']
        unique_together = [['evaluation', 'question']]
        indexes = [
            models.Index(fields=['evaluation', 'question']),
        ]
    
    def __str__(self):
        return f"{self.evaluation.candidate} - {self.question.question_text[:30]}"
    
    def check_answer(self):
        """
        Verifica si la respuesta es correcta (solo para preguntas auto-calificables)
        """
        if not self.question.is_auto_gradable():
            return None
        
        if self.question.question_type == 'multiple_choice':
            self.is_correct = self.selected_option == self.question.correct_answer
        elif self.question.question_type == 'true_false':
            self.is_correct = self.selected_option.lower() == str(self.question.correct_answer).lower()
        elif self.question.question_type == 'scale':
            # Para escalas, la respuesta es correcta si está dentro de un rango aceptable
            if self.question.correct_answer:
                target = int(self.question.correct_answer)
                self.is_correct = abs(self.scale_value - target) <= 1
        
        # Asignar puntos
        if self.is_correct:
            self.points_earned = self.question.points
        else:
            self.points_earned = 0
        
        self.save(update_fields=['is_correct', 'points_earned'])
        return self.is_correct


class EvaluationComment(models.Model):
    """
    Comentarios y retroalimentación sobre evaluaciones
    """
    
    evaluation = models.ForeignKey(
        CandidateEvaluation,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('evaluación')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evaluation_comments',
        verbose_name=_('usuario')
    )
    
    comment = models.TextField(_('comentario'))
    is_internal = models.BooleanField(
        _('es interno'),
        default=False,
        help_text='Si es visible solo internamente'
    )
    
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('comentario de evaluación')
        verbose_name_plural = _('comentarios de evaluación')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comentario de {self.user} en {self.evaluation}"