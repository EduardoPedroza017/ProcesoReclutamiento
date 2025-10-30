"""
Views para Servicios de IA
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q
from datetime import timedelta

from .models import CVAnalysis, CandidateProfileMatching, ProfileGeneration, AILog
from .serializers import (
    CVAnalysisSerializer,
    CVAnalysisCreateSerializer,
    CandidateProfileMatchingSerializer,
    MatchingRequestSerializer,
    ProfileGenerationSerializer,
    ProfileGenerationCreateSerializer,
    AILogSerializer,
    SummarizeRequestSerializer,
    BulkMatchingRequestSerializer,
    AIStatsSerializer,
)
from .services import CVAnalyzerService, MatchingService, ProfileGenerationService, SummarizationService
from .tasks import analyze_cv_task, calculate_matching_task, generate_profile_task
from apps.candidates.models import Candidate
from apps.profiles.models import Profile
from apps.accounts.permissions import IsAdminOrDirector


class CVAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para análisis de CVs
    
    Endpoints:
    - GET /api/ai/cv-analysis/ - Listar análisis
    - GET /api/ai/cv-analysis/{id}/ - Detalle de análisis
    - POST /api/ai/cv-analysis/analyze/ - Analizar CV
    - POST /api/ai/cv-analysis/reanalyze/{id}/ - Reanalizar CV
    """
    queryset = CVAnalysis.objects.select_related('candidate', 'created_by').all()
    serializer_class = CVAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'candidate': ['exact'],
        'status': ['exact', 'in'],
        'created_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['created_at', 'completed_at', 'processing_time']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """
        Analizar un CV
        
        Body (form-data):
        - candidate_id: ID del candidato
        - document_file: Archivo del CV (PDF o DOCX)
        """
        serializer = CVAnalysisCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        candidate_id = serializer.validated_data['candidate_id']
        document_file = serializer.validated_data['document_file']
        
        # Verificar que el candidato exista
        try:
            candidate = Candidate.objects.get(pk=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidato no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear el análisis
        analysis = CVAnalysis.objects.create(
            candidate=candidate,
            document_file=document_file,
            status=CVAnalysis.STATUS_PENDING,
            created_by=request.user
        )
        
        # Procesar de forma asíncrona con Celery
        analyze_cv_task.delay(analysis.id)
        
        return Response({
            'message': 'Análisis iniciado',
            'analysis_id': analysis.id,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """Reanalizar un CV existente"""
        analysis = self.get_object()
        
        # Resetear el estado
        analysis.status = CVAnalysis.STATUS_PENDING
        analysis.error_message = ''
        analysis.save()
        
        # Procesar de forma asíncrona
        analyze_cv_task.delay(analysis.id)
        
        return Response({
            'message': 'Reanálisis iniciado',
            'analysis_id': analysis.id,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


class MatchingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para matching candidato-perfil
    
    Endpoints:
    - GET /api/ai/matching/ - Listar matchings
    - GET /api/ai/matching/{id}/ - Detalle de matching
    - POST /api/ai/matching/calculate/ - Calcular matching
    - POST /api/ai/matching/bulk_calculate/ - Matching masivo
    - GET /api/ai/matching/best_matches/{profile_id}/ - Mejores matches para un perfil
    """
    queryset = CandidateProfileMatching.objects.select_related(
        'candidate', 'profile', 'created_by'
    ).all()
    serializer_class = CandidateProfileMatchingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'candidate': ['exact'],
        'profile': ['exact'],
        'overall_score': ['gte', 'lte'],
        'created_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['overall_score', 'created_at']
    ordering = ['-overall_score']
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calcular matching entre un candidato y un perfil
        
        Body:
        {
            "candidate_id": 1,
            "profile_id": 1
        }
        """
        serializer = MatchingRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        candidate_id = serializer.validated_data['candidate_id']
        profile_id = serializer.validated_data['profile_id']
        
        # Verificar que existan
        try:
            candidate = Candidate.objects.get(pk=candidate_id)
            profile = Profile.objects.get(pk=profile_id)
        except (Candidate.DoesNotExist, Profile.DoesNotExist):
            return Response(
                {'error': 'Candidato o perfil no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar si ya existe un matching
        existing = CandidateProfileMatching.objects.filter(
            candidate=candidate,
            profile=profile
        ).first()
        
        if existing:
            # Actualizar el matching existente
            matching = existing
        else:
            # Crear nuevo matching
            matching = CandidateProfileMatching.objects.create(
                candidate=candidate,
                profile=profile,
                overall_score=0,
                created_by=request.user
            )
        
        # Calcular matching de forma asíncrona
        calculate_matching_task.delay(matching.id)
        
        return Response({
            'message': 'Cálculo de matching iniciado',
            'matching_id': matching.id,
            'status': 'processing'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def bulk_calculate(self, request):
        """
        Calcular matching masivo de múltiples candidatos con un perfil
        
        Body:
        {
            "profile_id": 1,
            "candidate_ids": [1, 2, 3, 4, 5]
        }
        """
        serializer = BulkMatchingRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        profile_id = serializer.validated_data['profile_id']
        candidate_ids = serializer.validated_data['candidate_ids']
        
        # Verificar que el perfil exista
        try:
            profile = Profile.objects.get(pk=profile_id)
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Perfil no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que los candidatos existan
        candidates = Candidate.objects.filter(pk__in=candidate_ids)
        if candidates.count() != len(candidate_ids):
            return Response(
                {'error': 'Algunos candidatos no fueron encontrados'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear o actualizar matchings
        matching_ids = []
        for candidate in candidates:
            matching, created = CandidateProfileMatching.objects.get_or_create(
                candidate=candidate,
                profile=profile,
                defaults={
                    'overall_score': 0,
                    'created_by': request.user
                }
            )
            matching_ids.append(matching.id)
            
            # Iniciar cálculo asíncrono
            calculate_matching_task.delay(matching.id)
        
        return Response({
            'message': f'Cálculo de {len(matching_ids)} matchings iniciado',
            'matching_ids': matching_ids,
            'status': 'processing'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'])
    def best_matches(self, request):
        """
        Obtener los mejores matches para un perfil
        
        Query params:
        - profile_id: ID del perfil (requerido)
        - min_score: Puntuación mínima (opcional, default=70)
        - limit: Límite de resultados (opcional, default=10)
        """
        profile_id = request.query_params.get('profile_id')
        min_score = int(request.query_params.get('min_score', 70))
        limit = int(request.query_params.get('limit', 10))
        
        if not profile_id:
            return Response(
                {'error': 'Se requiere profile_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        matchings = self.get_queryset().filter(
            profile_id=profile_id,
            overall_score__gte=min_score
        ).order_by('-overall_score')[:limit]
        
        serializer = self.get_serializer(matchings, many=True)
        return Response(serializer.data)


class ProfileGenerationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para generación de perfiles
    
    Endpoints:
    - GET /api/ai/profile-generation/ - Listar generaciones
    - GET /api/ai/profile-generation/{id}/ - Detalle de generación
    - POST /api/ai/profile-generation/generate/ - Generar perfil
    """
    queryset = ProfileGeneration.objects.select_related('profile', 'created_by').all()
    serializer_class = ProfileGenerationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'profile': ['exact'],
        'status': ['exact', 'in'],
        'created_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generar un perfil desde una transcripción
        
        Body:
        {
            "meeting_transcription": "texto de la transcripción...",
            "client_name": "Nombre del cliente (opcional)",
            "additional_notes": "Notas adicionales (opcional)",
            "create_profile": false (si true, crea el perfil automáticamente)
        }
        """
        serializer = ProfileGenerationCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear la generación
        generation = ProfileGeneration.objects.create(
            meeting_transcription=serializer.validated_data['meeting_transcription'],
            additional_notes=serializer.validated_data.get('additional_notes', ''),
            status=ProfileGeneration.STATUS_PENDING,
            created_by=request.user
        )
        
        # Procesar de forma asíncrona
        create_profile = serializer.validated_data.get('create_profile', False)
        client_name = serializer.validated_data.get('client_name', '')
        
        generate_profile_task.delay(generation.id, client_name, create_profile)
        
        return Response({
            'message': 'Generación de perfil iniciada',
            'generation_id': generation.id,
            'status': 'pending'
        }, status=status.HTTP_202_ACCEPTED)


class AILogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para logs de IA
    
    Endpoints:
    - GET /api/ai/logs/ - Listar logs
    - GET /api/ai/logs/{id}/ - Detalle de log
    """
    queryset = AILog.objects.select_related(
        'candidate', 'profile', 'created_by'
    ).all()
    serializer_class = AILogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDirector]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'action': ['exact', 'in'],
        'success': ['exact'],
        'candidate': ['exact'],
        'profile': ['exact'],
        'created_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['created_at', 'execution_time', 'tokens_input', 'tokens_output']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de uso de IA"""
        queryset = self.get_queryset()
        
        # Total de llamadas
        total_api_calls = queryset.count()
        
        # Total de análisis de CV
        total_cv_analyses = CVAnalysis.objects.count()
        
        # Total de matchings
        total_matchings = CandidateProfileMatching.objects.count()
        
        # Total de generaciones
        total_profile_generations = ProfileGeneration.objects.count()
        
        # Total de tokens usados
        total_tokens = queryset.aggregate(
            total=Sum('tokens_input') + Sum('tokens_output')
        )['total'] or 0
        
        # Tiempo promedio de ejecución
        avg_execution_time = queryset.aggregate(
            avg=Avg('execution_time')
        )['avg'] or 0
        
        # Tasa de éxito
        total_calls = queryset.count()
        successful_calls = queryset.filter(success=True).count()
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Análisis por estado
        analyses_by_status = {}
        for status_code, status_name in CVAnalysis.STATUS_CHOICES:
            count = CVAnalysis.objects.filter(status=status_code).count()
            analyses_by_status[status_code] = {
                'count': count,
                'display': status_name
            }
        
        # Matchings por rango de puntuación
        matchings_by_score = {
            'excellent': CandidateProfileMatching.objects.filter(overall_score__gte=90).count(),
            'good': CandidateProfileMatching.objects.filter(
                overall_score__gte=70, overall_score__lt=90
            ).count(),
            'fair': CandidateProfileMatching.objects.filter(
                overall_score__gte=50, overall_score__lt=70
            ).count(),
            'poor': CandidateProfileMatching.objects.filter(overall_score__lt=50).count(),
        }
        
        # Actividad reciente
        recent_logs = queryset.order_by('-created_at')[:10]
        recent_activity = AILogSerializer(recent_logs, many=True).data
        
        stats_data = {
            'total_cv_analyses': total_cv_analyses,
            'total_matchings': total_matchings,
            'total_profile_generations': total_profile_generations,
            'total_api_calls': total_api_calls,
            'total_tokens_used': total_tokens,
            'average_execution_time': round(avg_execution_time, 2),
            'success_rate': round(success_rate, 2),
            'analyses_by_status': analyses_by_status,
            'matchings_by_score': matchings_by_score,
            'recent_activity': recent_activity,
        }
        
        serializer = AIStatsSerializer(stats_data)
        return Response(serializer.data)


class SummarizationViewSet(viewsets.ViewSet):
    """
    ViewSet para servicios de resumen
    
    Endpoints:
    - POST /api/ai/summarize/candidate/ - Resumir candidato
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def candidate(self, request):
        """
        Generar resumen ejecutivo de un candidato
        
        Body:
        {
            "candidate_id": 1
        }
        """
        serializer = SummarizeRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        candidate_id = serializer.validated_data['candidate_id']
        
        try:
            candidate = Candidate.objects.get(pk=candidate_id)
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Candidato no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Preparar datos del candidato
        candidate_data = {
            'nombre': candidate.full_name,
            'email': candidate.email,
            'telefono': candidate.phone,
            'ciudad': candidate.city,
            'puesto_actual': candidate.current_position,
            'empresa_actual': candidate.current_company,
            'años_experiencia': candidate.years_of_experience,
            'nivel_educacion': candidate.education_level,
            'universidad': candidate.university,
            'carrera': candidate.degree,
            'habilidades': candidate.skills,
            'idiomas': candidate.languages,
            'certificaciones': candidate.certifications,
        }
        
        # Generar resumen
        service = SummarizationService()
        result = service.summarize_candidate(candidate_data)
        
        if result['success']:
            # Actualizar el candidato con el resumen
            candidate.ai_summary = result['summary']
            candidate.save()
            
            # Registrar en el log
            AILog.objects.create(
                action=AILog.ACTION_SUMMARIZATION,
                prompt=f"Resumir candidato: {candidate.full_name}",
                response=result['summary'],
                tokens_input=result['tokens_input'],
                tokens_output=result['tokens_output'],
                execution_time=result['execution_time'],
                success=True,
                candidate=candidate,
                created_by=request.user
            )
            
            return Response({
                'summary': result['summary'],
                'execution_time': result['execution_time']
            })
        else:
            return Response(
                {'error': result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )