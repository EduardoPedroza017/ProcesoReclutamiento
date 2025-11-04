"""
Serializers para el sistema de evaluaciones
Maneja la serialización/deserialización de datos para la API REST
"""

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer,
    EvaluationComment
)


class EvaluationQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer para preguntas de evaluación
    """
    
    class Meta:
        model = EvaluationQuestion
        fields = [
            'id',
            'template',
            'question_text',
            'question_type',
            'options',
            'correct_answer',
            'points',
            'is_required',
            'order',
            'help_text',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_options(self, value):
        """Validar que las opciones sean una lista cuando aplique"""
        question_type = self.initial_data.get('question_type')
        if question_type == 'multiple_choice' and not isinstance(value, list):
            raise serializers.ValidationError(
                "Las opciones deben ser una lista para preguntas de opción múltiple"
            )
        return value


class EvaluationQuestionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar preguntas (sin respuestas correctas)
    Se usa cuando un candidato visualiza la evaluación
    """
    
    class Meta:
        model = EvaluationQuestion
        fields = [
            'id',
            'question_text',
            'question_type',
            'options',
            'points',
            'is_required',
            'order',
            'help_text'
        ]
        # Excluye correct_answer para que los candidatos no vean las respuestas


class EvaluationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer completo para plantillas de evaluación
    """
    questions = EvaluationQuestionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    total_questions = serializers.IntegerField(read_only=True)
    total_points = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    average_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = EvaluationTemplate
        fields = [
            'id',
            'title',
            'description',
            'category',
            'duration_minutes',
            'passing_score',
            'is_active',
            'is_template',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'profile',
            'questions',
            'total_questions',
            'total_points',
            'average_score'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Asignar el usuario actual como creador"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EvaluationTemplateListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar plantillas
    """
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    total_questions = serializers.IntegerField(read_only=True)
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    class Meta:
        model = EvaluationTemplate
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_display',
            'duration_minutes',
            'passing_score',
            'is_active',
            'total_questions',
            'created_by_name',
            'created_at'
        ]


class EvaluationAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer para respuestas de evaluación
    """
    question_text = serializers.CharField(
        source='question.question_text',
        read_only=True
    )
    question_type = serializers.CharField(
        source='question.question_type',
        read_only=True
    )
    question_points = serializers.DecimalField(
        source='question.points',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = EvaluationAnswer
        fields = [
            'id',
            'evaluation',
            'question',
            'question_text',
            'question_type',
            'question_points',
            'answer_text',
            'selected_option',
            'scale_value',
            'file_upload',
            'is_correct',
            'points_earned',
            'feedback',
            'answered_at'
        ]
        read_only_fields = [
            'id',
            'is_correct',
            'points_earned',
            'answered_at'
        ]
    
    def validate(self, data):
        """Validar que la respuesta sea apropiada para el tipo de pregunta"""
        question = data.get('question')
        
        if question.question_type == 'multiple_choice':
            if not data.get('selected_option'):
                raise serializers.ValidationError(
                    "Debe seleccionar una opción para preguntas de opción múltiple"
                )
        elif question.question_type == 'scale':
            if not data.get('scale_value'):
                raise serializers.ValidationError(
                    "Debe proporcionar un valor de escala"
                )
        elif question.question_type in ['short_text', 'long_text', 'code']:
            if not data.get('answer_text'):
                raise serializers.ValidationError(
                    "Debe proporcionar una respuesta de texto"
                )
        
        return data
    
    def create(self, validated_data):
        """Crear respuesta y verificar si es correcta"""
        answer = super().create(validated_data)
        answer.check_answer()
        return answer


class CandidateEvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer completo para evaluaciones de candidatos
    """
    template_title = serializers.CharField(
        source='template.title',
        read_only=True
    )
    template_category = serializers.CharField(
        source='template.get_category_display',
        read_only=True
    )
    candidate_name = serializers.CharField(
        source='candidate.full_name',
        read_only=True
    )
    candidate_email = serializers.EmailField(
        source='candidate.email',
        read_only=True
    )
    assigned_by_name = serializers.CharField(
        source='assigned_by.get_full_name',
        read_only=True
    )
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name',
        read_only=True
    )
    answers = EvaluationAnswerSerializer(many=True, read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = CandidateEvaluation
        fields = [
            'id',
            'template',
            'template_title',
            'template_category',
            'candidate',
            'candidate_name',
            'candidate_email',
            'assigned_by',
            'assigned_by_name',
            'reviewed_by',
            'reviewed_by_name',
            'status',
            'status_display',
            'assigned_at',
            'started_at',
            'completed_at',
            'reviewed_at',
            'expires_at',
            'auto_score',
            'manual_score',
            'final_score',
            'passed',
            'evaluator_comments',
            'internal_notes',
            'time_taken_minutes',
            'answers',
            'progress_percentage'
        ]
        read_only_fields = [
            'id',
            'assigned_at',
            'started_at',
            'completed_at',
            'reviewed_at',
            'auto_score',
            'progress_percentage'
        ]
    
    def create(self, validated_data):
        """Asignar el usuario actual como quien asigna la evaluación"""
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar timestamps según el estado"""
        new_status = validated_data.get('status')
        
        if new_status and new_status != instance.status:
            if new_status == 'in_progress' and not instance.started_at:
                instance.started_at = timezone.now()
            elif new_status == 'completed' and not instance.completed_at:
                instance.completed_at = timezone.now()
                # Calcular puntuación automáticamente
                instance.calculate_score()
            elif new_status == 'reviewed' and not instance.reviewed_at:
                instance.reviewed_at = timezone.now()
                validated_data['reviewed_by'] = self.context['request'].user
        
        return super().update(instance, validated_data)


class CandidateEvaluationListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar evaluaciones
    """
    template_title = serializers.CharField(source='template.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = CandidateEvaluation
        fields = [
            'id',
            'template',
            'template_title',
            'candidate',
            'candidate_name',
            'status',
            'status_display',
            'assigned_at',
            'completed_at',
            'final_score',
            'passed',
            'progress_percentage'
        ]


class EvaluationCommentSerializer(serializers.ModelSerializer):
    """
    Serializer para comentarios de evaluación
    """
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = EvaluationComment
        fields = [
            'id',
            'evaluation',
            'user',
            'user_name',
            'comment',
            'is_internal',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Asignar el usuario actual"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class EvaluationStartSerializer(serializers.Serializer):
    """
    Serializer para iniciar una evaluación
    """
    evaluation_id = serializers.IntegerField()


class EvaluationSubmitSerializer(serializers.Serializer):
    """
    Serializer para enviar respuestas de evaluación
    """
    answers = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate_answers(self, value):
        """Validar formato de respuestas"""
        for answer in value:
            if 'question_id' not in answer:
                raise serializers.ValidationError(
                    "Cada respuesta debe incluir question_id"
                )
        return value


class EvaluationReviewSerializer(serializers.Serializer):
    """
    Serializer para revisar y calificar evaluaciones
    """
    manual_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0'),
        max_value=Decimal('100')
    )
    evaluator_comments = serializers.CharField(required=False, allow_blank=True)
    internal_notes = serializers.CharField(required=False, allow_blank=True)
    
    # Calificación individual de respuestas
    answer_feedback = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class EvaluationStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de evaluaciones
    """
    total_evaluations = serializers.IntegerField()
    completed_evaluations = serializers.IntegerField()
    pending_evaluations = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    pass_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_completion_time = serializers.IntegerField()