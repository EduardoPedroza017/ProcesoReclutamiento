"""
Configuración del panel de administración para el sistema de evaluaciones
Permite gestionar evaluaciones, plantillas y preguntas desde el admin de Django
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer,
    EvaluationComment
)


class EvaluationQuestionInline(admin.TabularInline):
    """
    Inline para preguntas dentro de la plantilla de evaluación
    Permite agregar preguntas directamente desde la plantilla
    """
    model = EvaluationQuestion
    extra = 1
    fields = [
        'order',
        'question_text',
        'question_type',
        'points',
        'is_required'
    ]
    ordering = ['order']


@admin.register(EvaluationTemplate)
class EvaluationTemplateAdmin(admin.ModelAdmin):
    """
    Administración de plantillas de evaluación
    """
    list_display = [
        'title',
        'category_badge',
        'duration_minutes',
        'passing_score',
        'total_questions_count',
        'total_points_display',
        'is_active_badge',
        'created_by',
        'created_at'
    ]
    list_filter = [
        'category',
        'is_active',
        'is_template',
        'created_at'
    ]
    search_fields = [
        'title',
        'description',
        'created_by__email',
        'created_by__first_name',
        'created_by__last_name'
    ]
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at',
        'total_questions_count',
        'total_points_display',
        'average_score_display',
        'usage_stats'
    ]
    fieldsets = (
        ('Información General', {
            'fields': (
                'title',
                'description',
                'category',
                'profile'
            )
        }),
        ('Configuración', {
            'fields': (
                'duration_minutes',
                'passing_score',
                'is_active',
                'is_template'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'total_questions_count',
                'total_points_display',
                'average_score_display',
                'usage_stats'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    inlines = [EvaluationQuestionInline]
    actions = ['duplicate_templates', 'activate_templates', 'deactivate_templates']
    
    def save_model(self, request, obj, form, change):
        """Asignar el usuario actual como creador si es nuevo"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def category_badge(self, obj):
        """Badge con color para la categoría"""
        colors = {
            'technical': '#3498db',
            'soft_skills': '#2ecc71',
            'leadership': '#9b59b6',
            'cultural_fit': '#e74c3c',
            'language': '#f39c12',
            'other': '#95a5a6'
        }
        color = colors.get(obj.category, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Categoría'
    
    def is_active_badge(self, obj):
        """Badge para el estado activo/inactivo"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Activa</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactiva</span>'
        )
    is_active_badge.short_description = 'Estado'
    
    def total_questions_count(self, obj):
        """Total de preguntas"""
        return obj.total_questions
    total_questions_count.short_description = 'Total Preguntas'
    
    def total_points_display(self, obj):
        """Total de puntos posibles"""
        return f"{obj.total_points} pts"
    total_points_display.short_description = 'Puntos Totales'
    
    def average_score_display(self, obj):
        """Puntuación promedio"""
        avg = obj.average_score
        if avg is None:
            return "N/A"
        return f"{avg:.2f}%"
    average_score_display.short_description = 'Puntuación Promedio'
    
    def usage_stats(self, obj):
        """Estadísticas de uso de la plantilla"""
        total = obj.evaluations.count()
        completed = obj.evaluations.filter(status='completed').count()
        pending = obj.evaluations.filter(status='pending').count()
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '<strong>Total usos:</strong> {}<br>'
            '<strong>Completadas:</strong> {}<br>'
            '<strong>Pendientes:</strong> {}'
            '</div>',
            total, completed, pending
        )
    usage_stats.short_description = 'Uso'
    
    def duplicate_templates(self, request, queryset):
        """Acción para duplicar plantillas seleccionadas"""
        count = 0
        for template in queryset:
            new_template = EvaluationTemplate.objects.create(
                title=f"{template.title} (Copia)",
                description=template.description,
                category=template.category,
                duration_minutes=template.duration_minutes,
                passing_score=template.passing_score,
                is_active=False,
                is_template=True,
                created_by=request.user
            )
            
            # Copiar preguntas
            for question in template.questions.all():
                EvaluationQuestion.objects.create(
                    template=new_template,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    options=question.options,
                    correct_answer=question.correct_answer,
                    points=question.points,
                    is_required=question.is_required,
                    order=question.order,
                    help_text=question.help_text
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


@admin.register(EvaluationQuestion)
class EvaluationQuestionAdmin(admin.ModelAdmin):
    """
    Administración de preguntas de evaluación
    """
    list_display = [
        'template',
        'order',
        'question_preview',
        'question_type_badge',
        'points',
        'is_required',
        'is_auto_gradable_badge'
    ]
    list_filter = [
        'question_type',
        'is_required',
        'template__category',
        'created_at'
    ]
    search_fields = [
        'question_text',
        'template__title'
    ]
    readonly_fields = ['created_at', 'updated_at', 'is_auto_gradable_badge']
    fieldsets = (
        ('Pregunta', {
            'fields': (
                'template',
                'question_text',
                'question_type',
                'help_text'
            )
        }),
        ('Opciones y Respuesta', {
            'fields': (
                'options',
                'correct_answer'
            )
        }),
        ('Configuración', {
            'fields': (
                'points',
                'is_required',
                'order'
            )
        }),
        ('Información', {
            'fields': (
                'is_auto_gradable_badge',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def question_preview(self, obj):
        """Vista previa de la pregunta"""
        text = obj.question_text
        if len(text) > 80:
            text = text[:80] + '...'
        return text
    question_preview.short_description = 'Pregunta'
    
    def question_type_badge(self, obj):
        """Badge para el tipo de pregunta"""
        colors = {
            'multiple_choice': '#3498db',
            'true_false': '#2ecc71',
            'short_text': '#f39c12',
            'long_text': '#e67e22',
            'scale': '#9b59b6',
            'code': '#34495e',
            'file_upload': '#95a5a6'
        }
        color = colors.get(obj.question_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_question_type_display()
        )
    question_type_badge.short_description = 'Tipo'
    
    def is_auto_gradable_badge(self, obj):
        """Indicador de auto-calificable"""
        if obj.is_auto_gradable():
            return format_html('<span style="color: green;">✓ Auto-calificable</span>')
        return format_html('<span style="color: orange;">✗ Requiere revisión manual</span>')
    is_auto_gradable_badge.short_description = 'Calificación'


class EvaluationAnswerInline(admin.TabularInline):
    """
    Inline para respuestas dentro de la evaluación
    """
    model = EvaluationAnswer
    extra = 0
    readonly_fields = [
        'question',
        'answer_text',
        'selected_option',
        'scale_value',
        'is_correct',
        'points_earned',
        'answered_at'
    ]
    can_delete = False
    fields = [
        'question',
        'answer_text',
        'is_correct',
        'points_earned',
        'feedback'
    ]


@admin.register(CandidateEvaluation)
class CandidateEvaluationAdmin(admin.ModelAdmin):
    """
    Administración de evaluaciones de candidatos
    """
    list_display = [
        'candidate',
        'template',
        'status_badge',
        'final_score_display',
        'passed_badge',
        'assigned_by',
        'assigned_at',
        'completed_at'
    ]
    list_filter = [
        'status',
        'passed',
        'template__category',
        'assigned_at',
        'completed_at'
    ]
    search_fields = [
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'template__title'
    ]
    readonly_fields = [
        'assigned_by',
        'assigned_at',
        'started_at',
        'completed_at',
        'reviewed_at',
        'reviewed_by',
        'auto_score',
        'final_score',
        'passed',
        'time_taken_minutes',
        'progress_percentage_display',
        'answers_summary'
    ]
    fieldsets = (
        ('Información', {
            'fields': (
                'template',
                'candidate',
                'status'
            )
        }),
        ('Fechas', {
            'fields': (
                'assigned_at',
                'assigned_by',
                'started_at',
                'completed_at',
                'reviewed_at',
                'reviewed_by',
                'expires_at'
            )
        }),
        ('Puntuación', {
            'fields': (
                'auto_score',
                'manual_score',
                'final_score',
                'passed',
                'time_taken_minutes'
            )
        }),
        ('Feedback', {
            'fields': (
                'evaluator_comments',
                'internal_notes'
            )
        }),
        ('Resumen', {
            'fields': (
                'progress_percentage_display',
                'answers_summary'
            ),
            'classes': ('collapse',)
        })
    )
    inlines = [EvaluationAnswerInline]
    actions = ['mark_as_completed', 'mark_as_reviewed']
    
    def status_badge(self, obj):
        """Badge de color para el estado"""
        colors = {
            'pending': '#f39c12',
            'in_progress': '#3498db',
            'completed': '#2ecc71',
            'reviewed': '#9b59b6',
            'expired': '#e74c3c'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def final_score_display(self, obj):
        """Mostrar puntuación con color"""
        if obj.final_score is None:
            return "N/A"
        
        score = float(obj.final_score)
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}%</span>',
            color,
            score
        )
    final_score_display.short_description = 'Puntuación Final'
    
    def passed_badge(self, obj):
        """Badge de aprobado/reprobado"""
        if obj.passed is None:
            return "Pendiente"
        if obj.passed:
            return format_html('<span style="color: green;">✓ Aprobado</span>')
        return format_html('<span style="color: red;">✗ Reprobado</span>')
    passed_badge.short_description = 'Resultado'
    
    def progress_percentage_display(self, obj):
        """Barra de progreso"""
        progress = obj.progress_percentage
        return format_html(
            '<div style="width: 200px; background-color: #ecf0f1; border-radius: 5px;">'
            '<div style="width: {}%; background-color: #3498db; padding: 5px; '
            'border-radius: 5px; text-align: center; color: white; font-size: 11px;">'
            '{:.1f}%'
            '</div></div>',
            progress, progress
        )
    progress_percentage_display.short_description = 'Progreso'
    
    def answers_summary(self, obj):
        """Resumen de respuestas"""
        total = obj.answers.count()
        correct = obj.answers.filter(is_correct=True).count()
        incorrect = obj.answers.filter(is_correct=False).count()
        pending = total - correct - incorrect
        
        return format_html(
            '<div style="line-height: 2;">'
            '<strong>Total respuestas:</strong> {}<br>'
            '<span style="color: green;">✓ Correctas: {}</span><br>'
            '<span style="color: red;">✗ Incorrectas: {}</span><br>'
            '<span style="color: orange;">⊙ Pendientes: {}</span>'
            '</div>',
            total, correct, incorrect, pending
        )
    answers_summary.short_description = 'Resumen de Respuestas'
    
    def mark_as_completed(self, request, queryset):
        """Marcar evaluaciones como completadas"""
        from django.utils import timezone
        updated = 0
        for evaluation in queryset:
            if evaluation.status not in ['completed', 'reviewed']:
                evaluation.status = 'completed'
                evaluation.completed_at = timezone.now()
                evaluation.calculate_score()
                evaluation.save()
                updated += 1
        
        self.message_user(request, f"{updated} evaluación(es) marcada(s) como completada(s).")
    mark_as_completed.short_description = "Marcar como completadas"
    
    def mark_as_reviewed(self, request, queryset):
        """Marcar evaluaciones como revisadas"""
        from django.utils import timezone
        updated = 0
        for evaluation in queryset.filter(status='completed'):
            evaluation.status = 'reviewed'
            evaluation.reviewed_at = timezone.now()
            evaluation.reviewed_by = request.user
            evaluation.save()
            updated += 1
        
        self.message_user(request, f"{updated} evaluación(es) marcada(s) como revisada(s).")
    mark_as_reviewed.short_description = "Marcar como revisadas"


@admin.register(EvaluationAnswer)
class EvaluationAnswerAdmin(admin.ModelAdmin):
    """
    Administración de respuestas de evaluación
    """
    list_display = [
        'evaluation',
        'question_preview',
        'is_correct_badge',
        'points_earned',
        'answered_at'
    ]
    list_filter = [
        'is_correct',
        'question__question_type',
        'answered_at'
    ]
    search_fields = [
        'evaluation__candidate__first_name',
        'evaluation__candidate__last_name',
        'question__question_text',
        'answer_text'
    ]
    readonly_fields = ['answered_at', 'is_correct', 'points_earned']
    
    def question_preview(self, obj):
        """Vista previa de la pregunta"""
        text = obj.question.question_text
        if len(text) > 60:
            text = text[:60] + '...'
        return text
    question_preview.short_description = 'Pregunta'
    
    def is_correct_badge(self, obj):
        """Badge de correcto/incorrecto"""
        if obj.is_correct is None:
            return format_html('<span style="color: orange;">Pendiente</span>')
        if obj.is_correct:
            return format_html('<span style="color: green;">✓ Correcta</span>')
        return format_html('<span style="color: red;">✗ Incorrecta</span>')
    is_correct_badge.short_description = 'Estado'


@admin.register(EvaluationComment)
class EvaluationCommentAdmin(admin.ModelAdmin):
    """
    Administración de comentarios de evaluación
    """
    list_display = [
        'evaluation',
        'user',
        'comment_preview',
        'is_internal',
        'created_at'
    ]
    list_filter = [
        'is_internal',
        'created_at'
    ]
    search_fields = [
        'evaluation__candidate__first_name',
        'evaluation__candidate__last_name',
        'user__email',
        'comment'
    ]
    readonly_fields = ['user', 'created_at']
    
    def comment_preview(self, obj):
        """Vista previa del comentario"""
        text = obj.comment
        if len(text) > 60:
            text = text[:60] + '...'
        return text
    comment_preview.short_description = 'Comentario'