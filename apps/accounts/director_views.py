"""
Views específicas para el Director de Reclutamiento
Incluye dashboard, reportes, analytics y métricas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg, F, Sum, Max, Min
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
from apps.accounts.permissions import IsDirectorOrAbove
from apps.profiles.models import Profile, ProfileStatusHistory
from apps.candidates.models import Candidate, CandidateProfile
from apps.clients.models import Client
from apps.evaluations.models import CandidateEvaluation
from apps.accounts.models import User
from apps.ai_services.models import CVAnalysis, CandidateProfileMatching
from apps.documents.models import GeneratedDocument


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def director_dashboard(request):
    """
    Dashboard principal del Director
    GET /api/director/dashboard/
    
    Retorna métricas clave y KPIs del sistema
    """
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # ============================================
    # MÉTRICAS DE PERFILES
    # ============================================
    
    # Total de perfiles
    total_profiles = Profile.objects.count()
    
    # Perfiles por estado
    profiles_by_status = Profile.objects.values('status').annotate(
        count=Count('id')
    )
    profiles_status_dict = {item['status']: item['count'] for item in profiles_by_status}
    
    # Perfiles activos (no completados ni cancelados)
    active_profiles = Profile.objects.exclude(
        status__in=[Profile.STATUS_COMPLETED, Profile.STATUS_CANCELLED]
    ).count()
    
    # Perfiles nuevos este mes
    new_profiles_this_month = Profile.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Perfiles completados este mes
    completed_this_month = Profile.objects.filter(
        status=Profile.STATUS_COMPLETED,
        updated_at__gte=thirty_days_ago
    ).count()
    
    # Tasa de éxito (completados vs total)
    success_rate = 0
    if total_profiles > 0:
        completed_total = Profile.objects.filter(
            status=Profile.STATUS_COMPLETED
        ).count()
        success_rate = (completed_total / total_profiles) * 100
    
    # Perfiles por prioridad
    profiles_by_priority = Profile.objects.values('priority').annotate(
        count=Count('id')
    )
    
    # ============================================
    # MÉTRICAS DE CANDIDATOS
    # ============================================
    
    total_candidates = Candidate.objects.count()
    
    # Candidatos activos
    active_candidates = Candidate.objects.exclude(
        status__in=[Candidate.STATUS_HIRED, Candidate.STATUS_REJECTED, Candidate.STATUS_WITHDRAWN]
    ).count()
    
    # Candidatos contratados este mes
    hired_this_month = Candidate.objects.filter(
        status=Candidate.STATUS_HIRED,
        updated_at__gte=thirty_days_ago
    ).count()
    
    # Candidatos en proceso de entrevista
    in_interview = Candidate.objects.filter(
        status=Candidate.STATUS_INTERVIEW
    ).count()
    
    # Candidatos con oferta extendida
    with_offer = Candidate.objects.filter(
        status=Candidate.STATUS_OFFER
    ).count()
    
    # ============================================
    # MÉTRICAS DE CLIENTES
    # ============================================
    
    total_clients = Client.objects.count()
    
    # Clientes activos (con perfiles activos)
    active_clients = Client.objects.filter(
        profiles__status__in=[
            Profile.STATUS_IN_PROGRESS,
            Profile.STATUS_REVIEW,
            Profile.STATUS_APPROVED,
            Profile.STATUS_PUBLISHED,
            Profile.STATUS_CANDIDATES_REVIEWING,
            Profile.STATUS_IN_INTERVIEWS,
        ]
    ).distinct().count()
    
    # Nuevos clientes este mes
    new_clients_this_month = Client.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # ============================================
    # MÉTRICAS DE EVALUACIONES
    # ============================================
    
    total_evaluations = CandidateEvaluation.objects.count()
    
    pending_evaluations = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_PENDING
    ).count()
    
    in_progress_evaluations = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_IN_PROGRESS
    ).count()
    
    completed_evaluations = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_COMPLETED
    ).count()
    
    # Promedio de puntuación de evaluaciones
    avg_evaluation_score = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_COMPLETED
    ).aggregate(avg=Avg('final_score'))['avg'] or 0
    
    # ============================================
    # MÉTRICAS DE IA
    # ============================================
    
    total_cv_analyses = CVAnalysis.objects.count()
    
    cv_analyses_this_month = CVAnalysis.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # Promedio de score de matching
    avg_matching_score = CandidateProfileMatching.objects.aggregate(
        avg=Avg('overall_score')
    )['avg'] or 0
    
    # ============================================
    # MÉTRICAS DE DOCUMENTOS
    # ============================================
    
    total_documents = GeneratedDocument.objects.count()
    
    documents_generated_this_month = GeneratedDocument.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    # ============================================
    # MÉTRICAS DEL EQUIPO
    # ============================================
    
    total_supervisors = User.objects.filter(
        role=User.ROLE_SUPERVISOR,
        is_active=True
    ).count()
    
    # Perfiles asignados por supervisor
    profiles_per_supervisor = Profile.objects.filter(
        assigned_to__role=User.ROLE_SUPERVISOR
    ).values('assigned_to__first_name', 'assigned_to__last_name').annotate(
        count=Count('id')
    )[:5]  # Top 5
    
    # ============================================
    # ALERTAS Y PENDIENTES
    # ============================================
    
    # Perfiles pendientes de aprobación
    pending_approval = Profile.objects.filter(
        status=Profile.STATUS_PENDING
    ).count()
    
    # Perfiles próximos a vencer
    profiles_near_deadline = Profile.objects.filter(
        deadline__lte=today + timedelta(days=7),
        deadline__gte=today,
        status__in=[Profile.STATUS_IN_PROGRESS, Profile.STATUS_REVIEW]
    ).count()
    
    # Evaluaciones pendientes de revisión
    evaluations_pending_review = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_PENDING_REVIEW
    ).count()
    
    # ============================================
    # TENDENCIAS (últimos 30 días)
    # ============================================
    
    # Perfiles creados por día
    profiles_trend = Profile.objects.filter(
        created_at__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Candidatos agregados por día
    candidates_trend = Candidate.objects.filter(
        created_at__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # ============================================
    # PIPELINE DE RECLUTAMIENTO
    # ============================================
    
    pipeline = {
        'total_positions': total_profiles,
        'in_sourcing': Profile.objects.filter(
            status__in=[Profile.STATUS_IN_PROGRESS, Profile.STATUS_PUBLISHED]
        ).count(),
        'in_screening': Candidate.objects.filter(
            status=Candidate.STATUS_SCREENING
        ).count(),
        'in_evaluation': CandidateEvaluation.objects.filter(
            status__in=[
                CandidateEvaluation.STATUS_IN_PROGRESS,
                CandidateEvaluation.STATUS_PENDING_REVIEW
            ]
        ).count(),
        'in_interview': in_interview,
        'with_offer': with_offer,
        'hired': Candidate.objects.filter(
            status=Candidate.STATUS_HIRED
        ).count(),
    }
    
    # ============================================
    # RESPUESTA CONSOLIDADA
    # ============================================
    
    return Response({
        'overview': {
            'total_profiles': total_profiles,
            'active_profiles': active_profiles,
            'total_candidates': total_candidates,
            'active_candidates': active_candidates,
            'total_clients': total_clients,
            'active_clients': active_clients,
            'success_rate': round(success_rate, 2),
        },
        'this_month': {
            'new_profiles': new_profiles_this_month,
            'completed_profiles': completed_this_month,
            'hired_candidates': hired_this_month,
            'new_clients': new_clients_this_month,
            'cv_analyses': cv_analyses_this_month,
            'documents_generated': documents_generated_this_month,
        },
        'profiles': {
            'by_status': profiles_status_dict,
            'by_priority': list(profiles_by_priority),
            'pending_approval': pending_approval,
            'near_deadline': profiles_near_deadline,
        },
        'candidates': {
            'total': total_candidates,
            'active': active_candidates,
            'in_interview': in_interview,
            'with_offer': with_offer,
            'hired_this_month': hired_this_month,
        },
        'evaluations': {
            'total': total_evaluations,
            'pending': pending_evaluations,
            'in_progress': in_progress_evaluations,
            'completed': completed_evaluations,
            'avg_score': round(avg_evaluation_score, 2),
            'pending_review': evaluations_pending_review,
        },
        'ai_metrics': {
            'total_analyses': total_cv_analyses,
            'analyses_this_month': cv_analyses_this_month,
            'avg_matching_score': round(avg_matching_score, 2),
        },
        'team': {
            'total_supervisors': total_supervisors,
            'top_performers': list(profiles_per_supervisor),
        },
        'pipeline': pipeline,
        'alerts': {
            'pending_approval': pending_approval,
            'near_deadline': profiles_near_deadline,
            'pending_review': evaluations_pending_review,
        },
        'trends': {
            'profiles': list(profiles_trend),
            'candidates': list(candidates_trend),
        },
        'generated_at': timezone.now(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def profiles_overview(request):
    """
    Vista general de perfiles con filtros avanzados
    GET /api/director/profiles/overview/
    
    Query params:
    - status: filtrar por estado
    - priority: filtrar por prioridad
    - client_id: filtrar por cliente
    - assigned_to: filtrar por supervisor
    - date_from: fecha desde
    - date_to: fecha hasta
    """
    queryset = Profile.objects.select_related('client', 'assigned_to')
    
    # Aplicar filtros
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    priority_filter = request.query_params.get('priority')
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
    
    client_id = request.query_params.get('client_id')
    if client_id:
        queryset = queryset.filter(client_id=client_id)
    
    assigned_to = request.query_params.get('assigned_to')
    if assigned_to:
        queryset = queryset.filter(assigned_to_id=assigned_to)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    
    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    
    # Estadísticas
    total = queryset.count()
    
    by_status = queryset.values('status').annotate(
        count=Count('id')
    )
    
    by_priority = queryset.values('priority').annotate(
        count=Count('id')
    )
    
    by_client = queryset.values(
        'client__company_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    by_supervisor = queryset.filter(
        assigned_to__isnull=False
    ).values(
        'assigned_to__first_name',
        'assigned_to__last_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Tiempo promedio por fase
    avg_time_to_approval = queryset.filter(
        status__in=[Profile.STATUS_APPROVED, Profile.STATUS_COMPLETED]
    ).aggregate(
        avg=Avg(F('updated_at') - F('created_at'))
    )['avg']
    
    return Response({
        'total': total,
        'by_status': list(by_status),
        'by_priority': list(by_priority),
        'top_clients': list(by_client),
        'by_supervisor': list(by_supervisor),
        'avg_time_to_approval_days': avg_time_to_approval.days if avg_time_to_approval else 0,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def candidates_overview(request):
    """
    Vista general de candidatos
    GET /api/director/candidates/overview/
    
    Query params similares a profiles_overview
    """
    queryset = Candidate.objects.all()
    
    # Aplicar filtros
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    
    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)
    
    # Estadísticas
    total = queryset.count()
    
    by_status = queryset.values('status').annotate(
        count=Count('id')
    )
    
    by_source = queryset.values('source').annotate(
        count=Count('id')
    )
    
    # Candidatos con mejor matching score
    top_matches = CandidateProfileMatching.objects.filter(
        candidate__in=queryset
    ).order_by('-overall_score')[:10].values(
        'candidate__first_name',
        'candidate__last_name',
        'profile__position_title',
        'overall_score'
    )
    
    return Response({
        'total': total,
        'by_status': list(by_status),
        'by_source': list(by_source),
        'top_matches': list(top_matches),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def team_performance(request):
    """
    Rendimiento del equipo de supervisores
    GET /api/director/team/performance/
    """
    supervisors = User.objects.filter(
        role=User.ROLE_SUPERVISOR,
        is_active=True
    )
    
    performance_data = []
    
    for supervisor in supervisors:
        # Perfiles asignados
        total_profiles = Profile.objects.filter(
            assigned_to=supervisor
        ).count()
        
        # Perfiles completados
        completed_profiles = Profile.objects.filter(
            assigned_to=supervisor,
            status=Profile.STATUS_COMPLETED
        ).count()
        
        # Tasa de éxito
        success_rate = 0
        if total_profiles > 0:
            success_rate = (completed_profiles / total_profiles) * 100
        
        # Candidatos gestionados
        candidates_managed = Candidate.objects.filter(
            assigned_to=supervisor
        ).count()
        
        # Evaluaciones completadas
        evaluations_reviewed = CandidateEvaluation.objects.filter(
            reviewed_by=supervisor,
            status=CandidateEvaluation.STATUS_COMPLETED
        ).count()
        
        # Tiempo promedio de cierre
        avg_closure_time = Profile.objects.filter(
            assigned_to=supervisor,
            status=Profile.STATUS_COMPLETED
        ).aggregate(
            avg=Avg(F('updated_at') - F('created_at'))
        )['avg']
        
        performance_data.append({
            'supervisor': {
                'id': supervisor.id,
                'name': supervisor.get_full_name(),
                'email': supervisor.email,
            },
            'metrics': {
                'total_profiles': total_profiles,
                'completed_profiles': completed_profiles,
                'success_rate': round(success_rate, 2),
                'candidates_managed': candidates_managed,
                'evaluations_reviewed': evaluations_reviewed,
                'avg_closure_days': avg_closure_time.days if avg_closure_time else 0,
            }
        })
    
    # Ordenar por tasa de éxito
    performance_data.sort(key=lambda x: x['metrics']['success_rate'], reverse=True)
    
    return Response({
        'team_size': len(performance_data),
        'performance': performance_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def client_analytics(request):
    """
    Analytics por cliente
    GET /api/director/clients/analytics/
    
    Query params:
    - client_id: ID del cliente específico (opcional)
    """
    client_id = request.query_params.get('client_id')
    
    if client_id:
        # Analytics de un cliente específico
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        total_profiles = Profile.objects.filter(client=client).count()
        completed_profiles = Profile.objects.filter(
            client=client,
            status=Profile.STATUS_COMPLETED
        ).count()
        
        active_profiles = Profile.objects.filter(
            client=client
        ).exclude(
            status__in=[Profile.STATUS_COMPLETED, Profile.STATUS_CANCELLED]
        ).count()
        
        success_rate = 0
        if total_profiles > 0:
            success_rate = (completed_profiles / total_profiles) * 100
        
        profiles_by_status = Profile.objects.filter(
            client=client
        ).values('status').annotate(count=Count('id'))
        
        avg_time_to_hire = Profile.objects.filter(
            client=client,
            status=Profile.STATUS_COMPLETED
        ).aggregate(
            avg=Avg(F('updated_at') - F('created_at'))
        )['avg']
        
        return Response({
            'client': {
                'id': client.id,
                'name': client.company_name,
                'industry': client.industry,
            },
            'metrics': {
                'total_profiles': total_profiles,
                'completed_profiles': completed_profiles,
                'active_profiles': active_profiles,
                'success_rate': round(success_rate, 2),
                'avg_time_to_hire_days': avg_time_to_hire.days if avg_time_to_hire else 0,
            },
            'profiles_by_status': list(profiles_by_status),
        })
    
    else:
        # Analytics de todos los clientes
        clients = Client.objects.all()
        
        client_stats = []
        
        for client in clients:
            total_profiles = Profile.objects.filter(client=client).count()
            completed_profiles = Profile.objects.filter(
                client=client,
                status=Profile.STATUS_COMPLETED
            ).count()
            
            success_rate = 0
            if total_profiles > 0:
                success_rate = (completed_profiles / total_profiles) * 100
            
            client_stats.append({
                'client': {
                    'id': client.id,
                    'name': client.company_name,
                    'industry': client.industry,
                },
                'total_profiles': total_profiles,
                'completed_profiles': completed_profiles,
                'success_rate': round(success_rate, 2),
            })
        
        # Ordenar por total de perfiles
        client_stats.sort(key=lambda x: x['total_profiles'], reverse=True)
        
        return Response({
            'total_clients': len(client_stats),
            'clients': client_stats[:20],  # Top 20
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def monthly_report(request):
    """
    Reporte mensual consolidado
    GET /api/director/reports/monthly/
    
    Query params:
    - month: número del mes (1-12), default: mes actual
    - year: año, default: año actual
    """
    month = int(request.query_params.get('month', timezone.now().month))
    year = int(request.query_params.get('year', timezone.now().year))
    
    # Rango de fechas
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Perfiles creados en el mes
    profiles_created = Profile.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).count()
    
    # Perfiles completados en el mes
    profiles_completed = Profile.objects.filter(
        status=Profile.STATUS_COMPLETED,
        updated_at__gte=start_date,
        updated_at__lt=end_date
    ).count()
    
    # Candidatos agregados
    candidates_added = Candidate.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).count()
    
    # Candidatos contratados
    candidates_hired = Candidate.objects.filter(
        status=Candidate.STATUS_HIRED,
        updated_at__gte=start_date,
        updated_at__lt=end_date
    ).count()
    
    # Evaluaciones completadas
    evaluations_completed = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_COMPLETED,
        completed_at__gte=start_date,
        completed_at__lt=end_date
    ).count()
    
    # Análisis de CVs realizados
    cv_analyses = CVAnalysis.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).count()
    
    # Documentos generados
    documents_generated = GeneratedDocument.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).count()
    
    # Clientes nuevos
    new_clients = Client.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).count()
    
    # Top 5 clientes más activos
    top_clients = Profile.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date
    ).values(
        'client__company_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Top 5 supervisores más productivos
    top_supervisors = Profile.objects.filter(
        created_at__gte=start_date,
        created_at__lt=end_date,
        assigned_to__role=User.ROLE_SUPERVISOR
    ).values(
        'assigned_to__first_name',
        'assigned_to__last_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return Response({
        'period': {
            'month': month,
            'year': year,
            'month_name': datetime(year, month, 1).strftime('%B'),
        },
        'summary': {
            'profiles_created': profiles_created,
            'profiles_completed': profiles_completed,
            'candidates_added': candidates_added,
            'candidates_hired': candidates_hired,
            'evaluations_completed': evaluations_completed,
            'cv_analyses': cv_analyses,
            'documents_generated': documents_generated,
            'new_clients': new_clients,
        },
        'top_clients': list(top_clients),
        'top_supervisors': list(top_supervisors),
        'generated_at': timezone.now(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def pending_actions(request):
    """
    Acciones pendientes que requieren atención del director
    GET /api/director/pending-actions/
    """
    today = timezone.now()
    
    # Perfiles pendientes de aprobación
    pending_approval_profiles = Profile.objects.filter(
        status=Profile.STATUS_PENDING
    ).select_related('client', 'created_by').values(
        'id',
        'position_title',
        'client__company_name',
        'created_by__first_name',
        'created_by__last_name',
        'created_at',
        'priority'
    )[:10]
    
    # Perfiles próximos a vencer
    profiles_near_deadline = Profile.objects.filter(
        deadline__lte=today + timedelta(days=7),
        deadline__gte=today
    ).exclude(
        status__in=[Profile.STATUS_COMPLETED, Profile.STATUS_CANCELLED]
    ).select_related('client', 'assigned_to').values(
        'id',
        'position_title',
        'client__company_name',
        'assigned_to__first_name',
        'assigned_to__last_name',
        'deadline',
        'status'
    )[:10]
    
    # Evaluaciones pendientes de revisión
    evaluations_pending_review = CandidateEvaluation.objects.filter(
        status=CandidateEvaluation.STATUS_PENDING_REVIEW
    ).select_related('candidate', 'template').values(
        'id',
        'candidate__first_name',
        'candidate__last_name',
        'template__title',
        'completed_at'
    )[:10]
    
    # Perfiles sin supervisor asignado
    unassigned_profiles = Profile.objects.filter(
        assigned_to__isnull=True,
        status__in=[Profile.STATUS_APPROVED, Profile.STATUS_IN_PROGRESS]
    ).select_related('client').values(
        'id',
        'position_title',
        'client__company_name',
        'created_at',
        'priority'
    )[:10]
    
    return Response({
        'pending_approval': {
            'count': len(pending_approval_profiles),
            'items': list(pending_approval_profiles),
        },
        'near_deadline': {
            'count': len(profiles_near_deadline),
            'items': list(profiles_near_deadline),
        },
        'pending_review': {
            'count': len(evaluations_pending_review),
            'items': list(evaluations_pending_review),
        },
        'unassigned_profiles': {
            'count': len(unassigned_profiles),
            'items': list(unassigned_profiles),
        },
        'total_pending': (
            len(pending_approval_profiles) +
            len(profiles_near_deadline) +
            len(evaluations_pending_review) +
            len(unassigned_profiles)
        ),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def recruitment_funnel(request):
    """
    Embudo/funnel del proceso de reclutamiento
    GET /api/director/funnel/
    
    Muestra el flujo completo: Perfiles → Candidatos → Evaluaciones → Contrataciones
    """
    # Etapa 1: Perfiles creados
    total_profiles = Profile.objects.count()
    
    # Etapa 2: Perfiles aprobados
    approved_profiles = Profile.objects.filter(
        status__in=[
            Profile.STATUS_APPROVED,
            Profile.STATUS_PUBLISHED,
            Profile.STATUS_IN_PROGRESS,
            Profile.STATUS_CANDIDATES_REVIEWING,
            Profile.STATUS_IN_INTERVIEWS,
            Profile.STATUS_COMPLETED
        ]
    ).count()
    
    # Etapa 3: Candidatos activos
    active_candidates = Candidate.objects.exclude(
        status__in=[Candidate.STATUS_REJECTED, Candidate.STATUS_WITHDRAWN]
    ).count()
    
    # Etapa 4: Candidatos calificados
    qualified_candidates = Candidate.objects.filter(
        status=Candidate.STATUS_QUALIFIED
    ).count()
    
    # Etapa 5: En evaluación
    in_evaluation = CandidateEvaluation.objects.filter(
        status__in=[
            CandidateEvaluation.STATUS_IN_PROGRESS,
            CandidateEvaluation.STATUS_PENDING_REVIEW
        ]
    ).count()
    
    # Etapa 6: En entrevistas
    in_interview = Candidate.objects.filter(
        status=Candidate.STATUS_INTERVIEW
    ).count()
    
    # Etapa 7: Con oferta
    with_offer = Candidate.objects.filter(
        status=Candidate.STATUS_OFFER
    ).count()
    
    # Etapa 8: Contratados
    hired = Candidate.objects.filter(
        status=Candidate.STATUS_HIRED
    ).count()
    
    # Calcular tasas de conversión
    conversion_rates = {}
    
    if total_profiles > 0:
        conversion_rates['profile_to_approved'] = round((approved_profiles / total_profiles) * 100, 2)
    
    if approved_profiles > 0:
        conversion_rates['approved_to_candidates'] = round((active_candidates / approved_profiles) * 100, 2)
    
    if active_candidates > 0:
        conversion_rates['candidates_to_qualified'] = round((qualified_candidates / active_candidates) * 100, 2)
    
    if qualified_candidates > 0:
        conversion_rates['qualified_to_interview'] = round((in_interview / qualified_candidates) * 100, 2)
    
    if in_interview > 0:
        conversion_rates['interview_to_offer'] = round((with_offer / in_interview) * 100, 2)
    
    if with_offer > 0:
        conversion_rates['offer_to_hired'] = round((hired / with_offer) * 100, 2)
    
    return Response({
        'funnel': {
            'total_profiles': total_profiles,
            'approved_profiles': approved_profiles,
            'active_candidates': active_candidates,
            'qualified_candidates': qualified_candidates,
            'in_evaluation': in_evaluation,
            'in_interview': in_interview,
            'with_offer': with_offer,
            'hired': hired,
        },
        'conversion_rates': conversion_rates,
    })