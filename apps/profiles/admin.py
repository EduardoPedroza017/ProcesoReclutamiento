"""
Configuración del Admin para Perfiles de Reclutamiento
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Profile, ProfileStatusHistory, ProfileDocument


class ProfileStatusHistoryInline(admin.TabularInline):
    """Inline para mostrar el historial de estados dentro del perfil"""
    model = ProfileStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'timestamp', 'notes']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ProfileDocumentInline(admin.TabularInline):
    """Inline para mostrar documentos dentro del perfil"""
    model = ProfileDocument
    extra = 1
    readonly_fields = ['uploaded_by', 'uploaded_at', 'file_link']
    fields = ['document_type', 'file', 'file_link', 'description', 'uploaded_by', 'uploaded_at']
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Ver archivo</a>', obj.file.url)
        return "-"
    file_link.short_description = 'Enlace'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Administración de Perfiles de Reclutamiento"""
    
    list_display = [
        'position_title',
        'client_link',
        'status_badge',
        'priority_badge',
        'service_type',
        'assigned_to',
        'salary_range_display',
        'number_of_positions',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'priority',
        'service_type',
        'is_remote',
        'is_hybrid',
        'client_approved',
        'created_at',
        'salary_currency',
    ]
    
    search_fields = [
        'position_title',
        'client__company_name',
        'department',
        'location_city',
        'location_state',
        'position_description',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'completed_at',
        'client_approval_date',
        'candidates_count',
        'salary_range',
    ]
    
    autocomplete_fields = ['client', 'assigned_to', 'created_by']
    
    inlines = [ProfileStatusHistoryInline, ProfileDocumentInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                ('client', 'assigned_to'),
                'position_title',
                'department',
                'position_description',
            )
        }),
        ('Ubicación', {
            'fields': (
                ('location_city', 'location_state'),
                ('is_remote', 'is_hybrid'),
            )
        }),
        ('Salario', {
            'fields': (
                ('salary_min', 'salary_max'),
                ('salary_currency', 'salary_period'),
                'salary_range',
            )
        }),
        ('Requisitos', {
            'fields': (
                'education_level',
                'years_experience',
                ('age_min', 'age_max'),
                'technical_skills',
                'soft_skills',
                'languages',
                'additional_requirements',
            )
        }),
        ('Beneficios y Otros', {
            'fields': (
                'benefits',
            )
        }),
        ('Gestión del Proceso', {
            'fields': (
                ('status', 'priority'),
                ('service_type', 'number_of_positions'),
                ('desired_start_date', 'deadline'),
                'internal_notes',
            )
        }),
        ('Transcripción de Reunión (IA)', {
            'fields': (
                'meeting_transcription',
            ),
            'classes': ('collapse',),
        }),
        ('Aprobación del Cliente', {
            'fields': (
                'client_approved',
                'client_approval_date',
                'client_feedback',
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                ('created_at', 'updated_at'),
                'completed_at',
                'candidates_count',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'mark_as_approved',
        'mark_as_in_progress',
        'mark_as_completed',
        'mark_as_cancelled',
    ]
    
    def client_link(self, obj):
        """Muestra un enlace al cliente"""
        if obj.client:
            url = reverse('admin:clients_client_change', args=[obj.client.pk])
            return format_html('<a href="{}">{}</a>', url, obj.client.company_name)
        return "-"
    client_link.short_description = 'Cliente'
    
    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'draft': '#6c757d',           # Gris
            'pending': '#ffc107',          # Amarillo
            'approved': '#28a745',         # Verde
            'in_progress': '#17a2b8',      # Azul claro
            'candidates_found': '#007bff', # Azul
            'in_evaluation': '#fd7e14',    # Naranja
            'in_interview': '#e83e8c',     # Rosa
            'finalists': '#6f42c1',        # Púrpura
            'completed': '#20c997',        # Verde azulado
            'cancelled': '#dc3545',        # Rojo
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def priority_badge(self, obj):
        """Muestra la prioridad con un badge de color"""
        colors = {
            'low': '#28a745',      # Verde
            'medium': '#ffc107',   # Amarillo
            'high': '#fd7e14',     # Naranja
            'urgent': '#dc3545',   # Rojo
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    
    def salary_range_display(self, obj):
        """Muestra el rango salarial formateado"""
        return obj.salary_range
    salary_range_display.short_description = 'Rango Salarial'
    
    # Acciones personalizadas
    @admin.action(description='Marcar como Aprobado')
    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status=Profile.STATUS_APPROVED)
        self.message_user(request, f'{updated} perfil(es) marcado(s) como Aprobado.')
    
    @admin.action(description='Marcar como En Proceso')
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status=Profile.STATUS_IN_PROGRESS)
        self.message_user(request, f'{updated} perfil(es) marcado(s) como En Proceso.')
    
    @admin.action(description='Marcar como Completado')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            status=Profile.STATUS_COMPLETED,
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} perfil(es) marcado(s) como Completado.')
    
    @admin.action(description='Marcar como Cancelado')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status=Profile.STATUS_CANCELLED)
        self.message_user(request, f'{updated} perfil(es) marcado(s) como Cancelado.')
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que creó el perfil"""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProfileStatusHistory)
class ProfileStatusHistoryAdmin(admin.ModelAdmin):
    """Administración del Historial de Estados"""
    
    list_display = [
        'profile',
        'from_status_display',
        'to_status_display',
        'changed_by',
        'timestamp',
    ]
    
    list_filter = [
        'from_status',
        'to_status',
        'timestamp',
    ]
    
    search_fields = [
        'profile__position_title',
        'profile__client__company_name',
        'notes',
    ]
    
    readonly_fields = [
        'profile',
        'from_status',
        'to_status',
        'changed_by',
        'timestamp',
    ]
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar manualmente"""
        return False
    
    def from_status_display(self, obj):
        """Muestra el estado anterior con color"""
        return format_html(
            '<span style="padding: 2px 8px; background-color: #e9ecef; '
            'border-radius: 3px;">{}</span>',
            obj.get_from_status_display()
        )
    from_status_display.short_description = 'Estado Anterior'
    
    def to_status_display(self, obj):
        """Muestra el estado nuevo con color"""
        return format_html(
            '<span style="padding: 2px 8px; background-color: #d4edda; '
            'border-radius: 3px; color: #155724;">{}</span>',
            obj.get_to_status_display()
        )
    to_status_display.short_description = 'Estado Nuevo'


@admin.register(ProfileDocument)
class ProfileDocumentAdmin(admin.ModelAdmin):
    """Administración de Documentos de Perfiles"""
    
    list_display = [
        'profile',
        'document_type',
        'description',
        'uploaded_by',
        'uploaded_at',
        'file_preview',
    ]
    
    list_filter = [
        'document_type',
        'uploaded_at',
    ]
    
    search_fields = [
        'profile__position_title',
        'profile__client__company_name',
        'description',
    ]
    
    readonly_fields = [
        'uploaded_by',
        'uploaded_at',
        'file_preview',
    ]
    
    autocomplete_fields = ['profile']
    
    def file_preview(self, obj):
        """Muestra un enlace para ver/descargar el archivo"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #007bff; '
                'color: white; padding: 5px 10px; text-decoration: none; '
                'border-radius: 3px;">📄 Ver/Descargar</a>',
                obj.file.url
            )
        return "-"
    file_preview.short_description = 'Archivo'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que subió el documento"""
        if not change:  # Si es nuevo
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)