"""
Serializers para la API de Documentos
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DocumentTemplate,
    GeneratedDocument,
    DocumentSection,
    DocumentLog
)
from apps.profiles.models import Profile
from apps.candidates.models import Candidate

User = get_user_model()


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer para DocumentTemplate
    """
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    document_type_display = serializers.CharField(
        source='get_document_type_display',
        read_only=True
    )
    generated_documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'name',
            'description',
            'document_type',
            'document_type_display',
            'header_text',
            'footer_text',
            'logo',
            'style_config',
            'sections',
            'is_active',
            'is_default',
            'created_by',
            'created_by_name',
            'generated_documents_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_generated_documents_count(self, obj):
        """Retorna el número de documentos generados con esta plantilla"""
        return obj.generated_documents.count()
    
    def validate_sections(self, value):
        """Valida que las secciones sean una lista de strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Las secciones deben ser una lista")
        
        for section in value:
            if not isinstance(section, str):
                raise serializers.ValidationError("Cada sección debe ser un string")
        
        return value
    
    def validate_style_config(self, value):
        """Valida la configuración de estilo"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("La configuración de estilo debe ser un objeto JSON")
        
        return value


class DocumentTemplateSummarySerializer(serializers.ModelSerializer):
    """
    Serializer resumido para DocumentTemplate (para listados)
    """
    document_type_display = serializers.CharField(
        source='get_document_type_display',
        read_only=True
    )
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'name',
            'document_type',
            'document_type_display',
            'is_active',
            'is_default',
        ]


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer completo para GeneratedDocument
    """
    template_name = serializers.CharField(
        source='template.name',
        read_only=True
    )
    generated_by_name = serializers.CharField(
        source='generated_by.get_full_name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    profile_title = serializers.CharField(
        source='profile.position_title',
        read_only=True
    )
    candidate_name = serializers.CharField(
        source='candidate.get_full_name',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    can_regenerate = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedDocument
        fields = [
            'id',
            'title',
            'description',
            'template',
            'template_name',
            'profile',
            'profile_title',
            'candidate',
            'candidate_name',
            'custom_data',
            'file',
            'file_url',
            'file_size',
            'file_size_mb',
            'status',
            'status_display',
            'error_message',
            'generation_time',
            'download_count',
            'last_downloaded_at',
            'version',
            'parent_document',
            'generated_by',
            'generated_by_name',
            'can_regenerate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'file',
            'file_size',
            'status',
            'error_message',
            'generation_time',
            'download_count',
            'last_downloaded_at',
            'version',
            'generated_by',
            'created_at',
            'updated_at',
        ]
    
    def get_file_url(self, obj):
        """Retorna la URL del archivo si existe"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_mb(self, obj):
        """Retorna el tamaño del archivo en MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0
    
    def get_can_regenerate(self, obj):
        """Indica si el documento puede ser regenerado"""
        return obj.status in [GeneratedDocument.STATUS_COMPLETED, GeneratedDocument.STATUS_FAILED]
    
    def validate(self, data):
        """Valida que al menos profile o candidate estén presentes"""
        profile = data.get('profile')
        candidate = data.get('candidate')
        template = data.get('template')
        
        if not profile and not candidate and not data.get('custom_data'):
            raise serializers.ValidationError(
                "Debe proporcionar al menos un perfil, candidato o datos personalizados"
            )
        
        # Validar que la plantilla sea del tipo correcto
        if template and profile and template.document_type == DocumentTemplate.TYPE_PROFILE:
            pass  # Correcto
        elif template and candidate and template.document_type == DocumentTemplate.TYPE_CANDIDATE_REPORT:
            pass  # Correcto
        elif template and template.document_type == DocumentTemplate.TYPE_CUSTOM:
            pass  # Correcto
        
        return data


class GeneratedDocumentSummarySerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listados de documentos
    """
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedDocument
        fields = [
            'id',
            'title',
            'status',
            'status_display',
            'file_url',
            'download_count',
            'created_at',
        ]
    
    def get_file_url(self, obj):
        """Retorna la URL del archivo si existe"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class GenerateDocumentRequestSerializer(serializers.Serializer):
    """
    Serializer para la solicitud de generación de documento
    """
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    template_id = serializers.IntegerField(required=False, allow_null=True)
    profile_id = serializers.IntegerField(required=False, allow_null=True)
    candidate_id = serializers.IntegerField(required=False, allow_null=True)
    custom_data = serializers.JSONField(required=False)
    async_generation = serializers.BooleanField(default=True)
    
    def validate_template_id(self, value):
        """Valida que la plantilla exista"""
        if value:
            try:
                DocumentTemplate.objects.get(id=value, is_active=True)
            except DocumentTemplate.DoesNotExist:
                raise serializers.ValidationError("La plantilla no existe o está inactiva")
        return value
    
    def validate_profile_id(self, value):
        """Valida que el perfil exista"""
        if value:
            try:
                Profile.objects.get(id=value)
            except Profile.DoesNotExist:
                raise serializers.ValidationError("El perfil no existe")
        return value
    
    def validate_candidate_id(self, value):
        """Valida que el candidato exista"""
        if value:
            try:
                Candidate.objects.get(id=value)
            except Candidate.DoesNotExist:
                raise serializers.ValidationError("El candidato no existe")
        return value
    
    def validate(self, data):
        """Valida que se proporcione al menos perfil, candidato o datos personalizados"""
        if not data.get('profile_id') and not data.get('candidate_id') and not data.get('custom_data'):
            raise serializers.ValidationError(
                "Debe proporcionar profile_id, candidate_id o custom_data"
            )
        return data


class DocumentSectionSerializer(serializers.ModelSerializer):
    """
    Serializer para DocumentSection
    """
    
    class Meta:
        model = DocumentSection
        fields = [
            'id',
            'name',
            'code',
            'description',
            'content',
            'order',
            'is_active',
            'available_variables',
            'created_at',
            'updated_at',
        ]
    
    def validate_code(self, value):
        """Valida que el código sea único"""
        instance = self.instance
        if DocumentSection.objects.filter(code=value).exclude(pk=instance.pk if instance else None).exists():
            raise serializers.ValidationError("Ya existe una sección con este código")
        return value
    
    def validate_available_variables(self, value):
        """Valida que las variables sean una lista"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Las variables disponibles deben ser una lista")
        return value


class DocumentLogSerializer(serializers.ModelSerializer):
    """
    Serializer para DocumentLog
    """
    user_name = serializers.CharField(
        source='user.get_full_name',
        read_only=True
    )
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    document_title = serializers.CharField(
        source='document.title',
        read_only=True
    )
    
    class Meta:
        model = DocumentLog
        fields = [
            'id',
            'document',
            'document_title',
            'action',
            'action_display',
            'user',
            'user_name',
            'details',
            'ip_address',
            'created_at',
        ]
        read_only_fields = ['created_at']


class BulkGenerateDocumentsSerializer(serializers.Serializer):
    """
    Serializer para generación masiva de documentos
    """
    template_id = serializers.IntegerField()
    profile_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    def validate_template_id(self, value):
        """Valida que la plantilla exista"""
        try:
            DocumentTemplate.objects.get(id=value, is_active=True)
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("La plantilla no existe o está inactiva")
        return value
    
    def validate(self, data):
        """Valida que se proporcionen IDs de perfiles o candidatos"""
        if not data.get('profile_ids') and not data.get('candidate_ids'):
            raise serializers.ValidationError(
                "Debe proporcionar al menos profile_ids o candidate_ids"
            )
        return data


class DocumentStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de documentos
    """
    total_documents = serializers.IntegerField()
    by_status = serializers.DictField()
    by_type = serializers.DictField()
    total_downloads = serializers.IntegerField()
    average_generation_time = serializers.FloatField()
    recent_documents = GeneratedDocumentSummarySerializer(many=True)