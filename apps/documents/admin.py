"""
Admin para la gestión de Documentos
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DocumentTemplate,
    GeneratedDocument,
    DocumentSection,
    DocumentLog
)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """
    Admin para DocumentTemplate
    """
    list_display = [
        'name',
        'document_type_badge',
        'is_active_badge',
        'is_default_badge',
        'created_by',
        'documents_count',
        'created_at'
    ]
    list_filter = [
        'document_type',
        'is_active',
        'is_default',
        'created_at'
    ]
    search_fields = [
        'name',
        'description',
        'header_text',
        'footer_text'
    ]
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at',
        'documents_count',
        'logo_preview'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'document_type',
                'is_active',
                'is_default'
            )
        }),
        ('Configuración Visual', {
            'fields': (
                'logo',
                'logo_preview',
                'header_text',
                'footer_text',
                'style_config'
            )
        }),
        ('Contenido', {
            'fields': (
                'sections',
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_by',
                'documents_count',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def document_type_badge(self, obj):
        """Badge para el tipo de documento"""
        colors = {
            'profile': '#3498db',
            'candidate_report': '#2ecc71',
            'comparison': '#f39c12',
            'final_report': '#e74c3c',
            'client_report': '#9b59b6',
            'custom': '#95a5a6',
        }
        color = colors.get(obj.document_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_document_type_display()
        )
    document_type_badge.short_description = 'Tipo'
    
    def is_active_badge(self, obj):
        """Badge para el estado activo"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactivo</span>'
        )
    is_active_badge.short_description = 'Estado'
    
    def is_default_badge(self, obj):
        """Badge para plantilla por defecto"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #f39c12; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px;">★ POR DEFECTO</span>'
            )
        return '-'
    is_default_badge.short_description = 'Predeterminada'
    
    def documents_count(self, obj):
        """Número de documentos generados con esta plantilla"""
        count = obj.generated_documents.count()
        url = reverse('admin:documents_generateddocument_changelist') + f'?template__id__exact={obj.id}'
        return format_html(
            '<a href="{}">{} documentos</a>',
            url,
            count
        )
    documents_count.short_description = 'Documentos Generados'
    
    def logo_preview(self, obj):
        """Preview del logo"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.logo.url
            )
        return '-'
    logo_preview.short_description = 'Preview del Logo'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo estableciendo el usuario creador"""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    """
    Admin para GeneratedDocument
    """
    list_display = [
        'title',
        'status_badge',
        'template_link',
        'profile_link',
        'candidate_link',
        'generated_by',
        'download_count',
        'file_size_display',
        'created_at',
        'actions_column'
    ]
    list_filter = [
        'status',
        'template__document_type',
        'created_at',
        'generated_by'
    ]
    search_fields = [
        'title',
        'description',
        'profile__position_title',
        'candidate__first_name',
        'candidate__last_name'
    ]
    readonly_fields = [
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
        'file_preview',
        'parent_link'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'title',
                'description',
                'status',
                'error_message'
            )
        }),
        ('Configuración', {
            'fields': (
                'template',
                'profile',
                'candidate',
                'custom_data'
            )
        }),
        ('Archivo Generado', {
            'fields': (
                'file',
                'file_preview',
                'file_size',
                'generation_time'
            )
        }),
        ('Estadísticas', {
            'fields': (
                'download_count',
                'last_downloaded_at',
                'version',
                'parent_document',
                'parent_link'
            )
        }),
        ('Auditoría', {
            'fields': (
                'generated_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Badge para el estado del documento"""
        colors = {
            'pending': '#f39c12',
            'generating': '#3498db',
            'completed': '#2ecc71',
            'failed': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        
        icon = {
            'pending': '⏳',
            'generating': '⚙️',
            'completed': '✓',
            'failed': '✗',
        }.get(obj.status, '•')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def template_link(self, obj):
        """Link a la plantilla"""
        if obj.template:
            url = reverse('admin:documents_documenttemplate_change', args=[obj.template.id])
            return format_html('<a href="{}">{}</a>', url, obj.template.name)
        return '-'
    template_link.short_description = 'Plantilla'
    
    def profile_link(self, obj):
        """Link al perfil"""
        if obj.profile:
            url = reverse('admin:profiles_profile_change', args=[obj.profile.id])
            return format_html('<a href="{}">{}</a>', url, obj.profile.position_title)
        return '-'
    profile_link.short_description = 'Perfil'
    
    def candidate_link(self, obj):
        """Link al candidato"""
        if obj.candidate:
            url = reverse('admin:candidates_candidate_change', args=[obj.candidate.id])
            return format_html('<a href="{}">{}</a>', url, obj.candidate.get_full_name())
        return '-'
    candidate_link.short_description = 'Candidato'
    
    def file_size_display(self, obj):
        """Tamaño del archivo formateado"""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            if size_mb < 1:
                size_kb = obj.file_size / 1024
                return f"{size_kb:.1f} KB"
            return f"{size_mb:.2f} MB"
        return '-'
    file_size_display.short_description = 'Tamaño'
    
    def file_preview(self, obj):
        """Preview o link de descarga del archivo"""
        if obj.file and obj.status == 'completed':
            return format_html(
                '<a href="{}" class="button" target="_blank">Descargar PDF</a>',
                obj.file.url
            )
        return '-'
    file_preview.short_description = 'Archivo'
    
    def parent_link(self, obj):
        """Link al documento padre"""
        if obj.parent_document:
            url = reverse('admin:documents_generateddocument_change', args=[obj.parent_document.id])
            return format_html(
                '<a href="{}">Ver documento original (v{})</a>',
                url,
                obj.parent_document.version
            )
        return '-'
    parent_link.short_description = 'Documento Original'
    
    def actions_column(self, obj):
        """Acciones disponibles"""
        actions = []
        
        if obj.status == 'completed' and obj.file:
            actions.append(
                f'<a href="{obj.file.url}" class="button" target="_blank">Ver</a>'
            )
        
        if obj.status in ['completed', 'failed']:
            actions.append(
                '<button class="button" onclick="regenerateDocument({})">Regenerar</button>'.format(obj.id)
            )
        
        return format_html(' '.join(actions))
    actions_column.short_description = 'Acciones'


@admin.register(DocumentSection)
class DocumentSectionAdmin(admin.ModelAdmin):
    """
    Admin para DocumentSection
    """
    list_display = [
        'name',
        'code',
        'order',
        'is_active_badge',
        'variables_count',
        'created_at'
    ]
    list_filter = [
        'is_active',
        'created_at'
    ]
    search_fields = [
        'name',
        'code',
        'description',
        'content'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'variables_count'
    ]
    ordering = ['order', 'name']
    
    def is_active_badge(self, obj):
        """Badge para el estado activo"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    is_active_badge.short_description = 'Activo'
    
    def variables_count(self, obj):
        """Número de variables disponibles"""
        return len(obj.available_variables) if obj.available_variables else 0
    variables_count.short_description = 'Variables'


@admin.register(DocumentLog)
class DocumentLogAdmin(admin.ModelAdmin):
    """
    Admin para DocumentLog
    """
    list_display = [
        'document_link',
        'action_badge',
        'user',
        'ip_address',
        'created_at'
    ]
    list_filter = [
        'action',
        'created_at'
    ]
    search_fields = [
        'document__title',
        'user__email',
        'ip_address'
    ]
    readonly_fields = [
        'document',
        'action',
        'user',
        'details',
        'ip_address',
        'created_at'
    ]
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar logs"""
        return False
    
    def document_link(self, obj):
        """Link al documento"""
        url = reverse('admin:documents_generateddocument_change', args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, obj.document.title)
    document_link.short_description = 'Documento'
    
    def action_badge(self, obj):
        """Badge para la acción"""
        colors = {
            'generated': '#3498db',
            'downloaded': '#2ecc71',
            'shared': '#f39c12',
            'deleted': '#e74c3c',
            'regenerated': '#9b59b6',
        }
        color = colors.get(obj.action, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Acción'