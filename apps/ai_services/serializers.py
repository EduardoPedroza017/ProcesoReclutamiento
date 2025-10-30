"""
Serializers para Servicios de IA
"""
from rest_framework import serializers
from .models import CVAnalysis, CandidateProfileMatching, ProfileGeneration, AILog


class CVAnalysisSerializer(serializers.ModelSerializer):
    """Serializer para análisis de CVs"""
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CVAnalysis
        fields = [
            'id',
            'candidate',
            'candidate_name',
            'document_file',
            'extracted_text',
            'parsed_data',
            'ai_summary',
            'strengths',
            'weaknesses',
            'recommended_positions',
            'status',
            'status_display',
            'error_message',
            'created_by',
            'created_by_name',
            'created_at',
            'completed_at',
            'processing_time',
        ]
        read_only_fields = [
            'extracted_text',
            'parsed_data',
            'ai_summary',
            'strengths',
            'weaknesses',
            'recommended_positions',
            'status',
            'error_message',
            'created_by',
            'created_at',
            'completed_at',
            'processing_time',
        ]


class CVAnalysisCreateSerializer(serializers.Serializer):
    """Serializer para crear análisis de CV"""
    candidate_id = serializers.IntegerField(required=True)
    document_file = serializers.FileField(required=True)
    
    def validate_document_file(self, value):
        """Valida el tipo de archivo"""
        allowed_extensions = ['.pdf', '.docx']
        file_extension = value.name.lower()[value.name.rfind('.'):]
        
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Formato de archivo no soportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Validar tamaño (máximo 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "El archivo es demasiado grande. Tamaño máximo: 10MB"
            )
        
        return value


class CandidateProfileMatchingSerializer(serializers.ModelSerializer):
    """Serializer para matching candidato-perfil"""
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    profile_title = serializers.CharField(source='profile.position_title', read_only=True)
    profile_client = serializers.CharField(source='profile.client.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_good_match = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CandidateProfileMatching
        fields = [
            'id',
            'candidate',
            'candidate_name',
            'profile',
            'profile_title',
            'profile_client',
            'overall_score',
            'technical_skills_score',
            'soft_skills_score',
            'experience_score',
            'education_score',
            'location_score',
            'salary_score',
            'matching_analysis',
            'strengths',
            'gaps',
            'recommendations',
            'is_good_match',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = [
            'overall_score',
            'technical_skills_score',
            'soft_skills_score',
            'experience_score',
            'education_score',
            'location_score',
            'salary_score',
            'matching_analysis',
            'strengths',
            'gaps',
            'recommendations',
            'created_by',
            'created_at',
        ]


class MatchingRequestSerializer(serializers.Serializer):
    """Serializer para solicitar matching"""
    candidate_id = serializers.IntegerField(required=True)
    profile_id = serializers.IntegerField(required=True)


class ProfileGenerationSerializer(serializers.ModelSerializer):
    """Serializer para generación de perfiles"""
    profile_title = serializers.CharField(source='profile.position_title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ProfileGeneration
        fields = [
            'id',
            'profile',
            'profile_title',
            'meeting_transcription',
            'additional_notes',
            'generated_profile_data',
            'status',
            'status_display',
            'error_message',
            'created_by',
            'created_by_name',
            'created_at',
            'completed_at',
            'processing_time',
        ]
        read_only_fields = [
            'generated_profile_data',
            'status',
            'error_message',
            'created_by',
            'created_at',
            'completed_at',
            'processing_time',
        ]


class ProfileGenerationCreateSerializer(serializers.Serializer):
    """Serializer para crear generación de perfil"""
    meeting_transcription = serializers.CharField(required=True)
    client_name = serializers.CharField(required=False, allow_blank=True)
    additional_notes = serializers.CharField(required=False, allow_blank=True)
    create_profile = serializers.BooleanField(default=False)
    
    def validate_meeting_transcription(self, value):
        """Valida que la transcripción no esté vacía"""
        if len(value.strip()) < 100:
            raise serializers.ValidationError(
                "La transcripción es demasiado corta. Debe tener al menos 100 caracteres."
            )
        return value


class AILogSerializer(serializers.ModelSerializer):
    """Serializer para logs de IA"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    profile_title = serializers.CharField(source='profile.position_title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    total_tokens = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AILog
        fields = [
            'id',
            'action',
            'action_display',
            'prompt',
            'response',
            'model_used',
            'tokens_input',
            'tokens_output',
            'total_tokens',
            'execution_time',
            'success',
            'error_message',
            'candidate',
            'candidate_name',
            'profile',
            'profile_title',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = fields


class SummarizeRequestSerializer(serializers.Serializer):
    """Serializer para solicitar resumen de candidato"""
    candidate_id = serializers.IntegerField(required=True)


class BulkMatchingRequestSerializer(serializers.Serializer):
    """Serializer para matching masivo"""
    profile_id = serializers.IntegerField(required=True)
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1,
        max_length=50
    )


class AIStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de IA"""
    total_cv_analyses = serializers.IntegerField()
    total_matchings = serializers.IntegerField()
    total_profile_generations = serializers.IntegerField()
    total_api_calls = serializers.IntegerField()
    total_tokens_used = serializers.IntegerField()
    average_execution_time = serializers.FloatField()
    success_rate = serializers.FloatField()
    analyses_by_status = serializers.DictField()
    matchings_by_score = serializers.DictField()
    recent_activity = serializers.ListField()