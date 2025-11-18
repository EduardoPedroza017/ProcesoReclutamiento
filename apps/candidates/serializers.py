"""
Serializers para Candidatos
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Candidate,
    CandidateProfile,
    CandidateDocument,
    CandidateStatusHistory,
    CandidateNote,
)
from apps.profiles.models import Profile


class CandidateDocumentSerializer(serializers.ModelSerializer):
    """Serializer para documentos de candidatos"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CandidateDocument
        fields = [
            'id',
            'candidate',
            'document_type',
            'file',
            'file_url',
            'original_filename',
            'description',
            'ai_extracted_text',
            'ai_parsed_data',
            'uploaded_by',
            'uploaded_by_name',
            'uploaded_at',
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'original_filename']
    
    def get_file_url(self, obj):
        """Retorna la URL completa del archivo"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class CandidateNoteSerializer(serializers.ModelSerializer):
    """Serializer para notas de candidatos"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = CandidateNote
        fields = [
            'id',
            'candidate',
            'note',
            'is_important',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class CandidateStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer para historial de estados"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = CandidateStatusHistory
        fields = [
            'id',
            'from_status',
            'from_status_display',
            'to_status',
            'to_status_display',
            'changed_by',
            'changed_by_name',
            'notes',
            'timestamp',
        ]
        read_only_fields = ['changed_by', 'timestamp']


class CandidateProfileSerializer(serializers.ModelSerializer):
    """Serializer para aplicaciones de candidatos a perfiles"""
    profile_title = serializers.CharField(source='profile.position_title', read_only=True)
    profile_client = serializers.CharField(source='profile.client.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CandidateProfile
        fields = [
            'id',
            'candidate',
            'profile',
            'profile_title',
            'profile_client',
            'status',
            'status_display',
            'match_percentage',
            'overall_rating',
            'notes',
            'rejection_reason',
            'applied_at',
            'interview_date',
            'offer_date',
        ]
        read_only_fields = ['applied_at']


class CandidateListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de candidatos"""
    full_name = serializers.CharField(read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_applications = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'full_name',
            'first_name',
            'last_name',
            'email',
            'phone',
            'city',
            'state',
            'status',
            'status_display',
            'current_position',
            'current_company',
            'years_of_experience',
            'assigned_to',
            'assigned_to_name',
            'active_applications',
            'created_at',
        ]


class CandidateDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de candidato"""
    full_name = serializers.CharField(read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    salary_expectation_range = serializers.CharField(read_only=True)
    active_applications = serializers.IntegerField(read_only=True)
    
    # Relaciones
    documents = CandidateDocumentSerializer(many=True, read_only=True)
    candidate_profiles = CandidateProfileSerializer(many=True, read_only=True)
    status_history = CandidateStatusHistorySerializer(many=True, read_only=True)
    notes = CandidateNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Candidate
        fields = '__all__'
        read_only_fields = [
            'created_by',
            'created_at',
            'updated_at',
        ]


class CandidateCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar candidatos"""
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'alternative_phone',
            'city',
            'state',
            'country',
            'address',
            'current_position',
            'current_company',
            'years_of_experience',
            'education_level',
            'university',
            'degree',
            'skills',
            'languages',
            'certifications',
            'salary_expectation_min',
            'salary_expectation_max',
            'salary_currency',
            'status',
            'assigned_to',
            'source',
            'internal_notes',
            'available_from',
            'notice_period_days',
            'linkedin_url',
            'portfolio_url',
            'github_url',
        ]
    
    def validate_email(self, value):
        """Valida que el email sea único"""
        # Si estamos actualizando, excluir el candidato actual
        instance = getattr(self, 'instance', None)
        queryset = Candidate.objects.filter(email=value)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un candidato con este correo electrónico")
        
        return value
    
    def validate_years_of_experience(self, value):
        """Valida años de experiencia"""
        if value < 0:
            raise serializers.ValidationError("Los años de experiencia no pueden ser negativos")
        if value > 60:
            raise serializers.ValidationError("Los años de experiencia parecen incorrectos")
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        # Validar expectativas salariales
        salary_min = data.get('salary_expectation_min')
        salary_max = data.get('salary_expectation_max')
        
        if salary_min and salary_max and salary_max < salary_min:
            raise serializers.ValidationError({
                'salary_expectation_max': 'La expectativa máxima debe ser mayor o igual a la mínima'
            })
        
        # Validar días de preaviso
        notice_period = data.get('notice_period_days')
        if notice_period is not None and notice_period < 0:
            raise serializers.ValidationError({
                'notice_period_days': 'Los días de preaviso no pueden ser negativos'
            })
        
        return data
    
    def create(self, validated_data):
        """Crea un candidato y registra el usuario creador"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualiza un candidato y registra cambios de estado"""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Si cambió el estado, registrar en el historial
        if old_status != new_status:
            request = self.context.get('request')
            CandidateStatusHistory.objects.create(
                candidate=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user if request else None,
                notes=validated_data.get('internal_notes', '')
            )
        
        return super().update(instance, validated_data)


class CandidateStatusChangeSerializer(serializers.Serializer):
    """Serializer para cambiar el estado de un candidato"""
    status = serializers.ChoiceField(choices=Candidate.STATUS_CHOICES, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class CandidateAssignSerializer(serializers.Serializer):
    """Serializer para asignar candidato a un perfil"""
    profile_id = serializers.IntegerField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_profile_id(self, value):
        """Valida que el perfil exista"""
        try:
            Profile.objects.get(pk=value)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("El perfil no existe")
        return value


class CandidateStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de candidatos"""
    total_candidates = serializers.IntegerField()
    by_status = serializers.DictField()
    by_experience = serializers.DictField()
    active_applications = serializers.IntegerField()
    new_this_month = serializers.IntegerField()
    hired_this_month = serializers.IntegerField()


class CandidateMatchSerializer(serializers.Serializer):
    """Serializer para matching de candidato con perfil"""
    profile_id = serializers.IntegerField(required=True)
    
    def validate_profile_id(self, value):
        """Valida que el perfil exista"""
        try:
            Profile.objects.get(pk=value)
        except Profile.DoesNotExist:
            raise serializers.ValidationError("El perfil no existe")
        return value


class BulkCandidateUploadSerializer(serializers.Serializer):
    """Serializer para carga masiva de candidatos desde CSV"""
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        """Valida que el archivo sea CSV"""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("El archivo debe ser CSV")
        return value