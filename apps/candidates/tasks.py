"""
Tareas asíncronas de Celery para Candidatos
"""
from celery import shared_task, group
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
import time
import os

from .models import Candidate, CandidateDocument, CandidateProfile
from apps.profiles.models import Profile
from apps.ai_services.models import CVAnalysis, CandidateProfileMatching, AILog
from apps.ai_services.services import CVAnalyzerService, MatchingService
from apps.ai_services.tasks import analyze_cv_task, calculate_matching_task


@shared_task(bind=True, max_retries=3)
def process_single_cv_for_bulk_upload(
    self,
    cv_file_path: str,
    cv_filename: str,
    profile_id: int = None,
    created_by_id: int = None
):
    """
    Procesa un solo CV en el contexto de carga masiva
    
    Args:
        cv_file_path: Ruta del archivo CV guardado temporalmente
        cv_filename: Nombre original del archivo
        profile_id: ID del perfil al que asignar (opcional)
        created_by_id: ID del usuario que creó
        
    Returns:
        Dict con resultado del procesamiento
    """
    start_time = time.time()
    
    try:
        # 1. Extraer texto del CV
        service = CVAnalyzerService()
        extracted_text = service.extract_text_from_file(cv_file_path)
        
        if not extracted_text or len(extracted_text) < 50:
            return {
                'success': False,
                'filename': cv_filename,
                'error': 'No se pudo extraer texto suficiente del CV',
                'candidate_id': None
            }
        
        # 2. Analizar con IA
        analysis_result = service.analyze_cv(extracted_text)
        
        if not analysis_result['success']:
            return {
                'success': False,
                'filename': cv_filename,
                'error': analysis_result.get('error', 'Error en análisis de IA'),
                'candidate_id': None
            }
        
        parsed_data = analysis_result['parsed_data']
        
        # 3. Validar que tengamos al menos email o nombre
        email = parsed_data.get('datos_personales', {}).get('email', '').strip()
        nombre_completo = parsed_data.get('datos_personales', {}).get('nombre_completo', '').strip()
        
        if not email and not nombre_completo:
            return {
                'success': False,
                'filename': cv_filename,
                'error': 'No se pudo extraer email ni nombre del CV',
                'candidate_id': None
            }
        
        # 4. Extraer nombres (si tenemos nombre completo)
        first_name = ''
        last_name = ''
        
        if nombre_completo:
            partes = nombre_completo.split()
            if len(partes) >= 2:
                first_name = partes[0]
                last_name = ' '.join(partes[1:])
            elif len(partes) == 1:
                first_name = partes[0]
                last_name = ''
        
        # Si no hay nombre, usar el email como base
        if not first_name:
            first_name = email.split('@')[0] if email else cv_filename.replace('.pdf', '').replace('.docx', '')
        
        # 5. Verificar si ya existe el candidato (por email)
        candidate = None
        if email:
            candidate = Candidate.objects.filter(email=email).first()
        
        # 6. Crear o actualizar candidato
        with transaction.atomic():
            if candidate:
                # Actualizar candidato existente
                candidate_created = False
            else:
                # Crear nuevo candidato
                datos_personales = parsed_data.get('datos_personales', {})
                educacion = parsed_data.get('educacion', [])
                experiencia = parsed_data.get('experiencia_laboral', [])
                
                # Determinar nivel de educación
                education_level = ''
                if educacion and len(educacion) > 0:
                    education_level = educacion[0].get('nivel', '')
                
                # Obtener posición y empresa actual
                current_position = ''
                current_company = ''
                if experiencia and len(experiencia) > 0:
                    current_position = experiencia[0].get('puesto', '')
                    current_company = experiencia[0].get('empresa', '')
                
                # Crear candidato
                candidate = Candidate.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email if email else f"{first_name.lower()}.{last_name.lower()}@temp.com",
                    phone=datos_personales.get('telefono', ''),
                    city=datos_personales.get('ciudad', ''),
                    state=datos_personales.get('estado', ''),
                    current_position=current_position,
                    current_company=current_company,
                    years_of_experience=parsed_data.get('años_experiencia_total', 0),
                    education_level=education_level,
                    skills=parsed_data.get('habilidades_tecnicas', []),
                    languages=parsed_data.get('idiomas', []),
                    status=Candidate.STATUS_NEW,
                    created_by_id=created_by_id
                )
                candidate_created = True
            
            # 7. Guardar el CV como documento
            with open(cv_file_path, 'rb') as f:
                cv_content = f.read()
            
            document = CandidateDocument.objects.create(
                candidate=candidate,
                document_type=CandidateDocument.DOCUMENT_TYPE_CV,
                file=ContentFile(cv_content, name=cv_filename),
                original_filename=cv_filename,
                description=f'CV cargado masivamente - {cv_filename}',
                ai_extracted_text=extracted_text,
                ai_parsed_data=parsed_data,
                uploaded_by_id=created_by_id
            )
            
            # 8. Crear registro de CVAnalysis
            cv_analysis = CVAnalysis.objects.create(
                candidate=candidate,
                document_file=document.file,
                extracted_text=extracted_text,
                parsed_data=parsed_data,
                ai_summary=analysis_result.get('summary', ''),
                strengths=analysis_result.get('strengths', []),
                weaknesses=analysis_result.get('weaknesses', []),
                recommended_positions=analysis_result.get('recommended_positions', []),
                status=CVAnalysis.STATUS_COMPLETED,
                completed_at=timezone.now(),
                processing_time=time.time() - start_time,
                created_by_id=created_by_id
            )
            
            # 9. Si hay perfil, vincular candidato y calcular matching
            matching_score = None
            if profile_id:
                try:
                    profile = Profile.objects.get(pk=profile_id)
                    
                    # Crear relación candidato-perfil si no existe
                    candidate_profile, cp_created = CandidateProfile.objects.get_or_create(
                        candidate=candidate,
                        profile=profile,
                        defaults={
                            'status': CandidateProfile.STATUS_APPLIED,
                            'notes': f'Candidato agregado por carga masiva de CVs'
                        }
                    )
                    
                    # Calcular matching
                    matching_service = MatchingService()
                    
                    # Preparar datos del candidato
                    candidate_data = {
                        'nombre': candidate.full_name,
                        'email': candidate.email,
                        'ciudad': candidate.city,
                        'estado': candidate.state,
                        'puesto_actual': candidate.current_position,
                        'empresa_actual': candidate.current_company,
                        'años_experiencia': candidate.years_of_experience,
                        'nivel_educacion': candidate.education_level,
                        'habilidades': parsed_data.get('habilidades_tecnicas', []),
                        'habilidades_blandas': parsed_data.get('habilidades_blandas', []),
                        'idiomas': parsed_data.get('idiomas', []),
                    }
                    
                    # Preparar datos del perfil
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
                            'minimo': float(profile.salary_min) if profile.salary_min else 0,
                            'maximo': float(profile.salary_max) if profile.salary_max else 0,
                        },
                        'requisitos': {
                            'nivel_educacion': profile.education_level,
                            'años_experiencia': profile.years_experience,
                        },
                        'habilidades_tecnicas': profile.technical_skills or [],
                        'habilidades_blandas': profile.soft_skills or [],
                        'idiomas': profile.languages or []
                    }
                    
                    # Calcular matching
                    matching_result = matching_service.calculate_matching(candidate_data, profile_data)
                    
                    if matching_result['success']:
                        # Crear o actualizar matching
                        matching, _ = CandidateProfileMatching.objects.update_or_create(
                            candidate=candidate,
                            profile=profile,
                            defaults={
                                'overall_score': matching_result.get('overall_score', 0),
                                'technical_skills_score': matching_result.get('technical_skills_score', 0),
                                'soft_skills_score': matching_result.get('soft_skills_score', 0),
                                'experience_score': matching_result.get('experience_score', 0),
                                'education_score': matching_result.get('education_score', 0),
                                'location_score': matching_result.get('location_score', 0),
                                'salary_score': matching_result.get('salary_score', 0),
                                'matching_analysis': matching_result.get('matching_analysis', ''),
                                'strengths': matching_result.get('strengths', []),
                                'gaps': matching_result.get('gaps', []),
                                'recommendations': matching_result.get('recommendations', ''),
                                'created_by_id': created_by_id
                            }
                        )
                        matching_score = matching.overall_score
                        
                        # Actualizar porcentaje de match en CandidateProfile
                        candidate_profile.match_percentage = matching_score
                        candidate_profile.save()
                    
                except Profile.DoesNotExist:
                    pass  # Perfil no existe, continuar sin matching
            
            # 10. Registrar en log de IA
            AILog.objects.create(
                action=AILog.ACTION_CV_ANALYSIS,
                prompt=f"Análisis masivo de CV: {cv_filename}",
                response=analysis_result.get('summary', '')[:500],
                model_used='claude-3-sonnet-20240229',
                tokens_input=analysis_result.get('tokens_input', 0),
                tokens_output=analysis_result.get('tokens_output', 0),
                execution_time=time.time() - start_time,
                success=True,
                candidate=candidate,
                profile_id=profile_id,
                created_by_id=created_by_id
            )
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(cv_file_path):
                os.remove(cv_file_path)
        except:
            pass
        
        return {
            'success': True,
            'filename': cv_filename,
            'candidate_id': candidate.id,
            'candidate_name': candidate.full_name,
            'candidate_email': candidate.email,
            'created': candidate_created,
            'matching_score': matching_score,
            'processing_time': time.time() - start_time
        }
        
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            if os.path.exists(cv_file_path):
                os.remove(cv_file_path)
        except:
            pass
        
        # Reintentar si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        return {
            'success': False,
            'filename': cv_filename,
            'error': str(e),
            'candidate_id': None
        }


@shared_task
def bulk_upload_cvs_task(
    cv_files_data: list,
    profile_id: int = None,
    created_by_id: int = None
):
    """
    Tarea principal para procesar múltiples CVs secuencialmente
    
    Args:
        cv_files_data: Lista de dicts con {'path': ..., 'filename': ...}
        profile_id: ID del perfil opcional
        created_by_id: ID del usuario
        
    Returns:
        Dict con resumen de resultados
    """
    start_time = time.time()
    results = []
    
    # Procesar cada CV secuencialmente (sin crear subtareas)
    for cv_data in cv_files_data:
        try:
            # Llamar la función directamente SIN el decorador de tarea
            result = _process_single_cv_sync(
                cv_data['path'],
                cv_data['filename'],
                profile_id,
                created_by_id
            )
            results.append(result)
        except Exception as e:
            results.append({
                'success': False,
                'filename': cv_data['filename'],
                'error': str(e),
                'candidate_id': None
            })
    
    # Procesar resultados
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    created_candidates = [r for r in successful if r.get('created', False)]
    updated_candidates = [r for r in successful if not r.get('created', False)]
    
    return {
        'total_processed': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'created': len(created_candidates),
        'updated': len(updated_candidates),
        'successful_details': successful,
        'failed_details': failed,
        'total_time': time.time() - start_time
    }


def _process_single_cv_sync(
    cv_file_path: str,
    cv_filename: str,
    profile_id: int = None,
    created_by_id: int = None
):
    """
    Procesa un solo CV de forma síncrona (función auxiliar, no es tarea Celery)
    
    Esta función contiene la misma lógica que process_single_cv_for_bulk_upload
    pero sin el decorador @shared_task para evitar el error de .get()
    """
    start_time = time.time()
    
    try:
        from apps.ai_services.services import CVAnalyzerService, MatchingService
        from apps.profiles.models import Profile
        from .models import Candidate, CandidateDocument, CandidateProfile
        
        # 1. Extraer texto del CV
        service = CVAnalyzerService()
        extracted_text = service.extract_text_from_file(cv_file_path)
        
        if not extracted_text or len(extracted_text) < 50:
            return {
                'success': False,
                'filename': cv_filename,
                'error': 'No se pudo extraer texto suficiente del CV',
                'candidate_id': None
            }
        
        # 2. Analizar con IA
        analysis_result = service.analyze_cv(extracted_text)
        
        if not analysis_result['success']:
            return {
                'success': False,
                'filename': cv_filename,
                'error': analysis_result.get('error', 'Error en análisis de IA'),
                'candidate_id': None
            }
        
        parsed_data = analysis_result['parsed_data']
        
        # 3. Validar que tengamos al menos email o nombre
        email = parsed_data.get('datos_personales', {}).get('email', '').strip()
        nombre_completo = parsed_data.get('datos_personales', {}).get('nombre_completo', '').strip()
        
        if not email and not nombre_completo:
            return {
                'success': False,
                'filename': cv_filename,
                'error': 'No se pudo extraer email ni nombre del CV',
                'candidate_id': None
            }
        
        # 4. Buscar o crear candidato
        candidate = None
        created = False
        
        if email:
            candidate = Candidate.objects.filter(email__iexact=email).first()
        
        if not candidate and nombre_completo:
            # Intentar buscar por nombre
            nombres = nombre_completo.split()
            if len(nombres) >= 2:
                candidate = Candidate.objects.filter(
                    first_name__iexact=nombres[0],
                    last_name__icontains=nombres[-1]
                ).first()
        
        # Obtener datos personales
        datos = parsed_data.get('datos_personales', {})
        
        if not candidate:
            # Crear nuevo candidato
            nombres = nombre_completo.split() if nombre_completo else ['Sin', 'Nombre']
            first_name = nombres[0] if nombres else 'Sin'
            last_name = ' '.join(nombres[1:]) if len(nombres) > 1 else 'Nombre'
            
            candidate = Candidate.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email or f"sin_email_{timezone.now().timestamp()}@temporal.com",
                phone=datos.get('telefono', ''),
                city=datos.get('ciudad', ''),
                state=datos.get('estado', ''),
                country=datos.get('pais', 'México'),
                created_by_id=created_by_id
            )
            created = True
        
        # 5. Actualizar datos del candidato
        if datos.get('telefono') and not candidate.phone:
            candidate.phone = datos.get('telefono')
        if datos.get('ciudad') and not candidate.city:
            candidate.city = datos.get('ciudad')
        if datos.get('linkedin'):
            candidate.linkedin_url = datos.get('linkedin')
        
        # Experiencia
        experiencia = parsed_data.get('experiencia_laboral', [])
        if experiencia:
            ultima = experiencia[0]
            candidate.current_position = ultima.get('puesto', '')
            candidate.current_company = ultima.get('empresa', '')
            
            # Calcular años de experiencia
            total_exp = 0
            for exp in experiencia:
                duracion = exp.get('duracion', '')
                if 'año' in duracion.lower():
                    try:
                        anos = int(''.join(filter(str.isdigit, duracion.split('año')[0])))
                        total_exp += anos
                    except:
                        pass
            if total_exp > 0:
                candidate.years_of_experience = total_exp
        
        # Educación
        educacion = parsed_data.get('educacion', [])
        if educacion:
            niveles = {
                'doctorado': 'doctorate',
                'maestría': 'masters',
                'licenciatura': 'bachelors',
                'ingeniería': 'bachelors',
                'técnico': 'technical',
                'preparatoria': 'high_school',
                'bachillerato': 'high_school',
            }
            for edu in educacion:
                titulo = edu.get('titulo', '').lower()
                for key, value in niveles.items():
                    if key in titulo:
                        candidate.education_level = value
                        break
        
        # Habilidades
        habilidades = parsed_data.get('habilidades', {})
        if habilidades:
            candidate.technical_skills = habilidades.get('tecnicas', [])
            candidate.soft_skills = habilidades.get('blandas', [])
            candidate.languages = habilidades.get('idiomas', [])
        
        # Guardar perfil IA
        candidate.ai_parsed_profile = parsed_data
        candidate.save()
        
        # 6. Guardar el CV como documento
        with open(cv_file_path, 'rb') as f:
            from django.core.files.base import ContentFile
            content = f.read()
            
            doc = CandidateDocument.objects.create(
                candidate=candidate,
                document_type='cv',
                uploaded_by_id=created_by_id
            )
            doc.file.save(cv_filename, ContentFile(content))
        
        # 7. Calcular matching si hay perfil
        matching_score = None
        if profile_id:
            try:
                profile = Profile.objects.get(pk=profile_id)
                
                # Crear relación candidato-perfil
                cp, _ = CandidateProfile.objects.get_or_create(
                    candidate=candidate,
                    profile=profile,
                    defaults={
                        'status': 'applied',
                        'applied_date': timezone.now()
                    }
                )
                
                # Calcular matching con IA
                matching_service = MatchingService()
                matching_result = matching_service.calculate_matching(candidate.id, profile_id)
                
                if matching_result.get('success'):
                    matching_score = matching_result.get('overall_score', 0)
                    cp.matching_score = matching_score
                    cp.save()
            except Exception as e:
                print(f"⚠️ Error calculando matching: {e}")
        
        # 8. Limpiar archivo temporal
        try:
            if os.path.exists(cv_file_path):
                os.remove(cv_file_path)
        except:
            pass
        
        return {
            'success': True,
            'filename': cv_filename,
            'candidate_id': candidate.id,
            'candidate_name': candidate.full_name,
            'candidate_email': candidate.email,
            'created': created,
            'matching_score': matching_score,
            'processing_time': time.time() - start_time
        }
        
    except Exception as e:
        # Limpiar archivo temporal en caso de error
        try:
            if os.path.exists(cv_file_path):
                os.remove(cv_file_path)
        except:
            pass
        
        return {
            'success': False,
            'filename': cv_filename,
            'error': str(e),
            'candidate_id': None
        }