"""
URLs para el sistema de evaluaciones
Define los endpoints de la API REST
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvaluationTemplateViewSet,
    EvaluationQuestionViewSet,
    CandidateEvaluationViewSet,
    EvaluationAnswerViewSet,
    EvaluationCommentViewSet
)

# Crear router para registrar los viewsets
router = DefaultRouter()

# Registrar viewsets con sus prefijos
router.register(r'templates', EvaluationTemplateViewSet, basename='template')
router.register(r'questions', EvaluationQuestionViewSet, basename='question')
router.register(r'candidate-evaluations', CandidateEvaluationViewSet, basename='candidate-evaluation')
router.register(r'answers', EvaluationAnswerViewSet, basename='answer')
router.register(r'comments', EvaluationCommentViewSet, basename='comment')

app_name = 'evaluations'

urlpatterns = [
    path('', include(router.urls)),
]

"""
ENDPOINTS DISPONIBLES:

═══════════════════════════════════════════════════════════════════
PLANTILLAS DE EVALUACIÓN (Templates)
═══════════════════════════════════════════════════════════════════
GET     /api/evaluations/templates/                    - Listar plantillas
POST    /api/evaluations/templates/                    - Crear plantilla
GET     /api/evaluations/templates/{id}/               - Detalle de plantilla
PUT     /api/evaluations/templates/{id}/               - Actualizar plantilla
PATCH   /api/evaluations/templates/{id}/               - Actualización parcial
DELETE  /api/evaluations/templates/{id}/               - Eliminar plantilla

Acciones especiales:
POST    /api/evaluations/templates/{id}/duplicate/     - Duplicar plantilla
GET     /api/evaluations/templates/{id}/statistics/    - Estadísticas de uso

═══════════════════════════════════════════════════════════════════
PREGUNTAS (Questions)
═══════════════════════════════════════════════════════════════════
GET     /api/evaluations/questions/                    - Listar preguntas
POST    /api/evaluations/questions/                    - Crear pregunta
GET     /api/evaluations/questions/{id}/               - Detalle de pregunta
PUT     /api/evaluations/questions/{id}/               - Actualizar pregunta
PATCH   /api/evaluations/questions/{id}/               - Actualización parcial
DELETE  /api/evaluations/questions/{id}/               - Eliminar pregunta

Acciones especiales:
POST    /api/evaluations/questions/bulk_create/        - Crear múltiples preguntas

═══════════════════════════════════════════════════════════════════
EVALUACIONES DE CANDIDATOS (Candidate Evaluations)
═══════════════════════════════════════════════════════════════════
GET     /api/evaluations/candidate-evaluations/        - Listar evaluaciones
POST    /api/evaluations/candidate-evaluations/        - Asignar evaluación
GET     /api/evaluations/candidate-evaluations/{id}/   - Detalle de evaluación
PUT     /api/evaluations/candidate-evaluations/{id}/   - Actualizar evaluación
PATCH   /api/evaluations/candidate-evaluations/{id}/   - Actualización parcial
DELETE  /api/evaluations/candidate-evaluations/{id}/   - Eliminar evaluación

Acciones especiales (flujo de evaluación):
POST    /api/evaluations/candidate-evaluations/{id}/start/      - Iniciar evaluación
POST    /api/evaluations/candidate-evaluations/{id}/submit/     - Enviar respuestas
POST    /api/evaluations/candidate-evaluations/{id}/complete/   - Marcar completada
POST    /api/evaluations/candidate-evaluations/{id}/review/     - Revisar y calificar

Consultas especiales:
GET     /api/evaluations/candidate-evaluations/my_evaluations/      - Mis evaluaciones
GET     /api/evaluations/candidate-evaluations/pending_reviews/     - Pendientes de revisión
GET     /api/evaluations/candidate-evaluations/statistics/          - Estadísticas generales

═══════════════════════════════════════════════════════════════════
RESPUESTAS (Answers)
═══════════════════════════════════════════════════════════════════
GET     /api/evaluations/answers/                      - Listar respuestas
POST    /api/evaluations/answers/                      - Crear respuesta
GET     /api/evaluations/answers/{id}/                 - Detalle de respuesta
PUT     /api/evaluations/answers/{id}/                 - Actualizar respuesta
PATCH   /api/evaluations/answers/{id}/                 - Actualización parcial
DELETE  /api/evaluations/answers/{id}/                 - Eliminar respuesta

═══════════════════════════════════════════════════════════════════
COMENTARIOS (Comments)
═══════════════════════════════════════════════════════════════════
GET     /api/evaluations/comments/                     - Listar comentarios
POST    /api/evaluations/comments/                     - Crear comentario
GET     /api/evaluations/comments/{id}/                - Detalle de comentario
PUT     /api/evaluations/comments/{id}/                - Actualizar comentario
PATCH   /api/evaluations/comments/{id}/                - Actualización parcial
DELETE  /api/evaluations/comments/{id}/                - Eliminar comentario

═══════════════════════════════════════════════════════════════════
PARÁMETROS DE FILTRADO DISPONIBLES
═══════════════════════════════════════════════════════════════════

Templates:
    ?category=technical                 - Filtrar por categoría
    ?is_active=true                     - Solo plantillas activas
    ?is_template=true                   - Solo plantillas reutilizables
    ?search=Python                      - Buscar en título y descripción

Questions:
    ?template=1                         - Preguntas de una plantilla
    ?question_type=multiple_choice      - Por tipo de pregunta
    ?is_required=true                   - Solo preguntas obligatorias

Candidate Evaluations:
    ?status=pending                     - Por estado
    ?template=1                         - Por plantilla
    ?candidate=1                        - Por candidato
    ?passed=true                        - Solo aprobadas
    ?search=John                        - Buscar en nombre candidato

Answers:
    ?evaluation=1                       - Respuestas de una evaluación
    ?question=1                         - Respuestas a una pregunta
    ?is_correct=true                    - Solo respuestas correctas

Comments:
    ?evaluation=1                       - Comentarios de una evaluación
    ?is_internal=true                   - Solo comentarios internos

═══════════════════════════════════════════════════════════════════
EJEMPLOS DE USO
═══════════════════════════════════════════════════════════════════

1. Crear una plantilla de evaluación:
POST /api/evaluations/templates/
{
    "title": "Evaluación Python Senior",
    "description": "Evaluación técnica para desarrolladores Python senior",
    "category": "technical",
    "duration_minutes": 90,
    "passing_score": 75.00,
    "is_active": true
}

2. Agregar preguntas a la plantilla:
POST /api/evaluations/questions/bulk_create/
{
    "template_id": 1,
    "questions": [
        {
            "question_text": "¿Qué es una lista por comprensión en Python?",
            "question_type": "multiple_choice",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "B) ...",
            "points": 5.00,
            "order": 1
        },
        {
            "question_text": "Explica la diferencia entre @staticmethod y @classmethod",
            "question_type": "long_text",
            "points": 10.00,
            "order": 2
        }
    ]
}

3. Asignar evaluación a un candidato:
POST /api/evaluations/candidate-evaluations/
{
    "template": 1,
    "candidate": 5,
    "expires_at": "2025-11-10T23:59:59Z"
}

4. Iniciar evaluación (por el candidato):
POST /api/evaluations/candidate-evaluations/1/start/

5. Enviar respuestas:
POST /api/evaluations/candidate-evaluations/1/submit/
{
    "answers": [
        {
            "question_id": 1,
            "selected_option": "B) ..."
        },
        {
            "question_id": 2,
            "answer_text": "Los métodos estáticos no reciben self ni cls..."
        }
    ]
}

6. Revisar y calificar (Director/Admin):
POST /api/evaluations/candidate-evaluations/1/review/
{
    "manual_score": 85.5,
    "evaluator_comments": "Excelente comprensión de los conceptos",
    "internal_notes": "Considerarlo para el proceso avanzado",
    "answer_feedback": [
        {
            "answer_id": 2,
            "feedback": "Respuesta completa y bien explicada",
            "points_earned": 10.00
        }
    ]
}

7. Ver estadísticas:
GET /api/evaluations/candidate-evaluations/statistics/
GET /api/evaluations/templates/1/statistics/

8. Ver evaluaciones pendientes de revisión:
GET /api/evaluations/candidate-evaluations/pending_reviews/
"""