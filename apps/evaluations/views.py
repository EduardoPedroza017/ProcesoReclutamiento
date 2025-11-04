"""
Views para el sistema de evaluaciones
Maneja la lógica de negocio y endpoints de la API
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer,
    EvaluationComment
)
from .serializers import (
    EvaluationTemplateSerializer,
    EvaluationTemplateListSerializer,
    EvaluationQuestionSerializer,
    EvaluationQuestionListSerializer,
    CandidateEvaluationSerializer,
    CandidateEvaluationListSerializer,
    EvaluationAnswerSerializer,
    EvaluationCommentSerializer,
    EvaluationStartSerializer,
    EvaluationSubmitSerializer,
    EvaluationReviewSerializer,
    EvaluationStatsSerializer
)
from apps.accounts.permissions import IsAdminUser, IsDirectorOrAbove, IsSupervisorOrAbove


class EvaluationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de plantillas de evaluación
    
    Endpoints:
    - GET /api/evaluations/templates/ - Listar plantillas
    - POST /api/evaluations/templates/ - Crear plantilla
    - GET /api/evaluations/templates/{id}/ - Detalle de plantilla
    - PUT /api/evaluations/templates/{id}/ - Actualizar plantilla
    - DELETE /api/evaluations/templates/{id}/ - Eliminar plantilla
    - POST /api/evaluations/templates/{id}/duplicate/ - Duplicar plantilla
    - GET /api/evaluations/templates/{id}/statistics/ - Estadísticas de uso
    """
    
    queryset = EvaluationTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsDirectorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_template']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'duration_minutes']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return EvaluationTemplateListSerializer
        return EvaluationTemplateSerializer
    
    def get_queryset(self):
        """
        Filtrar plantillas según permisos:
        - Admin: ve todas
        - Director: ve todas las activas
        - Supervisor: ve solo las que le fueron asignadas
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'admin':
            return queryset
        elif user.role == 'director':
            return queryset.filter(is_active=True)
        else:  # supervisor
            # Solo plantillas usadas en evaluaciones asignadas a ellos
            return queryset.filter(
                Q(evaluations__assigned_by=user) |
                Q(evaluations__reviewed_by=user)
            ).distinct()
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicar una plantilla de evaluación con todas sus preguntas
        """
        template = self.get_object()
        
        # Crear copia de la plantilla
        new_template = EvaluationTemplate.objects.create(
            title=f"{template.title} (Copia)",
            description=template.description,
            category=template.category,
            duration_minutes=template.duration_minutes,
            passing_score=template.passing_score,
            is_active=False,  # Desactivada por defecto
            is_template=True,
            created_by=request.user
        )
        
        # Copiar todas las preguntas
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
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        Obtener estadísticas de uso de una plantilla
        """
        template = self.get_object()
        
        evaluations = CandidateEvaluation.objects.filter(template=template)
        completed = evaluations.filter(status='completed')
        
        stats = {
            'total_uses': evaluations.count(),
            'completed': completed.count(),
            'in_progress': evaluations.filter(status='in_progress').count(),
            'pending': evaluations.filter(status='pending').count(),
            'average_score': completed.aggregate(
                avg=Avg('final_score')
            )['avg'] or 0,
            'pass_rate': (
                completed.filter(passed=True).count() / completed.count() * 100
                if completed.count() > 0 else 0
            ),
            'average_time': completed.aggregate(
                avg=Avg('time_taken_minutes')
            )['avg'] or 0
        }
        
        return Response(stats)


class EvaluationQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de preguntas de evaluación
    
    Endpoints:
    - GET /api/evaluations/questions/ - Listar preguntas
    - POST /api/evaluations/questions/ - Crear pregunta
    - GET /api/evaluations/questions/{id}/ - Detalle de pregunta
    - PUT /api/evaluations/questions/{id}/ - Actualizar pregunta
    - DELETE /api/evaluations/questions/{id}/ - Eliminar pregunta
    - POST /api/evaluations/questions/bulk_create/ - Crear múltiples preguntas
    """
    
    queryset = EvaluationQuestion.objects.all()
    permission_classes = [IsAuthenticated, IsDirectorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['template', 'question_type', 'is_required']
    ordering_fields = ['order', 'points']
    ordering = ['template', 'order']
    
    def get_serializer_class(self):
        """Usar serializer sin respuestas correctas para candidatos"""
        if self.request.user.role == 'supervisor' and self.action == 'list':
            return EvaluationQuestionListSerializer
        return EvaluationQuestionSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Crear múltiples preguntas a la vez
        Body: {"template_id": 1, "questions": [...]}
        """
        template_id = request.data.get('template_id')
        questions_data = request.data.get('questions', [])
        
        if not template_id:
            return Response(
                {'error': 'template_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            template = EvaluationTemplate.objects.get(id=template_id)
        except EvaluationTemplate.DoesNotExist:
            return Response(
                {'error': 'Plantilla no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_questions = []
        for idx, question_data in enumerate(questions_data):
            question_data['template'] = template.id
            question_data['order'] = question_data.get('order', idx)
            serializer = self.get_serializer(data=question_data)
            if serializer.is_valid():
                question = serializer.save()
                created_questions.append(question)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(created_questions, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CandidateEvaluationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de evaluaciones de candidatos
    
    Endpoints principales:
    - GET /api/evaluations/candidate-evaluations/ - Listar evaluaciones
    - POST /api/evaluations/candidate-evaluations/ - Asignar evaluación
    - GET /api/evaluations/candidate-evaluations/{id}/ - Detalle
    - PUT /api/evaluations/candidate-evaluations/{id}/ - Actualizar
    - DELETE /api/evaluations/candidate-evaluations/{id}/ - Eliminar
    
    Acciones especiales:
    - POST /api/evaluations/candidate-evaluations/{id}/start/ - Iniciar evaluación
    - POST /api/evaluations/candidate-evaluations/{id}/submit/ - Enviar respuestas
    - POST /api/evaluations/candidate-evaluations/{id}/review/ - Revisar y calificar
    - POST /api/evaluations/candidate-evaluations/{id}/complete/ - Marcar como completada
    - GET /api/evaluations/candidate-evaluations/my_evaluations/ - Mis evaluaciones
    - GET /api/evaluations/candidate-evaluations/pending_reviews/ - Pendientes de revisión
    - GET /api/evaluations/candidate-evaluations/statistics/ - Estadísticas generales
    """
    
    queryset = CandidateEvaluation.objects.select_related(
        'template', 'candidate', 'assigned_by', 'reviewed_by'
    ).prefetch_related('answers', 'answers__question')
    permission_classes = [IsAuthenticated, IsSupervisorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'template', 'candidate', 'passed']
    search_fields = ['candidate__first_name', 'candidate__last_name', 'template__title']
    ordering_fields = ['assigned_at', 'completed_at', 'final_score']
    ordering = ['-assigned_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado para listados"""
        if self.action == 'list':
            return CandidateEvaluationListSerializer
        return CandidateEvaluationSerializer
    
    def get_queryset(self):
        """
        Filtrar evaluaciones según permisos:
        - Admin/Director: ven todas
        - Supervisor: solo las que asignó o debe revisar
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role in ['admin', 'director']:
            return queryset
        else:  # supervisor
            return queryset.filter(
                Q(assigned_by=user) | Q(reviewed_by=user)
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Iniciar una evaluación
        Cambia el estado a 'in_progress' y registra la hora de inicio
        """
        evaluation = self.get_object()
        
        if evaluation.status != 'pending':
            return Response(
                {'error': 'La evaluación ya fue iniciada o completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si no ha expirado
        if evaluation.expires_at and evaluation.expires_at < timezone.now():
            evaluation.status = 'expired'
            evaluation.save()
            return Response(
                {'error': 'La evaluación ha expirado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation.status = 'in_progress'
        evaluation.started_at = timezone.now()
        evaluation.save()
        
        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Enviar respuestas de una evaluación
        Body: {"answers": [{"question_id": 1, "answer_text": "...", ...}, ...]}
        """
        evaluation = self.get_object()
        
        if evaluation.status not in ['pending', 'in_progress']:
            return Response(
                {'error': 'La evaluación ya fue completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EvaluationSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        answers_data = serializer.validated_data['answers']
        
        # Guardar respuestas
        for answer_data in answers_data:
            question_id = answer_data.pop('question_id')
            
            try:
                question = EvaluationQuestion.objects.get(
                    id=question_id,
                    template=evaluation.template
                )
            except EvaluationQuestion.DoesNotExist:
                return Response(
                    {'error': f'Pregunta {question_id} no encontrada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear o actualizar respuesta
            answer, created = EvaluationAnswer.objects.update_or_create(
                evaluation=evaluation,
                question=question,
                defaults=answer_data
            )
            
            # Verificar respuesta si es auto-calificable
            answer.check_answer()
        
        # Marcar como completada
        evaluation.status = 'completed'
        evaluation.completed_at = timezone.now()
        
        # Calcular tiempo tomado
        if evaluation.started_at:
            time_diff = evaluation.completed_at - evaluation.started_at
            evaluation.time_taken_minutes = int(time_diff.total_seconds() / 60)
        
        evaluation.save()
        
        # Calcular puntuación automática
        evaluation.calculate_score()
        
        evaluation.refresh_from_db()
        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsDirectorOrAbove])
    def review(self, request, pk=None):
        """
        Revisar y calificar una evaluación
        Solo para Directores y Admins
        Body: {
            "manual_score": 85.5,
            "evaluator_comments": "...",
            "internal_notes": "...",
            "answer_feedback": [{"answer_id": 1, "feedback": "...", "points_earned": 5}, ...]
        }
        """
        evaluation = self.get_object()
        
        if evaluation.status != 'completed':
            return Response(
                {'error': 'La evaluación debe estar completada para ser revisada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EvaluationReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar puntuación y comentarios
        evaluation.manual_score = serializer.validated_data['manual_score']
        evaluation.final_score = evaluation.manual_score
        evaluation.passed = evaluation.final_score >= float(evaluation.template.passing_score)
        evaluation.evaluator_comments = serializer.validated_data.get('evaluator_comments', '')
        evaluation.internal_notes = serializer.validated_data.get('internal_notes', '')
        evaluation.status = 'reviewed'
        evaluation.reviewed_at = timezone.now()
        evaluation.reviewed_by = request.user
        evaluation.save()
        
        # Actualizar feedback de respuestas individuales
        answer_feedback = serializer.validated_data.get('answer_feedback', [])
        for feedback_data in answer_feedback:
            answer_id = feedback_data.get('answer_id')
            try:
                answer = EvaluationAnswer.objects.get(
                    id=answer_id,
                    evaluation=evaluation
                )
                answer.feedback = feedback_data.get('feedback', '')
                answer.points_earned = feedback_data.get('points_earned', answer.points_earned)
                answer.save()
            except EvaluationAnswer.DoesNotExist:
                continue
        
        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Marcar evaluación como completada manualmente
        Útil si el candidato completó la evaluación offline
        """
        evaluation = self.get_object()
        
        if evaluation.status == 'completed':
            return Response(
                {'error': 'La evaluación ya está completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        evaluation.status = 'completed'
        evaluation.completed_at = timezone.now()
        evaluation.save()
        
        serializer = self.get_serializer(evaluation)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_evaluations(self, request):
        """
        Obtener evaluaciones asignadas por el usuario actual
        """
        evaluations = self.get_queryset().filter(assigned_by=request.user)
        serializer = self.get_serializer(evaluations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsDirectorOrAbove])
    def pending_reviews(self, request):
        """
        Obtener evaluaciones pendientes de revisión
        Solo para Directores y Admins
        """
        evaluations = CandidateEvaluation.objects.filter(
            status='completed'
        ).select_related('template', 'candidate', 'assigned_by')
        
        serializer = self.get_serializer(evaluations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Obtener estadísticas generales de evaluaciones
        """
        queryset = self.get_queryset()
        
        total = queryset.count()
        completed = queryset.filter(status='completed')
        reviewed = queryset.filter(status='reviewed')
        
        stats = {
            'total_evaluations': total,
            'completed_evaluations': completed.count(),
            'pending_evaluations': queryset.filter(status='pending').count(),
            'in_progress_evaluations': queryset.filter(status='in_progress').count(),
            'reviewed_evaluations': reviewed.count(),
            'average_score': completed.aggregate(avg=Avg('final_score'))['avg'] or 0,
            'pass_rate': (
                completed.filter(passed=True).count() / completed.count() * 100
                if completed.count() > 0 else 0
            ),
            'average_completion_time': completed.aggregate(
                avg=Avg('time_taken_minutes')
            )['avg'] or 0,
        }
        
        serializer = EvaluationStatsSerializer(data=stats)
        serializer.is_valid()
        return Response(serializer.data)


class EvaluationAnswerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de respuestas de evaluación
    Principalmente usado para consulta y actualización de feedback
    """
    
    queryset = EvaluationAnswer.objects.select_related(
        'evaluation', 'question'
    )
    serializer_class = EvaluationAnswerSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAbove]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['evaluation', 'question', 'is_correct']
    
    def get_queryset(self):
        """Filtrar respuestas según permisos"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role in ['admin', 'director']:
            return queryset
        else:  # supervisor
            return queryset.filter(
                Q(evaluation__assigned_by=user) |
                Q(evaluation__reviewed_by=user)
            )


class EvaluationCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para comentarios en evaluaciones
    """
    
    queryset = EvaluationComment.objects.select_related('evaluation', 'user')
    serializer_class = EvaluationCommentSerializer
    permission_classes = [IsAuthenticated, IsSupervisorOrAbove]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['evaluation', 'is_internal']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filtrar comentarios según permisos:
        - Comentarios internos solo para admin/director
        - Supervisores solo ven comentarios de sus evaluaciones
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role not in ['admin', 'director']:
            queryset = queryset.filter(
                Q(evaluation__assigned_by=user) |
                Q(evaluation__reviewed_by=user)
            )
            queryset = queryset.filter(is_internal=False)
        
        return queryset