"""
URLs para endpoints del Director de Reclutamiento
"""
from django.urls import path
from . import director_views

app_name = 'director'

urlpatterns = [
    # Dashboard principal
    path(
        'dashboard/',
        director_views.director_dashboard,
        name='dashboard'
    ),
    
    # Vistas generales
    path(
        'profiles/overview/',
        director_views.profiles_overview,
        name='profiles-overview'
    ),
    path(
        'candidates/overview/',
        director_views.candidates_overview,
        name='candidates-overview'
    ),
    
    # Rendimiento del equipo
    path(
        'team/performance/',
        director_views.team_performance,
        name='team-performance'
    ),
    
    # Analytics de clientes
    path(
        'clients/analytics/',
        director_views.client_analytics,
        name='client-analytics'
    ),
    
    # Reportes
    path(
        'reports/monthly/',
        director_views.monthly_report,
        name='monthly-report'
    ),
    
    # Acciones pendientes
    path(
        'pending-actions/',
        director_views.pending_actions,
        name='pending-actions'
    ),
    
    # Embudo de reclutamiento
    path(
        'funnel/',
        director_views.recruitment_funnel,
        name='recruitment-funnel'
    ),
]

"""
═══════════════════════════════════════════════════════════════════
ENDPOINTS DISPONIBLES PARA EL DIRECTOR
═══════════════════════════════════════════════════════════════════

📊 DASHBOARD Y MÉTRICAS
═══════════════════════════════════════════════════════════════════
GET /api/director/dashboard/
    Retorna: Métricas completas del sistema
    - Overview general (perfiles, candidatos, clientes)
    - Métricas del mes actual
    - Perfiles por estado y prioridad
    - Estadísticas de candidatos
    - Métricas de evaluaciones
    - Métricas de IA
    - Rendimiento del equipo
    - Pipeline de reclutamiento
    - Alertas y pendientes
    - Tendencias (gráficas)

GET /api/director/profiles/overview/
    Query params: status, priority, client_id, assigned_to, date_from, date_to
    Retorna: Vista general de perfiles con estadísticas

GET /api/director/candidates/overview/
    Query params: status, date_from, date_to
    Retorna: Vista general de candidatos

═══════════════════════════════════════════════════════════════════
👥 EQUIPO Y RENDIMIENTO
═══════════════════════════════════════════════════════════════════
GET /api/director/team/performance/
    Retorna: Rendimiento de cada supervisor
    - Perfiles asignados
    - Perfiles completados
    - Tasa de éxito
    - Candidatos gestionados
    - Evaluaciones revisadas
    - Tiempo promedio de cierre

═══════════════════════════════════════════════════════════════════
🏢 ANALYTICS DE CLIENTES
═══════════════════════════════════════════════════════════════════
GET /api/director/clients/analytics/
    Query params: client_id (opcional)
    Retorna:
    - Sin client_id: Analytics de todos los clientes (top 20)
    - Con client_id: Analytics detallado de un cliente específico
      * Total de perfiles
      * Perfiles completados
      * Tasa de éxito
      * Tiempo promedio de contratación
      * Perfiles por estado

═══════════════════════════════════════════════════════════════════
📈 REPORTES
═══════════════════════════════════════════════════════════════════
GET /api/director/reports/monthly/
    Query params: month (1-12), year
    Retorna: Reporte consolidado del mes
    - Perfiles creados y completados
    - Candidatos agregados y contratados
    - Evaluaciones completadas
    - Análisis de CVs realizados
    - Documentos generados
    - Clientes nuevos
    - Top 5 clientes más activos
    - Top 5 supervisores más productivos

═══════════════════════════════════════════════════════════════════
⚠️ ACCIONES PENDIENTES
═══════════════════════════════════════════════════════════════════
GET /api/director/pending-actions/
    Retorna: Acciones que requieren atención
    - Perfiles pendientes de aprobación (top 10)
    - Perfiles próximos a vencer (top 10)
    - Evaluaciones pendientes de revisión (top 10)
    - Perfiles sin supervisor asignado (top 10)
    - Total de acciones pendientes

═══════════════════════════════════════════════════════════════════
🎯 EMBUDO DE RECLUTAMIENTO
═══════════════════════════════════════════════════════════════════
GET /api/director/funnel/
    Retorna: Funnel completo del proceso
    - Total de perfiles
    - Perfiles aprobados
    - Candidatos activos
    - Candidatos calificados
    - En evaluación
    - En entrevistas
    - Con oferta
    - Contratados
    - Tasas de conversión entre etapas

═══════════════════════════════════════════════════════════════════
EJEMPLOS DE USO
═══════════════════════════════════════════════════════════════════

# 1. Obtener dashboard completo
GET /api/director/dashboard/

# 2. Ver perfiles de un cliente específico
GET /api/director/profiles/overview/?client_id=5

# 3. Ver rendimiento del equipo
GET /api/director/team/performance/

# 4. Obtener reporte mensual de octubre 2024
GET /api/director/reports/monthly/?month=10&year=2024

# 5. Ver analytics de un cliente
GET /api/director/clients/analytics/?client_id=3

# 6. Ver acciones pendientes
GET /api/director/pending-actions/

# 7. Ver embudo de reclutamiento
GET /api/director/funnel/

═══════════════════════════════════════════════════════════════════
"""