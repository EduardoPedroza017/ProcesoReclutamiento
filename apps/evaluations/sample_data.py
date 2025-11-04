"""
Script para generar datos de prueba del sistema de evaluaciones
Ejecutar: python manage.py shell < this_script.py
O desde Django shell: exec(open('this_script.py').read())
"""

from django.contrib.auth import get_user_model
from apps.evaluations.models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer,
    EvaluationComment
)
from apps.candidates.models import Candidate
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print("🚀 Generando datos de prueba para el sistema de evaluaciones...")
print()

# ============================================
# 1. CREAR USUARIOS DE PRUEBA
# ============================================
print("👤 Creando usuarios de prueba...")

admin_user, _ = User.objects.get_or_create(
    email='admin@recruitment.com',
    defaults={
        'first_name': 'Admin',
        'last_name': 'Sistema',
        'role': 'admin'
    }
)
admin_user.set_password('admin123')
admin_user.save()
print(f"   ✓ Admin: {admin_user.email}")

director, _ = User.objects.get_or_create(
    email='director@recruitment.com',
    defaults={
        'first_name': 'María',
        'last_name': 'Directora',
        'role': 'director'
    }
)
director.set_password('director123')
director.save()
print(f"   ✓ Director: {director.email}")

supervisor, _ = User.objects.get_or_create(
    email='supervisor@recruitment.com',
    defaults={
        'first_name': 'Juan',
        'last_name': 'Supervisor',
        'role': 'supervisor'
    }
)
supervisor.set_password('supervisor123')
supervisor.save()
print(f"   ✓ Supervisor: {supervisor.email}")

print()

# ============================================
# 2. CREAR CANDIDATOS DE PRUEBA
# ============================================
print("👥 Creando candidatos de prueba...")

candidatos = []
candidatos_data = [
    {
        'first_name': 'Carlos',
        'last_name': 'García',
        'email': 'carlos.garcia@email.com',
        'phone': '+52 55 1234 5678'
    },
    {
        'first_name': 'Ana',
        'last_name': 'Martínez',
        'email': 'ana.martinez@email.com',
        'phone': '+52 55 2345 6789'
    },
    {
        'first_name': 'Pedro',
        'last_name': 'López',
        'email': 'pedro.lopez@email.com',
        'phone': '+52 55 3456 7890'
    }
]

for data in candidatos_data:
    candidato, created = Candidate.objects.get_or_create(
        email=data['email'],
        defaults=data
    )
    candidatos.append(candidato)
    status = "✓" if created else "→"
    print(f"   {status} {candidato.full_name}")

print()

# ============================================
# 3. CREAR PLANTILLAS DE EVALUACIÓN
# ============================================
print("📋 Creando plantillas de evaluación...")

# Plantilla 1: Evaluación Python
python_template, created = EvaluationTemplate.objects.get_or_create(
    title='Evaluación Python Developer',
    defaults={
        'description': 'Evaluación técnica para desarrolladores Python mid-level a senior',
        'category': 'technical',
        'duration_minutes': 90,
        'passing_score': 70.00,
        'is_active': True,
        'created_by': director
    }
)
print(f"   {'✓' if created else '→'} {python_template.title}")

# Plantilla 2: Evaluación de Liderazgo
leadership_template, created = EvaluationTemplate.objects.get_or_create(
    title='Evaluación de Liderazgo',
    defaults={
        'description': 'Evaluación de habilidades de liderazgo y gestión de equipos',
        'category': 'leadership',
        'duration_minutes': 60,
        'passing_score': 75.00,
        'is_active': True,
        'created_by': director
    }
)
print(f"   {'✓' if created else '→'} {leadership_template.title}")

# Plantilla 3: Evaluación de Inglés
english_template, created = EvaluationTemplate.objects.get_or_create(
    title='Evaluación de Inglés Técnico',
    defaults={
        'description': 'Evaluación de comprensión y uso del inglés técnico',
        'category': 'language',
        'duration_minutes': 45,
        'passing_score': 80.00,
        'is_active': True,
        'created_by': director
    }
)
print(f"   {'✓' if created else '→'} {english_template.title}")

print()

# ============================================
# 4. CREAR PREGUNTAS PARA PYTHON
# ============================================
print("❓ Creando preguntas para evaluación Python...")

python_questions = [
    {
        'question_text': '¿Qué es un decorador en Python?',
        'question_type': 'multiple_choice',
        'options': [
            'A) Una función que modifica otra función',
            'B) Un tipo de variable especial',
            'C) Un método de clase estático',
            'D) Una estructura de datos'
        ],
        'correct_answer': 'A) Una función que modifica otra función',
        'points': 10.00,
        'order': 1
    },
    {
        'question_text': '¿Cuál es la diferencia principal entre una lista y una tupla?',
        'question_type': 'multiple_choice',
        'options': [
            'A) Las listas son más rápidas',
            'B) Las tuplas son inmutables',
            'C) Las listas solo almacenan números',
            'D) Las tuplas no pueden contener objetos'
        ],
        'correct_answer': 'B) Las tuplas son inmutables',
        'points': 10.00,
        'order': 2
    },
    {
        'question_text': 'Explica la diferencia entre @staticmethod y @classmethod en Python.',
        'question_type': 'long_text',
        'points': 15.00,
        'order': 3,
        'help_text': 'Proporciona ejemplos de uso de cada uno.'
    },
    {
        'question_text': '¿Qué hace el siguiente código?\n\nresult = [x**2 for x in range(10) if x % 2 == 0]',
        'question_type': 'multiple_choice',
        'options': [
            'A) Crea una lista con los números pares del 0 al 9',
            'B) Crea una lista con el cuadrado de los números pares del 0 al 9',
            'C) Crea una lista con el cuadrado de todos los números del 0 al 9',
            'D) Genera un error de sintaxis'
        ],
        'correct_answer': 'B) Crea una lista con el cuadrado de los números pares del 0 al 9',
        'points': 10.00,
        'order': 4
    },
    {
        'question_text': 'Escribe una función que devuelva el n-ésimo número de Fibonacci.',
        'question_type': 'code',
        'points': 20.00,
        'order': 5,
        'help_text': 'Puedes usar recursión o iteración.'
    },
    {
        'question_text': 'En una escala del 1 al 10, ¿cuál es tu nivel de experiencia con Django?',
        'question_type': 'scale',
        'points': 5.00,
        'order': 6,
        'correct_answer': '7'  # Valor de referencia
    },
    {
        'question_text': 'Python fue creado por Guido van Rossum.',
        'question_type': 'true_false',
        'correct_answer': 'True',
        'points': 5.00,
        'order': 7
    },
    {
        'question_text': 'Describe tu proyecto más complejo en Python y los desafíos que enfrentaste.',
        'question_type': 'long_text',
        'points': 25.00,
        'order': 8,
        'help_text': 'Incluye tecnologías utilizadas y resultados obtenidos.'
    }
]

for q_data in python_questions:
    question, created = EvaluationQuestion.objects.get_or_create(
        template=python_template,
        order=q_data['order'],
        defaults=q_data
    )
    status = "✓" if created else "→"
    print(f"   {status} Pregunta {question.order}: {question.question_text[:50]}...")

print()

# ============================================
# 5. CREAR PREGUNTAS PARA LIDERAZGO
# ============================================
print("❓ Creando preguntas para evaluación de Liderazgo...")

leadership_questions = [
    {
        'question_text': '¿Cuál consideras que es la cualidad más importante de un líder?',
        'question_type': 'multiple_choice',
        'options': [
            'A) Autoridad',
            'B) Empatía',
            'C) Conocimiento técnico',
            'D) Experiencia'
        ],
        'correct_answer': 'B) Empatía',
        'points': 10.00,
        'order': 1
    },
    {
        'question_text': 'Describe una situación en la que tuviste que resolver un conflicto en tu equipo.',
        'question_type': 'long_text',
        'points': 20.00,
        'order': 2
    },
    {
        'question_text': 'En una escala del 1 al 10, ¿qué tan cómodo te sientes delegando tareas?',
        'question_type': 'scale',
        'points': 10.00,
        'order': 3
    },
    {
        'question_text': '¿Cómo motivarías a un equipo que está desmotivado?',
        'question_type': 'long_text',
        'points': 20.00,
        'order': 4
    }
]

for q_data in leadership_questions:
    question, created = EvaluationQuestion.objects.get_or_create(
        template=leadership_template,
        order=q_data['order'],
        defaults=q_data
    )
    status = "✓" if created else "→"
    print(f"   {status} Pregunta {question.order}: {question.question_text[:50]}...")

print()

# ============================================
# 6. ASIGNAR EVALUACIONES A CANDIDATOS
# ============================================
print("📝 Asignando evaluaciones a candidatos...")

# Evaluación 1: Python a Carlos (Completada)
eval1, created = CandidateEvaluation.objects.get_or_create(
    template=python_template,
    candidate=candidatos[0],
    assigned_by=supervisor,
    defaults={
        'status': 'completed',
        'started_at': timezone.now() - timedelta(days=2, hours=2),
        'completed_at': timezone.now() - timedelta(days=2),
        'expires_at': timezone.now() + timedelta(days=5),
        'time_taken_minutes': 85
    }
)
print(f"   {'✓' if created else '→'} Evaluación Python para {candidatos[0].full_name}")

# Evaluación 2: Python a Ana (En progreso)
eval2, created = CandidateEvaluation.objects.get_or_create(
    template=python_template,
    candidate=candidatos[1],
    assigned_by=supervisor,
    defaults={
        'status': 'in_progress',
        'started_at': timezone.now() - timedelta(hours=1),
        'expires_at': timezone.now() + timedelta(days=5)
    }
)
print(f"   {'✓' if created else '→'} Evaluación Python para {candidatos[1].full_name}")

# Evaluación 3: Liderazgo a Pedro (Pendiente)
eval3, created = CandidateEvaluation.objects.get_or_create(
    template=leadership_template,
    candidate=candidatos[2],
    assigned_by=director,
    defaults={
        'status': 'pending',
        'expires_at': timezone.now() + timedelta(days=7)
    }
)
print(f"   {'✓' if created else '→'} Evaluación Liderazgo para {candidatos[2].full_name}")

print()

# ============================================
# 7. CREAR RESPUESTAS PARA EVALUACIÓN COMPLETADA
# ============================================
if eval1.status == 'completed' and eval1.answers.count() == 0:
    print("💬 Creando respuestas para evaluación completada de Carlos...")
    
    python_qs = python_template.questions.all()
    
    # Respuestas de Carlos
    answers_data = [
        {'question': python_qs[0], 'selected_option': 'A) Una función que modifica otra función', 'is_correct': True, 'points_earned': 10.00},
        {'question': python_qs[1], 'selected_option': 'B) Las tuplas son inmutables', 'is_correct': True, 'points_earned': 10.00},
        {'question': python_qs[2], 'answer_text': '@staticmethod no recibe ni self ni cls, mientras que @classmethod recibe cls como primer parámetro...'},
        {'question': python_qs[3], 'selected_option': 'B) Crea una lista con el cuadrado de los números pares del 0 al 9', 'is_correct': True, 'points_earned': 10.00},
        {'question': python_qs[4], 'answer_text': 'def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)'},
        {'question': python_qs[5], 'scale_value': 8, 'is_correct': True, 'points_earned': 5.00},
        {'question': python_qs[6], 'selected_option': 'True', 'is_correct': True, 'points_earned': 5.00},
        {'question': python_qs[7], 'answer_text': 'Mi proyecto más complejo fue un sistema de gestión de inventarios usando Django y React...'}
    ]
    
    for answer_data in answers_data:
        answer, _ = EvaluationAnswer.objects.get_or_create(
            evaluation=eval1,
            question=answer_data['question'],
            defaults={k: v for k, v in answer_data.items() if k != 'question'}
        )
        print(f"   ✓ Respuesta a: {answer.question.question_text[:40]}...")
    
    # Calcular puntuación automática
    eval1.calculate_score()
    print(f"   ✓ Puntuación calculada: {eval1.final_score}%")
    print()

# ============================================
# 8. AGREGAR COMENTARIOS
# ============================================
print("💭 Agregando comentarios a evaluaciones...")

comment1, _ = EvaluationComment.objects.get_or_create(
    evaluation=eval1,
    user=supervisor,
    defaults={
        'comment': 'El candidato demostró un sólido conocimiento de Python. Sus respuestas fueron claras y precisas.',
        'is_internal': False
    }
)
print(f"   ✓ Comentario público agregado a evaluación de {eval1.candidate.full_name}")

comment2, _ = EvaluationComment.objects.get_or_create(
    evaluation=eval1,
    user=director,
    defaults={
        'comment': 'Recomiendo avanzar a la siguiente etapa. Considerarlo para posición senior.',
        'is_internal': True
    }
)
print(f"   ✓ Comentario interno agregado a evaluación de {eval1.candidate.full_name}")

print()

# ============================================
# RESUMEN
# ============================================
print("=" * 60)
print("✅ DATOS DE PRUEBA GENERADOS EXITOSAMENTE")
print("=" * 60)
print()
print("📊 RESUMEN:")
print(f"   • Usuarios creados: {User.objects.count()}")
print(f"   • Candidatos creados: {Candidate.objects.count()}")
print(f"   • Plantillas de evaluación: {EvaluationTemplate.objects.count()}")
print(f"   • Preguntas totales: {EvaluationQuestion.objects.count()}")
print(f"   • Evaluaciones asignadas: {CandidateEvaluation.objects.count()}")
print(f"   • Respuestas registradas: {EvaluationAnswer.objects.count()}")
print(f"   • Comentarios: {EvaluationComment.objects.count()}")
print()
print("🔐 CREDENCIALES DE ACCESO:")
print("   Admin:")
print("      Email: admin@recruitment.com")
print("      Password: admin123")
print()
print("   Director:")
print("      Email: director@recruitment.com")
print("      Password: director123")
print()
print("   Supervisor:")
print("      Email: supervisor@recruitment.com")
print("      Password: supervisor123")
print()
print("🌐 ACCESO:")
print("   Panel Admin: http://localhost:8000/admin/")
print("   API: http://localhost:8000/api/evaluations/")
print()
print("=" * 60)