"""
Tareas asíncronas de Celery para Servicios de IA
"""
from celery import shared_task
from django.utils import timezone
import time

from .models import CVAnalysis, CandidateProfileMatching, ProfileGeneration, AILog
from .services import CVAnalyzerService, MatchingService, ProfileGenerationService
from apps.candidates.models import Candidate
from apps.profiles.models import Profile


@shared_task(bind=True, max_retries=3)
def analyze_cv_task(self, analysis_id):
    """
    Tarea asíncrona para analizar un CV
    
    Args:
        analysis_id: ID del análisis de CV
    """
    try:
        analysis = CVAnalysis.objects.get(pk=analysis_id)
    except CVAnalysis.DoesNotExist:
        return {'error': 'Análisis no encontrado'}
    
    # Marcar como procesando
    analysis.status = CVAnalysis.STATUS_PROCESSING
    analysis.save()
    
    start_time = time.time()
    
    try:
        # Inicializar servicio
        service = CVAnalyzerService()
        
        # Extraer texto del archivo
        file_path = analysis.document_file.path
        extracted_text = service.extract_text_from_file(file_path)
        
        # Guardar texto extraído
        analysis.extracted_text = extracted_text
        analysis.save()
        
        # Analizar con IA
        result = service.analyze_cv(extracted_text)
        
        if result['success']:
            # Actualizar análisis con los resultados
            analysis.parsed_data = result['parsed_data']
            analysis.ai_summary = result['summary']
            analysis.strengths = result['strengths']
            analysis.weaknesses = result['weaknesses']
            analysis.recommended_positions = result['recommended_positions']
            analysis.status = CVAnalysis.STATUS_COMPLETED
            analysis.completed_at = timezone.now()
            analysis.processing_time = time.time() - start_time
            analysis.save()
            
            # Actualizar candidato con información parseada
            candidate = analysis.candidate
            parsed_data = result['parsed_data']
            
            if parsed_data:
                # Actualizar datos básicos si no existen
                datos_personales = parsed_data.get('datos_personales', {})
                if not candidate.phone and datos_personales.get('telefono'):
                    candidate.phone = datos_personales.get('telefono')
                if not candidate.city and datos_personales.get('ciudad'):
                    candidate.city = datos_personales.get('ciudad')
                if not candidate.state and datos_personales.get('estado'):
                    candidate.state = datos_personales.get('estado')
                
                # Actualizar experiencia y educación
                if parsed_data.get('años_experiencia_total'):
                    candidate.years_of_experience = parsed_data.get('años_experiencia_total')
                
                educacion = parsed_data.get('educacion', [])
                if educacion:
                    candidate.education_level = educacion[0].get('nivel', '')
                    candidate.university = educacion[0].get('institucion', '')
                    candidate.degree = educacion[0].get('carrera', '')
                
                # Actualizar habilidades
                if parsed_data.get('habilidades_tecnicas'):
                    candidate.skills = parsed_data.get('habilidades_tecnicas')
                if parsed_data.get('idiomas'):
                    candidate.languages = parsed_data.get('idiomas')
                if parsed_data.get('certificaciones'):
                    candidate.certifications = parsed_data.get('certificaciones')
                
                # Guardar resumen de IA
                candidate.ai_summary = result['summary']
                
                candidate.save()
            
            # Registrar en log
            AILog.objects.create(
                action=AILog.ACTION_CV_ANALYSIS,
                prompt=f"Analizar CV de {analysis.candidate.full_name}",
                response=result['summary'],
                tokens_input=result['tokens_input'],
                tokens_output=result['tokens_output'],
                execution_time=result['execution_time'],
                success=True,
                candidate=analysis.candidate,
                created_by=analysis.created_by
            )
            
            return {
                'status': 'completed',
                'analysis_id': analysis.id,
                'summary': result['summary']
            }
        else:
            # Error en el análisis de IA
            analysis.status = CVAnalysis.STATUS_FAILED
            analysis.error_message = result['error']
            analysis.processing_time = time.time() - start_time
            analysis.save()
            
            # Registrar error en log
            AILog.objects.create(
                action=AILog.ACTION_CV_ANALYSIS,
                prompt=f"Analizar CV de {analysis.candidate.full_name}",
                response='',
                success=False,
                error_message=result['error'],
                candidate=analysis.candidate,
                created_by=analysis.created_by
            )
            
            return {
                'status': 'failed',
                'analysis_id': analysis.id,
                'error': result['error']
            }
            
    except Exception as e:
        # Error general
        analysis.status = CVAnalysis.STATUS_FAILED
        analysis.error_message = str(e)
        analysis.processing_time = time.time() - start_time
        analysis.save()
        
        # Reintentar si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'analysis_id': analysis.id,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def calculate_matching_task(self, matching_id):
    """
    Tarea asíncrona para calcular matching candidato-perfil
    
    Args:
        matching_id: ID del matching
    """
    try:
        matching = CandidateProfileMatching.objects.get(pk=matching_id)
    except CandidateProfileMatching.DoesNotExist:
        return {'error': 'Matching no encontrado'}
    
    try:
        # Preparar datos del candidato
        candidate = matching.candidate
        candidate_data = {
            'nombre': candidate.full_name,
            'email': candidate.email,
            'ciudad': candidate.city,
            'estado': candidate.state,
            'puesto_actual': candidate.current_position,
            'empresa_actual': candidate.current_company,
            'años_experiencia': candidate.years_of_experience,
            'nivel_educacion': candidate.education_level,
            'universidad': candidate.university,
            'carrera': candidate.degree,
            'habilidades': candidate.skills,
            'habilidades_blandas': [],
            'idiomas': candidate.languages,
            'expectativa_salarial': {
                'minimo': float(candidate.salary_expectation_min) if candidate.salary_expectation_min else 0,
                'maximo': float(candidate.salary_expectation_max) if candidate.salary_expectation_max else 0,
                'moneda': candidate.salary_currency
            }
        }
        
        # Preparar datos del perfil
        profile = matching.profile
        profile_data = {
            'titulo': profile.position_title,
            'descripcion': profile.position_description,
            'ubicacion': {
                'ciudad': profile.location_city,
                'estado': profile.location_state,
                'remoto': profile.is_remote,
                'hibrido': profile.is_hybrid
            },
            'salario': {
                'minimo': float(profile.salary_min),
                'maximo': float(profile.salary_max),
                'moneda': profile.salary_currency,
                'periodo': profile.salary_period
            },
            'requisitos': {
                'nivel_educacion': profile.education_level,
                'años_experiencia': profile.years_experience,
                'edad_minima': profile.age_min,
                'edad_maxima': profile.age_max
            },
            'habilidades_tecnicas': profile.technical_skills,
            'habilidades_blandas': profile.soft_skills,
            'idiomas': profile.languages
        }
        
        # Calcular matching con IA
        service = MatchingService()
        result = service.calculate_matching(candidate_data, profile_data)
        
        if result['success']:
            # Actualizar matching con los resultados
            matching.overall_score = result['overall_score']
            matching.technical_skills_score = result['technical_skills_score']
            matching.soft_skills_score = result['soft_skills_score']
            matching.experience_score = result['experience_score']
            matching.education_score = result['education_score']
            matching.location_score = result['location_score']
            matching.salary_score = result['salary_score']
            matching.matching_analysis = result['matching_analysis']
            matching.strengths = result['strengths']
            matching.gaps = result['gaps']
            matching.recommendations = result['recommendations']
            matching.save()
            
            # Actualizar puntuación en el candidato
            candidate.ai_match_score = result['overall_score']
            candidate.save()
            
            # Registrar en log
            AILog.objects.create(
                action=AILog.ACTION_MATCHING,
                prompt=f"Matching: {candidate.full_name} → {profile.position_title}",
                response=result['matching_analysis'],
                tokens_input=result['tokens_input'],
                tokens_output=result['tokens_output'],
                execution_time=result['execution_time'],
                success=True,
                candidate=candidate,
                profile=profile,
                created_by=matching.created_by
            )
            
            return {
                'status': 'completed',
                'matching_id': matching.id,
                'overall_score': result['overall_score']
            }
        else:
            # Error en el matching
            AILog.objects.create(
                action=AILog.ACTION_MATCHING,
                prompt=f"Matching: {candidate.full_name} → {profile.position_title}",
                response='',
                success=False,
                error_message=result['error'],
                candidate=candidate,
                profile=profile,
                created_by=matching.created_by
            )
            
            return {
                'status': 'failed',
                'matching_id': matching.id,
                'error': result['error']
            }
            
    except Exception as e:
        # Reintentar si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'matching_id': matching.id,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3)
def generate_profile_task(self, generation_id, client_name='', create_profile=False):
    """
    Tarea asíncrona para generar perfil desde transcripción
    
    Args:
        generation_id: ID de la generación
        client_name: Nombre del cliente
        create_profile: Si se debe crear el perfil automáticamente
    """
    try:
        generation = ProfileGeneration.objects.get(pk=generation_id)
    except ProfileGeneration.DoesNotExist:
        return {'error': 'Generación no encontrada'}
    
    # Marcar como procesando
    generation.status = ProfileGeneration.STATUS_PROCESSING
    generation.save()
    
    start_time = time.time()
    
    try:
        # Generar perfil con IA
        service = ProfileGenerationService()
        result = service.generate_profile_from_transcription(
            transcription=generation.meeting_transcription,
            client_name=client_name,
            additional_notes=generation.additional_notes
        )
        
        if result['success']:
            # Actualizar generación con los resultados
            generation.generated_profile_data = result['profile_data']
            generation.status = ProfileGeneration.STATUS_COMPLETED
            generation.completed_at = timezone.now()
            generation.processing_time = time.time() - start_time
            generation.save()
            
            # Si se solicita, crear el perfil automáticamente
            if create_profile and result['profile_data']:
                profile_data = result['profile_data']
                
                # Aquí se crearía el perfil real
                # TODO: Implementar creación automática de perfil
                # Esto requeriría obtener el cliente, etc.
                pass
            
            # Registrar en log
            AILog.objects.create(
                action=AILog.ACTION_PROFILE_GENERATION,
                prompt=f"Generar perfil para {client_name}",
                response=str(result['profile_data']),
                tokens_input=result['tokens_input'],
                tokens_output=result['tokens_output'],
                execution_time=result['execution_time'],
                success=True,
                created_by=generation.created_by
            )
            
            return {
                'status': 'completed',
                'generation_id': generation.id,
                'profile_data': result['profile_data']
            }
        else:
            # Error en la generación
            generation.status = ProfileGeneration.STATUS_FAILED
            generation.error_message = result['error']
            generation.processing_time = time.time() - start_time
            generation.save()
            
            # Registrar error en log
            AILog.objects.create(
                action=AILog.ACTION_PROFILE_GENERATION,
                prompt=f"Generar perfil para {client_name}",
                response='',
                success=False,
                error_message=result['error'],
                created_by=generation.created_by
            )
            
            return {
                'status': 'failed',
                'generation_id': generation.id,
                'error': result['error']
            }
            
    except Exception as e:
        # Error general
        generation.status = ProfileGeneration.STATUS_FAILED
        generation.error_message = str(e)
        generation.processing_time = time.time() - start_time
        generation.save()
        
        # Reintentar si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'status': 'failed',
            'generation_id': generation.id,
            'error': str(e)
        }