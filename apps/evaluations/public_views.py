"""
Vistas públicas para evaluaciones (sin autenticación)
"""

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    EvaluationTemplate,
    EvaluationQuestion,
    CandidateEvaluation,
    EvaluationAnswer
)


class PublicEvaluationView(APIView):
    """Vista pública para obtener una evaluación por token"""
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        template = get_object_or_404(EvaluationTemplate, share_token=token, is_active=True)
        questions = EvaluationQuestion.objects.filter(template=template).order_by('order')
        
        template_data = {
            'id': template.id,
            'title': template.title,
            'description': template.description,
            'category': template.category,
            'duration_minutes': template.duration_minutes,
            'passing_score': template.passing_score,
        }
        
        questions_data = [{
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'options': q.options,
            'points': q.points,
            'order': q.order,
            'is_required': q.is_required,
            'help_text': q.help_text,
        } for q in questions]
        
        return Response({'template': template_data, 'questions': questions_data})


class PublicEvaluationSubmitView(APIView):
    """Vista pública para enviar respuestas"""
    permission_classes = [AllowAny]
    
    def post(self, request, token):
        from apps.candidates.models import Candidate
        
        template = get_object_or_404(EvaluationTemplate, share_token=token, is_active=True)
        candidate_info = request.data.get('candidate_info', {})
        answers = request.data.get('answers', [])
        
        candidate, created = Candidate.objects.get_or_create(
            email=candidate_info.get('email'),
            defaults={
                'first_name': candidate_info.get('name', '').split()[0] if candidate_info.get('name') else 'Anónimo',
                'last_name': ' '.join(candidate_info.get('name', '').split()[1:]) if candidate_info.get('name') else '',
                'phone': candidate_info.get('phone', ''),
                'source': 'evaluacion_publica',
            }
        )
        
        evaluation = CandidateEvaluation.objects.create(
            template=template,
            candidate=candidate,
            status='completed',
            started_at=timezone.now(),
            completed_at=timezone.now()
        )
        
        total_points = 0
        earned_points = 0
        
        for answer_data in answers:
            question = EvaluationQuestion.objects.get(id=answer_data['question_id'])
            is_correct = False
            points_earned = 0
            
            if question.correct_answer and answer_data.get('answer_text'):
                is_correct = question.correct_answer.strip().lower() == answer_data['answer_text'].strip().lower()
                if is_correct:
                    points_earned = question.points
            
            EvaluationAnswer.objects.create(
                evaluation=evaluation,
                question=question,
                answer_text=answer_data.get('answer_text', ''),
                selected_option=answer_data.get('answer_text', ''),
                is_correct=is_correct,
                points_earned=points_earned
            )
            
            total_points += question.points
            earned_points += points_earned
        
        if total_points > 0:
            final_score = (earned_points / total_points) * 100
            evaluation.final_score = round(final_score, 2)
            evaluation.passed = final_score >= float(template.passing_score)
            evaluation.save()
        
        return Response({
            'success': True,
            'evaluation_id': evaluation.id,
            'final_score': evaluation.final_score,
            'passed': evaluation.passed,
            'message': '¡Evaluación enviada exitosamente!'
        }, status=status.HTTP_201_CREATED)
