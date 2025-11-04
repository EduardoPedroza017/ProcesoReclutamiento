"""
Tests para el sistema de evaluaciones
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer
)
from apps.candidates.models import Candidate
from apps.profiles.models import Profile

User = get_user_model()


class EvaluationTemplateModelTest(TestCase):
    """Tests para el modelo EvaluationTemplate"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            role='director'
        )
        
        self.template = EvaluationTemplate.objects.create(
            title='Evaluación Python',
            description='Evaluación técnica de Python',
            category='technical',
            duration_minutes=60,
            passing_score=70.00,
            created_by=self.user
        )
    
    def test_template_creation(self):
        """Test de creación de plantilla"""
        self.assertEqual(self.template.title, 'Evaluación Python')
        self.assertEqual(self.template.category, 'technical')
        self.assertEqual(self.template.passing_score, 70.00)
    
    def test_template_str(self):
        """Test del método __str__"""
        expected = f"Evaluación Python (Técnica)"
        self.assertEqual(str(self.template), expected)
    
    def test_total_questions_property(self):
        """Test de la propiedad total_questions"""
        # Sin preguntas
        self.assertEqual(self.template.total_questions, 0)
        
        # Crear preguntas
        EvaluationQuestion.objects.create(
            template=self.template,
            question_text='¿Qué es Python?',
            question_type='short_text',
            points=5.00
        )
        EvaluationQuestion.objects.create(
            template=self.template,
            question_text='¿Qué es una lista?',
            question_type='short_text',
            points=5.00
        )
        
        self.assertEqual(self.template.total_questions, 2)
    
    def test_total_points_property(self):
        """Test de la propiedad total_points"""
        # Crear preguntas con diferentes puntos
        EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Pregunta 1',
            question_type='short_text',
            points=10.00
        )
        EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Pregunta 2',
            question_type='short_text',
            points=15.00
        )
        
        self.assertEqual(self.template.total_points, 25.00)


class EvaluationQuestionModelTest(TestCase):
    """Tests para el modelo EvaluationQuestion"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        
        self.template = EvaluationTemplate.objects.create(
            title='Evaluación Test',
            category='technical',
            created_by=self.user
        )
    
    def test_multiple_choice_question(self):
        """Test de pregunta de opción múltiple"""
        question = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='¿Cuál es la respuesta correcta?',
            question_type='multiple_choice',
            options=['A', 'B', 'C', 'D'],
            correct_answer='B',
            points=5.00
        )
        
        self.assertEqual(question.question_type, 'multiple_choice')
        self.assertTrue(question.is_auto_gradable())
        self.assertEqual(len(question.options), 4)
    
    def test_text_question(self):
        """Test de pregunta de texto"""
        question = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Explique el concepto',
            question_type='long_text',
            points=10.00
        )
        
        self.assertEqual(question.question_type, 'long_text')
        self.assertFalse(question.is_auto_gradable())
    
    def test_scale_question(self):
        """Test de pregunta de escala"""
        question = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Del 1 al 10, ¿qué tan...?',
            question_type='scale',
            points=5.00
        )
        
        self.assertEqual(question.question_type, 'scale')
        self.assertTrue(question.is_auto_gradable())


class CandidateEvaluationModelTest(TestCase):
    """Tests para el modelo CandidateEvaluation"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            email='evaluator@test.com',
            password='testpass123',
            role='director'
        )
        
        self.candidate = Candidate.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            phone='+1234567890'
        )
        
        self.template = EvaluationTemplate.objects.create(
            title='Evaluación Test',
            category='technical',
            passing_score=70.00,
            created_by=self.user
        )
        
        # Crear preguntas
        self.q1 = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Pregunta 1',
            question_type='multiple_choice',
            options=['A', 'B', 'C'],
            correct_answer='B',
            points=10.00
        )
        
        self.q2 = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Pregunta 2',
            question_type='true_false',
            correct_answer='True',
            points=10.00
        )
        
        self.evaluation = CandidateEvaluation.objects.create(
            template=self.template,
            candidate=self.candidate,
            assigned_by=self.user
        )
    
    def test_evaluation_creation(self):
        """Test de creación de evaluación"""
        self.assertEqual(self.evaluation.status, 'pending')
        self.assertIsNotNone(self.evaluation.assigned_at)
        self.assertIsNone(self.evaluation.started_at)
        self.assertIsNone(self.evaluation.completed_at)
    
    def test_evaluation_start(self):
        """Test de inicio de evaluación"""
        self.evaluation.status = 'in_progress'
        self.evaluation.started_at = timezone.now()
        self.evaluation.save()
        
        self.assertEqual(self.evaluation.status, 'in_progress')
        self.assertIsNotNone(self.evaluation.started_at)
    
    def test_calculate_score_with_correct_answers(self):
        """Test de cálculo de puntuación con respuestas correctas"""
        # Completar evaluación
        self.evaluation.status = 'completed'
        self.evaluation.completed_at = timezone.now()
        self.evaluation.save()
        
        # Crear respuestas correctas
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q1,
            selected_option='B',
            is_correct=True,
            points_earned=10.00
        )
        
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q2,
            selected_option='True',
            is_correct=True,
            points_earned=10.00
        )
        
        # Calcular puntuación
        score = self.evaluation.calculate_score()
        
        self.assertEqual(score, 100.00)
        self.assertTrue(self.evaluation.passed)
    
    def test_calculate_score_with_partial_correct(self):
        """Test de cálculo con respuestas parcialmente correctas"""
        self.evaluation.status = 'completed'
        self.evaluation.completed_at = timezone.now()
        self.evaluation.save()
        
        # Una correcta, una incorrecta
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q1,
            selected_option='B',
            is_correct=True,
            points_earned=10.00
        )
        
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q2,
            selected_option='False',
            is_correct=False,
            points_earned=0.00
        )
        
        score = self.evaluation.calculate_score()
        
        self.assertEqual(score, 50.00)
        self.assertFalse(self.evaluation.passed)  # Menos de 70%
    
    def test_progress_percentage(self):
        """Test del porcentaje de progreso"""
        # Sin respuestas
        self.assertEqual(self.evaluation.progress_percentage, 0)
        
        # Con una respuesta
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q1,
            answer_text='Mi respuesta'
        )
        
        self.assertEqual(self.evaluation.progress_percentage, 50.0)  # 1 de 2
        
        # Con dos respuestas
        EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.q2,
            answer_text='Otra respuesta'
        )
        
        self.assertEqual(self.evaluation.progress_percentage, 100.0)


class EvaluationAnswerModelTest(TestCase):
    """Tests para el modelo EvaluationAnswer"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        
        self.candidate = Candidate.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com'
        )
        
        self.template = EvaluationTemplate.objects.create(
            title='Test',
            category='technical',
            created_by=self.user
        )
        
        self.question = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Test question',
            question_type='multiple_choice',
            options=['A', 'B', 'C'],
            correct_answer='B',
            points=10.00
        )
        
        self.evaluation = CandidateEvaluation.objects.create(
            template=self.template,
            candidate=self.candidate,
            assigned_by=self.user
        )
    
    def test_check_correct_multiple_choice_answer(self):
        """Test de verificación de respuesta correcta de opción múltiple"""
        answer = EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.question,
            selected_option='B'
        )
        
        result = answer.check_answer()
        
        self.assertTrue(result)
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.points_earned, 10.00)
    
    def test_check_incorrect_multiple_choice_answer(self):
        """Test de verificación de respuesta incorrecta"""
        answer = EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=self.question,
            selected_option='A'
        )
        
        result = answer.check_answer()
        
        self.assertFalse(result)
        self.assertFalse(answer.is_correct)
        self.assertEqual(answer.points_earned, 0.00)
    
    def test_text_answer_not_auto_gradable(self):
        """Test que preguntas de texto no son auto-calificables"""
        text_question = EvaluationQuestion.objects.create(
            template=self.template,
            question_text='Explain this',
            question_type='long_text',
            points=10.00
        )
        
        answer = EvaluationAnswer.objects.create(
            evaluation=self.evaluation,
            question=text_question,
            answer_text='My explanation'
        )
        
        result = answer.check_answer()
        
        self.assertIsNone(result)
        self.assertIsNone(answer.is_correct)


# Tests de API (si quieres agregar tests de endpoints)
class EvaluationAPITest(TestCase):
    """Tests para los endpoints de la API de evaluaciones"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Aquí se configurarían los tests de la API
        pass
    
    # Agregar tests de endpoints cuando sea necesario