"""
Serializers para Perfiles de Reclutamiento
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Profile, ProfileStatusHistory, ProfileDocument
from apps.clients.models import Client
from apps.accounts.models import User


class ProfileDocumentSerializer(serializers.ModelSerializer):
    """Serializer para documentos de perfiles"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfileDocument
        fields = [
            'id',
            'document_type',
            'file',
            'file_url',
            'description',
            'uploaded_by',
            'uploaded_by_name',
            'uploaded_at',
            'published_platforms',
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        """Retorna la URL completa del archivo"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ProfileStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer para historial de estados"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = ProfileStatusHistory
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


class ProfileListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de perfiles"""
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id',
            'position_title',
            'client',
            'client_name',
            'assigned_to',
            'assigned_to_name',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'service_type',
            'service_type_display',
            'location_city',
            'location_state',
            'salary_min',
            'salary_max',
            'salary_currency',
            'number_of_positions',
            'client_approved',
            'created_at',
            'updated_at',
        ]


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de perfil"""
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    client_data = serializers.SerializerMethodField()
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Campos calculados
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    salary_range = serializers.CharField(read_only=True)
    candidates_count = serializers.IntegerField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    
    # Relaciones
    status_history = ProfileStatusHistorySerializer(many=True, read_only=True)
    documents = ProfileDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = [
            'created_by',
            'created_at',
            'updated_at',
            'completed_at',
            'client_approval_date',
        ]
    
    def get_client_data(self, obj):
        """Retorna información básica del cliente"""
        return {
            'id': obj.client.id,
            'company_name': obj.client.company_name,
            'industry': obj.client.industry,
        }


class ProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar perfiles"""
    
    class Meta:
        model = Profile
        fields = [
            'id',
            'client',
            'assigned_to',
            'position_title',
            'position_description',
            'department',
            'location_city',
            'location_state',
            'is_remote',
            'is_hybrid',
            'salary_min',
            'salary_max',
            'salary_currency',
            'salary_period',
            'education_level',
            'years_experience',
            'age_min',
            'age_max',
            'technical_skills',
            'soft_skills',
            'languages',
            'benefits',
            'additional_requirements',
            'status',
            'service_type',
            'number_of_positions',
            'priority',
            'desired_start_date',
            'deadline',
            'meeting_transcription',
            'internal_notes',
            'client_feedback',
        ]
    
    def validate_salary_min(self, value):
        """Valida que el salario mínimo sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El salario mínimo debe ser mayor a 0")
        return value
    
    def validate_salary_max(self, value):
        """Valida que el salario máximo sea positivo"""
        if value <= 0:
            raise serializers.ValidationError("El salario máximo debe ser mayor a 0")
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto"""
        # Validar que salary_max sea mayor que salary_min
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        
        if salary_min and salary_max and salary_max < salary_min:
            raise serializers.ValidationError({
                'salary_max': 'El salario máximo debe ser mayor o igual al salario mínimo'
            })
        
        # Validar que age_max sea mayor que age_min
        age_min = data.get('age_min')
        age_max = data.get('age_max')
        
        if age_min and age_max and age_max < age_min:
            raise serializers.ValidationError({
                'age_max': 'La edad máxima debe ser mayor o igual a la edad mínima'
            })
        
        # Validar años de experiencia
        years_experience = data.get('years_experience')
        if years_experience is not None and years_experience < 0:
            raise serializers.ValidationError({
                'years_experience': 'Los años de experiencia no pueden ser negativos'
            })
        
        # Validar número de posiciones
        number_of_positions = data.get('number_of_positions', 1)
        if number_of_positions < 1:
            raise serializers.ValidationError({
                'number_of_positions': 'El número de posiciones debe ser al menos 1'
            })
        
        return data
    
    def create(self, validated_data):
        """Crea un perfil y registra el usuario creador"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualiza un perfil y registra cambios de estado"""
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Si cambió el estado, registrar en el historial
        if old_status != new_status:
            request = self.context.get('request')
            ProfileStatusHistory.objects.create(
                profile=instance,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user if request else None,
                notes=validated_data.get('internal_notes', '')
            )
            
            # Si se marca como completado, registrar la fecha
            if new_status == Profile.STATUS_COMPLETED and not instance.completed_at:
                validated_data['completed_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class ProfileApprovalSerializer(serializers.Serializer):
    """Serializer para aprobar un perfil"""
    approved = serializers.BooleanField(required=True)
    feedback = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validar que si se rechaza, se proporcione feedback"""
        if not data.get('approved') and not data.get('feedback'):
            raise serializers.ValidationError({
                'feedback': 'El feedback es requerido cuando se rechaza un perfil'
            })
        return data


class ProfileStatusChangeSerializer(serializers.Serializer):
    """Serializer para cambiar el estado de un perfil"""
    status = serializers.ChoiceField(choices=Profile.STATUS_CHOICES, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ProfileStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de perfiles"""
    total_profiles = serializers.IntegerField()
    by_status = serializers.DictField()
    by_priority = serializers.DictField()
    by_service_type = serializers.DictField()
    urgent_profiles = serializers.IntegerField()
    approved_profiles = serializers.IntegerField()
    completed_this_month = serializers.IntegerField()