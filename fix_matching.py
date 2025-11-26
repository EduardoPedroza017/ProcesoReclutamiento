# fix_matching.py
from apps.candidates.models import CandidateProfile
from apps.ai_services.models import CandidateProfileMatching
from apps.ai_services.services import MatchingService

print('Calculando matchings...')

for app in CandidateProfile.objects.filter(profile_id=2):
    print(f'Procesando {app.candidate.full_name}...')
    
    candidate = app.candidate
    profile = app.profile
    
    candidate_data = {
        'nombre': candidate.full_name,
        'email': candidate.email,
        'ciudad': candidate.city or '',
        'estado': candidate.state or '',
        'puesto_actual': candidate.current_position or '',
        'empresa_actual': candidate.current_company or '',
        'años_experiencia': candidate.years_of_experience or 0,
        'nivel_educacion': candidate.education_level or '',
        'habilidades': [],
        'habilidades_blandas': [],
        'idiomas': []
    }
    
    profile_data = {
        'titulo': profile.position_title,
        'descripcion': profile.position_description or '',
        'ubicacion': {
            'ciudad': profile.location_city or '',
            'estado': profile.location_state or '',
            'remoto': profile.is_remote,
            'hibrido': profile.is_hybrid
        },
        'salario': {
            'minimo': float(profile.salary_min) if profile.salary_min else 0,
            'maximo': float(profile.salary_max) if profile.salary_max else 0,
        },
        'requisitos': {
            'nivel_educacion': profile.education_level or '',
            'años_experiencia': profile.years_experience or 0,
        },
        'habilidades_tecnicas': profile.technical_skills or [],
        'habilidades_blandas': profile.soft_skills or [],
        'idiomas': profile.languages or []
    }
    
    service = MatchingService()
    result = service.calculate_matching(candidate_data, profile_data)
    
    if result['success']:
        score = result['overall_score']
        
        matching, _ = CandidateProfileMatching.objects.update_or_create(
            candidate=candidate,
            profile=profile,
            defaults={
                'overall_score': score,
                'technical_skills_score': result.get('technical_skills_score', 0),
                'soft_skills_score': result.get('soft_skills_score', 0),
                'experience_score': result.get('experience_score', 0),
                'education_score': result.get('education_score', 0),
                'created_by_id': 1
            }
        )
        
        app.match_percentage = score
        app.save()
        
        print(f'  ✅ Match calculado: {score}%')
    else:
        print(f'  ❌ Error: {result.get("error")}')

print('\n✅ Proceso completado!')