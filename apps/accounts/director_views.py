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
from apps.candidates.models import Candidate, CandidateProfile, CandidateDocument, CandidateNote
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
    try:
        # Obtener parámetros
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        # Log de debugging
        print(f"📊 Generando reporte para: {month}/{year}")
        
        # Validar parámetros
        if month < 1 or month > 12:
            return Response(
                {'error': 'Mes inválido. Debe ser entre 1 y 12.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if year < 2000 or year > 2100:
            return Response(
                {'error': 'Año inválido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Diccionario de nombres de meses en español
        MONTHS = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Rango de fechas
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        print(f"📅 Rango: {start_date} - {end_date}")
        
        # ============================================
        # PERFILES
        # ============================================
        try:
            profiles_created = Profile.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            print(f"✅ Perfiles creados: {profiles_created}")
        except Exception as e:
            print(f"❌ Error en perfiles creados: {e}")
            profiles_created = 0
        
        try:
            profiles_completed = Profile.objects.filter(
                status=Profile.STATUS_COMPLETED,
                updated_at__gte=start_date,
                updated_at__lt=end_date
            ).count()
            print(f"✅ Perfiles completados: {profiles_completed}")
        except Exception as e:
            print(f"❌ Error en perfiles completados: {e}")
            profiles_completed = 0
        
        # ============================================
        # CANDIDATOS
        # ============================================
        try:
            candidates_added = Candidate.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            print(f"✅ Candidatos agregados: {candidates_added}")
        except Exception as e:
            print(f"❌ Error en candidatos agregados: {e}")
            candidates_added = 0
        
        try:
            candidates_hired = Candidate.objects.filter(
                status=Candidate.STATUS_HIRED,
                updated_at__gte=start_date,
                updated_at__lt=end_date
            ).count()
            print(f"✅ Candidatos contratados: {candidates_hired}")
        except Exception as e:
            print(f"❌ Error en candidatos contratados: {e}")
            candidates_hired = 0
        
        # ============================================
        # EVALUACIONES
        # ============================================
        try:
            evaluations_completed = CandidateEvaluation.objects.filter(
                status=CandidateEvaluation.STATUS_COMPLETED,
                completed_at__gte=start_date,
                completed_at__lt=end_date
            ).count()
            print(f"✅ Evaluaciones completadas: {evaluations_completed}")
        except Exception as e:
            print(f"❌ Error en evaluaciones: {e}")
            evaluations_completed = 0
        
        # ============================================
        # IA Y DOCUMENTOS
        # ============================================
        try:
            cv_analyses = CVAnalysis.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            print(f"✅ CVs analizados: {cv_analyses}")
        except Exception as e:
            print(f"❌ Error en CV analyses: {e}")
            cv_analyses = 0
        
        try:
            documents_generated = GeneratedDocument.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            print(f"✅ Documentos generados: {documents_generated}")
        except Exception as e:
            print(f"❌ Error en documentos: {e}")
            documents_generated = 0
        
        # ============================================
        # CLIENTES
        # ============================================
        try:
            new_clients = Client.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count()
            print(f"✅ Nuevos clientes: {new_clients}")
        except Exception as e:
            print(f"❌ Error en nuevos clientes: {e}")
            new_clients = 0
        
        # ============================================
        # TOP CLIENTES
        # ============================================
        try:
            top_clients = Profile.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values(
                'client__company_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            top_clients_list = list(top_clients)
            print(f"✅ Top clientes: {len(top_clients_list)}")
        except Exception as e:
            print(f"❌ Error en top clientes: {e}")
            top_clients_list = []
        
        # ============================================
        # TOP SUPERVISORES
        # ============================================
        try:
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
            
            top_supervisors_list = list(top_supervisors)
            print(f"✅ Top supervisores: {len(top_supervisors_list)}")
        except Exception as e:
            print(f"❌ Error en top supervisores: {e}")
            top_supervisors_list = []
        
        # ============================================
        # CONSTRUIR RESPUESTA
        # ============================================
        response_data = {
            'period': {
                'month': month,
                'year': year,
                'month_name': MONTHS.get(month, 'Desconocido'),
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
            'top_clients': top_clients_list,
            'top_supervisors': top_supervisors_list,
            'generated_at': timezone.now().isoformat(),
        }
        
        print(f"✅ Reporte generado exitosamente")
        return Response(response_data)
        
    except ValueError as e:
        print(f"❌ Error de validación: {e}")
        return Response(
            {'error': f'Parámetros inválidos: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def celery_tasks_status(request):
    """
    Obtiene el estado de las tareas de Celery
    GET /api/director/celery-tasks/
    
    Retorna información sobre tareas en ejecución, completadas y fallidas
    """
    from celery import current_app
    from django_celery_results.models import TaskResult
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Inicializar valores por defecto
    active_count = 0
    active_details = []
    scheduled_count = 0
    scheduled_details = []
    workers_info = []
    
    try:
        # Obtener información del inspector de Celery
        inspect = current_app.control.inspect()
        
        # Tareas activas
        active_tasks = inspect.active()
        if active_tasks:
            for worker, tasks in active_tasks.items():
                active_count += len(tasks)
                for task in tasks:
                    active_details.append({
                        'id': task['id'],
                        'name': task['name'],
                        'worker': worker,
                        'args': task.get('args', []),
                        'kwargs': task.get('kwargs', {}),
                    })
        
        # Tareas programadas
        scheduled_tasks = inspect.scheduled()
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                scheduled_count += len(tasks)
                for task in tasks:
                    scheduled_details.append({
                        'id': task['request']['id'],
                        'name': task['request']['task'],
                        'worker': worker,
                        'eta': task['eta'],
                    })
        
        # Lista de workers
        workers_info = list(active_tasks.keys()) if active_tasks else []
        
    except Exception as e:
        logger.warning(f"No se pudo conectar con Celery inspector: {e}")
        # Continuar con valores por defecto
    
    # Estadísticas de resultados de tareas (últimos 7 días)
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    task_stats = TaskResult.objects.filter(
        date_created__gte=seven_days_ago
    ).aggregate(
        total_tasks=Count('id'),
        successful_tasks=Count('id', filter=Q(status='SUCCESS')),
        failed_tasks=Count('id', filter=Q(status='FAILURE')),
        pending_tasks=Count('id', filter=Q(status='PENDING')),
        retry_tasks=Count('id', filter=Q(status='RETRY')),
    )
    
    # Tareas recientes (últimas 50)
    recent_tasks = TaskResult.objects.filter(
        date_created__gte=seven_days_ago
    ).order_by('-date_created')[:50].values(
        'task_id', 'task_name', 'status', 'result', 
        'date_created', 'date_done', 'traceback'
    )
    
    # Estadísticas por tipo de tarea
    task_types = TaskResult.objects.filter(
        date_created__gte=seven_days_ago
    ).values('task_name').annotate(
        total=Count('id'),
        successful=Count('id', filter=Q(status='SUCCESS')),
        failed=Count('id', filter=Q(status='FAILURE')),
    ).order_by('-total')
    
    return Response({
        'active_tasks': {
            'count': active_count,
            'tasks': active_details,
        },
        'scheduled_tasks': {
            'count': scheduled_count,
            'tasks': scheduled_details,
        },
        'statistics': task_stats,
        'recent_tasks': list(recent_tasks),
        'task_types': list(task_types),
        'workers_status': {
            'active_workers': len(workers_info),
            'workers': workers_info,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def celery_task_groups(request):
    """
    Obtiene información agrupada de tareas por categoría
    GET /api/director/celery-groups/
    """
    from django_celery_results.models import TaskResult
    from datetime import datetime, timedelta
    
    # Últimos 30 días
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Agrupar tareas por categorías principales
    task_groups = {
        'ai_services': {
            'name': 'Servicios de IA',
            'description': 'Análisis de CVs, matching y generación de perfiles',
            'tasks': []
        },
        'documents': {
            'name': 'Generación de Documentos',
            'description': 'Creación de PDFs y reportes',
            'tasks': []
        },
        'notifications': {
            'name': 'Notificaciones',
            'description': 'Envío de emails y notificaciones del sistema',
            'tasks': []
        },
        'system': {
            'name': 'Sistema',
            'description': 'Tareas de mantenimiento y limpieza',
            'tasks': []
        }
    }
    
    # Obtener estadísticas por grupo
    for group_key, group_info in task_groups.items():
        if group_key == 'ai_services':
            task_filter = Q(task_name__startswith='apps.ai_services')
        elif group_key == 'documents':
            task_filter = Q(task_name__startswith='apps.documents')
        elif group_key == 'notifications':
            task_filter = Q(task_name__startswith='apps.notifications')
        else:
            # Tareas del sistema y otras
            task_filter = ~Q(task_name__startswith='apps.')
        
        stats = TaskResult.objects.filter(
            date_created__gte=thirty_days_ago
        ).filter(task_filter).aggregate(
            total=Count('id'),
            successful=Count('id', filter=Q(status='SUCCESS')),
            failed=Count('id', filter=Q(status='FAILURE')),
            pending=Count('id', filter=Q(status='PENDING')),
        )
        
        # Tareas recientes de este grupo
        recent_tasks = TaskResult.objects.filter(
            date_created__gte=thirty_days_ago
        ).filter(task_filter).order_by('-date_created')[:10].values(
            'task_id', 'task_name', 'status', 'date_created', 'date_done'
        )
        
        group_info.update({
            'statistics': stats,
            'recent_tasks': list(recent_tasks)
        })
    
    return Response({
        'groups': task_groups,
        'summary': {
            'total_groups': len(task_groups),
            'period': '30 días',
        }
    })

    """
════════════════════════════════════════════════════════════════════
ENDPOINTS DE REPORTES INDIVIDUALES PARA DIRECTOR
════════════════════════════════════════════════════════════════════

Agregar estos endpoints al archivo: apps/accounts/director_views.py

Estos endpoints permiten generar reportes detallados de:
1. Perfil individual (vacante específica)
2. Candidatos de un perfil
3. Timeline/proceso completo de un perfil
4. Candidato individual completo
5. Reporte completo de un cliente

════════════════════════════════════════════════════════════════════
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Q, Avg, F, Max, Min
from django.utils import timezone
from datetime import timedelta

from apps.accounts.permissions import IsDirectorOrAbove
from apps.profiles.models import Profile, ProfileStatusHistory
from apps.candidates.models import Candidate, CandidateProfile, CandidateDocument, CandidateNote
from apps.clients.models import Client
from apps.evaluations.models import CandidateEvaluation
from apps.accounts.models import User


# ════════════════════════════════════════════════════════════════════
# 1. REPORTE DE PERFIL INDIVIDUAL
# ════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def profile_report(request, profile_id):
    """
    Reporte completo de un perfil individual (vacante)
    GET /api/director/reports/profile/{id}/
    
    Retorna toda la información del perfil incluyendo:
    - Datos básicos del perfil
    - Información del cliente
    - Supervisor asignado
    - Estadísticas de candidatos
    - Progreso del proceso
    - Historial de cambios de estado
    """
    try:
        profile = Profile.objects.select_related(
            'client', 
            'assigned_to', 
            'created_by'
        ).get(id=profile_id)
    except Profile.DoesNotExist:
        return Response(
            {'error': 'Perfil no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ============================================
    # DATOS BÁSICOS DEL PERFIL
    # ============================================
    profile_data = {
        'id': profile.id,
        'position_title': profile.position_title,
        'status': profile.status,
        'status_display': profile.get_status_display(),
        'priority': profile.priority,
        'service_type': profile.service_type,
        'location': {
            'city': profile.location_city,
            'state': profile.location_state,
            'work_mode': profile.work_mode,
        },
        'salary': {
            'min': profile.salary_min,
            'max': profile.salary_max,
            'currency': profile.salary_currency,
            'period': profile.salary_period,
        },
        'experience_required': profile.experience_required,
        'education_level': profile.education_level,
        'description': profile.job_description,
        'requirements': profile.requirements,
        'benefits': profile.benefits,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat(),
        'completed_at': profile.completed_at.isoformat() if profile.completed_at else None,
    }
    
    # ============================================
    # INFORMACIÓN DEL CLIENTE
    # ============================================
    client_data = {
        'id': profile.client.id,
        'company_name': profile.client.company_name,
        'industry': profile.client.industry,
        'contact_name': profile.client.contact_name,
        'contact_email': profile.client.contact_email,
        'contact_phone': profile.client.contact_phone,
    }
    
    # ============================================
    # SUPERVISOR ASIGNADO
    # ============================================
    supervisor_data = None
    if profile.assigned_to:
        supervisor_data = {
            'id': profile.assigned_to.id,
            'name': profile.assigned_to.get_full_name(),
            'email': profile.assigned_to.email,
        }
    
    # ============================================
    # ESTADÍSTICAS DE CANDIDATOS
    # ============================================
    applications = CandidateProfile.objects.filter(profile=profile)
    
    total_candidates = applications.count()
    
    candidates_by_status = applications.values('status').annotate(
        count=Count('id')
    )
    
    candidates_stats = {
        'total': total_candidates,
        'by_status': {item['status']: item['count'] for item in candidates_by_status},
        'applied': applications.filter(status=CandidateProfile.STATUS_APPLIED).count(),
        'screening': applications.filter(status=CandidateProfile.STATUS_SCREENING).count(),
        'shortlisted': applications.filter(status=CandidateProfile.STATUS_SHORTLISTED).count(),
        'interviewed': applications.filter(status=CandidateProfile.STATUS_INTERVIEWED).count(),
        'offered': applications.filter(status=CandidateProfile.STATUS_OFFERED).count(),
        'accepted': applications.filter(status=CandidateProfile.STATUS_ACCEPTED).count(),
        'rejected': applications.filter(status=CandidateProfile.STATUS_REJECTED).count(),
    }
    
    # ============================================
    # PROGRESO DEL PROCESO
    # ============================================
    days_open = (timezone.now() - profile.created_at).days
    days_to_complete = None
    if profile.completed_at:
        days_to_complete = (profile.completed_at - profile.created_at).days
    
    progress = {
        'days_open': days_open,
        'days_to_complete': days_to_complete,
        'is_completed': profile.status == Profile.STATUS_COMPLETED,
        'is_cancelled': profile.status == Profile.STATUS_CANCELLED,
    }
    
    # ============================================
    # HISTORIAL DE CAMBIOS DE ESTADO
    # ============================================
    status_history = ProfileStatusHistory.objects.filter(
        profile=profile
    ).select_related('changed_by').order_by('-timestamp')[:20]
    
    history_data = []
    for entry in status_history:
        history_data.append({
            'from_status': entry.from_status,
            'to_status': entry.to_status,
            'from_status_display': entry.get_from_status_display(),
            'to_status_display': entry.get_to_status_display(),
            'changed_by': entry.changed_by.get_full_name() if entry.changed_by else None,
            'notes': entry.notes,
            'timestamp': entry.timestamp.isoformat(),
        })
    
    # ============================================
    # RESPUESTA FINAL
    # ============================================
    return Response({
        'profile': profile_data,
        'client': client_data,
        'supervisor': supervisor_data,
        'candidates_stats': candidates_stats,
        'progress': progress,
        'status_history': history_data,
        'generated_at': timezone.now().isoformat(),
    })


# ════════════════════════════════════════════════════════════════════
# 2. REPORTE DE CANDIDATOS DE UN PERFIL
# ════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def profile_candidates_report(request, profile_id):
    """
    Reporte de todos los candidatos que aplicaron a un perfil
    GET /api/director/reports/profile/{id}/candidates/
    
    Query params:
    - status: filtrar por estado (opcional)
    """
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Response(
            {'error': 'Perfil no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Filtro por estado (opcional)
    status_filter = request.query_params.get('status')
    
    applications = CandidateProfile.objects.filter(
        profile=profile
    ).select_related('candidate').order_by('-applied_at')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # ============================================
    # CONSTRUIR LISTA DE CANDIDATOS
    # ============================================
    candidates_data = []
    
    for app in applications:
        candidate = app.candidate
        
        # Contar documentos del candidato
        documents_count = CandidateDocument.objects.filter(
            candidate=candidate
        ).count()
        
        # Contar evaluaciones del candidato para este perfil
        evaluations_count = CandidateEvaluation.objects.filter(
            candidate=candidate,
            profile=profile
        ).count()
        
        candidates_data.append({
            'application_id': app.id,
            'candidate_id': candidate.id,
            'full_name': candidate.full_name,
            'email': candidate.email,
            'phone': candidate.phone,
            'location': f"{candidate.city}, {candidate.state}",
            'current_position': candidate.current_position,
            'current_company': candidate.current_company,
            'years_of_experience': candidate.years_of_experience,
            'education_level': candidate.education_level,
            'status': app.status,
            'status_display': app.get_status_display(),
            'match_percentage': app.match_percentage,
            'overall_rating': app.overall_rating,
            'applied_at': app.applied_at.isoformat(),
            'interview_date': app.interview_date.isoformat() if app.interview_date else None,
            'offer_date': app.offer_date.isoformat() if app.offer_date else None,
            'rejection_reason': app.rejection_reason,
            'documents_count': documents_count,
            'evaluations_count': evaluations_count,
        })
    
    # ============================================
    # ESTADÍSTICAS RESUMEN
    # ============================================
    total = len(candidates_data)
    by_status = {}
    for app in applications:
        status_key = app.status
        by_status[status_key] = by_status.get(status_key, 0) + 1
    
    avg_match = applications.aggregate(
        avg=Avg('match_percentage')
    )['avg'] or 0
    
    # ============================================
    # RESPUESTA FINAL
    # ============================================
    return Response({
        'profile': {
            'id': profile.id,
            'title': profile.position_title,
            'client': profile.client.company_name,
        },
        'summary': {
            'total_candidates': total,
            'by_status': by_status,
            'avg_match_percentage': round(avg_match, 1),
        },
        'candidates': candidates_data,
        'generated_at': timezone.now().isoformat(),
    })


# ════════════════════════════════════════════════════════════════════
# 3. TIMELINE / PROCESO COMPLETO DE UN PERFIL
# ════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def profile_timeline_report(request, profile_id):
    """
    Timeline completo del proceso de un perfil
    GET /api/director/reports/profile/{id}/timeline/
    
    Retorna una línea de tiempo con todos los eventos importantes:
    - Creación del perfil
    - Cambios de estado
    - Candidatos que aplicaron
    - Evaluaciones realizadas
    - Comentarios importantes
    """
    try:
        profile = Profile.objects.select_related('client', 'assigned_to').get(id=profile_id)
    except Profile.DoesNotExist:
        return Response(
            {'error': 'Perfil no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    timeline = []
    
    # ============================================
    # 1. CREACIÓN DEL PERFIL
    # ============================================
    timeline.append({
        'type': 'profile_created',
        'title': 'Perfil Creado',
        'description': f'Se creó el perfil para {profile.position_title}',
        'user': profile.created_by.get_full_name() if profile.created_by else 'Sistema',
        'timestamp': profile.created_at.isoformat(),
        'icon': 'fas fa-plus-circle',
        'color': 'blue',
    })
    
    # ============================================
    # 2. CAMBIOS DE ESTADO
    # ============================================
    status_changes = ProfileStatusHistory.objects.filter(
        profile=profile
    ).select_related('changed_by').order_by('timestamp')
    
    for change in status_changes:
        timeline.append({
            'type': 'status_change',
            'title': 'Cambio de Estado',
            'description': f'De "{change.get_from_status_display()}" a "{change.get_to_status_display()}"',
            'user': change.changed_by.get_full_name() if change.changed_by else 'Sistema',
            'notes': change.notes,
            'timestamp': change.timestamp.isoformat(),
            'icon': 'fas fa-exchange-alt',
            'color': 'purple',
        })
    
    # ============================================
    # 3. CANDIDATOS QUE APLICARON
    # ============================================
    applications = CandidateProfile.objects.filter(
        profile=profile
    ).select_related('candidate').order_by('applied_at')
    
    for app in applications:
        timeline.append({
            'type': 'candidate_applied',
            'title': 'Candidato Aplicó',
            'description': f'{app.candidate.full_name} aplicó a la posición',
            'user': app.candidate.full_name,
            'timestamp': app.applied_at.isoformat(),
            'icon': 'fas fa-user-plus',
            'color': 'green',
            'candidate_id': app.candidate.id,
            'application_id': app.id,
        })
        
        # Agregar cambios de estado del candidato
        if app.interview_date:
            timeline.append({
                'type': 'interview_scheduled',
                'title': 'Entrevista Agendada',
                'description': f'Entrevista con {app.candidate.full_name}',
                'timestamp': app.interview_date.isoformat(),
                'icon': 'fas fa-calendar-check',
                'color': 'orange',
                'candidate_id': app.candidate.id,
            })
        
        if app.offer_date:
            timeline.append({
                'type': 'offer_extended',
                'title': 'Oferta Extendida',
                'description': f'Oferta enviada a {app.candidate.full_name}',
                'timestamp': app.offer_date.isoformat(),
                'icon': 'fas fa-handshake',
                'color': 'yellow',
                'candidate_id': app.candidate.id,
            })
        
        if app.status == CandidateProfile.STATUS_ACCEPTED:
            timeline.append({
                'type': 'offer_accepted',
                'title': 'Oferta Aceptada',
                'description': f'{app.candidate.full_name} aceptó la oferta',
                'timestamp': app.applied_at.isoformat(),  # Usar una fecha aproximada
                'icon': 'fas fa-check-circle',
                'color': 'green',
                'candidate_id': app.candidate.id,
            })
    
    # ============================================
    # 4. COMPLETADO/CANCELADO
    # ============================================
    if profile.completed_at:
        timeline.append({
            'type': 'profile_completed',
            'title': 'Perfil Completado',
            'description': 'El proceso de reclutamiento se completó exitosamente',
            'timestamp': profile.completed_at.isoformat(),
            'icon': 'fas fa-flag-checkered',
            'color': 'green',
        })
    
    # ============================================
    # ORDENAR POR FECHA
    # ============================================
    timeline.sort(key=lambda x: x['timestamp'])
    
    # ============================================
    # RESPUESTA FINAL
    # ============================================
    return Response({
        'profile': {
            'id': profile.id,
            'title': profile.position_title,
            'client': profile.client.company_name,
            'status': profile.status,
        },
        'timeline': timeline,
        'total_events': len(timeline),
        'generated_at': timezone.now().isoformat(),
    })


# ════════════════════════════════════════════════════════════════════
# 4. REPORTE COMPLETO DE UN CANDIDATO
# ════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def candidate_full_report(request, candidate_id):
    """
    Reporte completo de un candidato individual
    GET /api/director/reports/candidate/{id}/
    
    Incluye:
    - Información personal completa
    - Todas sus aplicaciones a perfiles
    - Documentos adjuntos
    - Evaluaciones recibidas
    - Notas del proceso
    """
    try:
        candidate = Candidate.objects.select_related('assigned_to').get(id=candidate_id)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Candidato no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ============================================
    # INFORMACIÓN PERSONAL
    # ============================================
    personal_data = {
        'id': candidate.id,
        'full_name': candidate.full_name,
        'email': candidate.email,
        'phone': candidate.phone,
        'secondary_phone': candidate.secondary_phone,
        'location': {
            'city': candidate.city,
            'state': candidate.state,
        },
        'current_position': candidate.current_position,
        'current_company': candidate.current_company,
        'years_of_experience': candidate.years_of_experience,
        'education_level': candidate.education_level,
        'university': candidate.university,
        'degree': candidate.degree,
        'skills': candidate.skills,
        'certifications': candidate.certifications,
        'languages': candidate.languages,
        'salary_expectation': {
            'min': candidate.salary_expectation_min,
            'max': candidate.salary_expectation_max,
            'currency': candidate.salary_currency,
        },
        'availability': candidate.availability,
        'linkedin_url': candidate.linkedin_url,
        'portfolio_url': candidate.portfolio_url,
        'github_url': candidate.github_url,
        'status': candidate.status,
        'created_at': candidate.created_at.isoformat(),
    }
    
    # ============================================
    # APLICACIONES A PERFILES
    # ============================================
    applications = CandidateProfile.objects.filter(
        candidate=candidate
    ).select_related('profile', 'profile__client').order_by('-applied_at')
    
    applications_data = []
    for app in applications:
        applications_data.append({
            'id': app.id,
            'profile': {
                'id': app.profile.id,
                'title': app.profile.position_title,
                'client': app.profile.client.company_name,
            },
            'status': app.status,
            'status_display': app.get_status_display(),
            'match_percentage': app.match_percentage,
            'overall_rating': app.overall_rating,
            'applied_at': app.applied_at.isoformat(),
            'interview_date': app.interview_date.isoformat() if app.interview_date else None,
            'offer_date': app.offer_date.isoformat() if app.offer_date else None,
            'rejection_reason': app.rejection_reason,
        })
    
    # ============================================
    # DOCUMENTOS
    # ============================================
    documents = CandidateDocument.objects.filter(
        candidate=candidate
    ).order_by('-uploaded_at')
    
    documents_data = []
    for doc in documents:
        documents_data.append({
            'id': doc.id,
            'type': doc.document_type,
            'filename': doc.original_filename,
            'description': doc.description,
            'uploaded_at': doc.uploaded_at.isoformat(),
            'file_url': doc.file.url if doc.file else None,
        })
    
    # ============================================
    # EVALUACIONES
    # ============================================
    evaluations = CandidateEvaluation.objects.filter(
        candidate=candidate
    ).select_related('profile', 'template', 'evaluator').order_by('-completed_at')
    
    evaluations_data = []
    for evaluation in evaluations:
        evaluations_data.append({
            'id': evaluation.id,
            'profile': {
                'id': evaluation.profile.id,
                'title': evaluation.profile.position_title,
            },
            'template': evaluation.template.title if evaluation.template else None,
            'evaluator': evaluation.evaluator.get_full_name() if evaluation.evaluator else None,
            'score': evaluation.overall_score,
            'status': evaluation.status,
            'completed_at': evaluation.completed_at.isoformat() if evaluation.completed_at else None,
        })
    
    # ============================================
    # NOTAS
    # ============================================
    notes = CandidateNote.objects.filter(
        candidate=candidate
    ).select_related('created_by').order_by('-created_at')[:10]
    
    notes_data = []
    for note in notes:
        notes_data.append({
            'id': note.id,
            'type': note.note_type,
            'content': note.content,
            'created_by': note.created_by.get_full_name() if note.created_by else None,
            'created_at': note.created_at.isoformat(),
        })
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    stats = {
        'total_applications': applications.count(),
        'active_applications': applications.exclude(
            status__in=[CandidateProfile.STATUS_REJECTED, CandidateProfile.STATUS_WITHDRAWN]
        ).count(),
        'total_documents': documents.count(),
        'total_evaluations': evaluations.count(),
        'total_notes': CandidateNote.objects.filter(candidate=candidate).count(),
        'avg_match_percentage': applications.aggregate(avg=Avg('match_percentage'))['avg'] or 0,
    }
    
    # ============================================
    # RESPUESTA FINAL
    # ============================================
    return Response({
        'personal_info': personal_data,
        'applications': applications_data,
        'documents': documents_data,
        'evaluations': evaluations_data,
        'notes': notes_data,
        'statistics': stats,
        'generated_at': timezone.now().isoformat(),
    })


# ════════════════════════════════════════════════════════════════════
# 5. REPORTE COMPLETO DE UN CLIENTE
# ════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDirectorOrAbove])
def client_full_report(request, client_id):
    """
    Reporte completo de un cliente
    GET /api/director/reports/client/{id}/
    
    Incluye:
    - Información del cliente
    - Todos sus perfiles (vacantes)
    - Estadísticas generales
    - Historial de colaboración
    """
    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return Response(
            {'error': 'Cliente no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # ============================================
    # INFORMACIÓN DEL CLIENTE
    # ============================================
    client_data = {
        'id': client.id,
        'company_name': client.company_name,
        'industry': client.industry,
        'website': client.website,
        'contact_name': client.contact_name,
        'contact_email': client.contact_email,
        'contact_phone': client.contact_phone,
        'address': client.address,
        'city': client.city,
        'state': client.state,
        'postal_code': client.postal_code,
        'notes': client.notes,
        'created_at': client.created_at.isoformat(),
    }
    
    # ============================================
    # PERFILES (VACANTES)
    # ============================================
    profiles = Profile.objects.filter(client=client).order_by('-created_at')
    
    profiles_data = []
    for profile in profiles:
        # Contar candidatos del perfil
        candidates_count = CandidateProfile.objects.filter(profile=profile).count()
        
        profiles_data.append({
            'id': profile.id,
            'title': profile.position_title,
            'status': profile.status,
            'status_display': profile.get_status_display(),
            'priority': profile.priority,
            'candidates_count': candidates_count,
            'created_at': profile.created_at.isoformat(),
            'completed_at': profile.completed_at.isoformat() if profile.completed_at else None,
        })
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    total_profiles = profiles.count()
    completed_profiles = profiles.filter(status=Profile.STATUS_COMPLETED).count()
    active_profiles = profiles.exclude(
        status__in=[Profile.STATUS_COMPLETED, Profile.STATUS_CANCELLED]
    ).count()
    
    success_rate = 0
    if total_profiles > 0:
        success_rate = (completed_profiles / total_profiles) * 100
    
    # Tiempo promedio de completado
    completed_with_time = profiles.filter(
        status=Profile.STATUS_COMPLETED,
        completed_at__isnull=False
    )
    
    avg_time = None
    if completed_with_time.exists():
        avg_time_delta = completed_with_time.aggregate(
            avg=Avg(F('completed_at') - F('created_at'))
        )['avg']
        if avg_time_delta:
            avg_time = avg_time_delta.days
    
    # Total de candidatos gestionados
    total_candidates = CandidateProfile.objects.filter(
        profile__client=client
    ).count()
    
    stats = {
        'total_profiles': total_profiles,
        'completed_profiles': completed_profiles,
        'active_profiles': active_profiles,
        'cancelled_profiles': profiles.filter(status=Profile.STATUS_CANCELLED).count(),
        'success_rate': round(success_rate, 1),
        'avg_days_to_complete': avg_time,
        'total_candidates_managed': total_candidates,
    }
    
    # ============================================
    # PERFILES POR ESTADO
    # ============================================
    profiles_by_status = profiles.values('status').annotate(count=Count('id'))
    status_breakdown = {item['status']: item['count'] for item in profiles_by_status}
    
    # ============================================
    # RESPUESTA FINAL
    # ============================================
    return Response({
        'client': client_data,
        'profiles': profiles_data,
        'statistics': stats,
        'profiles_by_status': status_breakdown,
        'generated_at': timezone.now().isoformat(),
    })