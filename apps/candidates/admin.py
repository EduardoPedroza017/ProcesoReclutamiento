"""
Configuración del Admin para Candidatos
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib import messages
import tempfile
import os
from .models import (
    Candidate,
    CandidateProfile,
    CandidateDocument,
    CandidateStatusHistory,
    CandidateNote,
)


class CandidateDocumentInline(admin.TabularInline):
    """Inline para documentos del candidato"""
    model = CandidateDocument
    extra = 1
    readonly_fields = ['uploaded_by', 'uploaded_at', 'file_link']
    fields = ['document_type', 'file', 'file_link', 'description', 'uploaded_by', 'uploaded_at']
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Ver archivo</a>', obj.file.url)
        return "-"
    file_link.short_description = 'Enlace'


class CandidateProfileInline(admin.TabularInline):
    """Inline para aplicaciones del candidato a perfiles"""
    model = CandidateProfile
    extra = 0
    readonly_fields = ['applied_at', 'profile_link']
    fields = ['profile_link', 'status', 'match_percentage', 'overall_rating', 'applied_at']
    
    def profile_link(self, obj):
        if obj.profile:
            url = reverse('admin:profiles_profile_change', args=[obj.profile.pk])
            return format_html('<a href="{}">{}</a>', url, obj.profile.position_title)
        return "-"
    profile_link.short_description = 'Perfil'


class CandidateStatusHistoryInline(admin.TabularInline):
    """Inline para historial de estados"""
    model = CandidateStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'timestamp']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class CandidateNoteInline(admin.TabularInline):
    """Inline para notas del candidato"""
    model = CandidateNote
    extra = 1
    readonly_fields = ['created_by', 'created_at']
    fields = ['note', 'is_important', 'created_by', 'created_at']


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Administración de Candidatos"""
    
    list_display = [
        'full_name',
        'email',
        'phone',
        'city',
        'status_badge',
        'years_of_experience',
        'assigned_to',
        'active_applications',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'education_level',
        'state',
        'country',
        'assigned_to',
        'created_at',
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'current_position',
        'current_company',
        'city',
        'state',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'full_name',
        'salary_expectation_range',
        'active_applications',
    ]
    
    autocomplete_fields = ['assigned_to', 'created_by']
    
    inlines = [
        CandidateProfileInline,
        CandidateDocumentInline,
        CandidateNoteInline,
        CandidateStatusHistoryInline,
    ]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                ('first_name', 'last_name'),
                'full_name',
                ('email', 'phone'),
                'alternative_phone',
            )
        }),
        ('Ubicación', {
            'fields': (
                ('city', 'state'),
                'country',
                'address',
            )
        }),
        ('Información Profesional', {
            'fields': (
                'current_position',
                'current_company',
                'years_of_experience',
                ('education_level', 'university'),
                'degree',
                'skills',
                'languages',
                'certifications',
            )
        }),
        ('Expectativas Salariales', {
            'fields': (
                ('salary_expectation_min', 'salary_expectation_max'),
                'salary_currency',
                'salary_expectation_range',
            )
        }),
        ('Disponibilidad', {
            'fields': (
                'available_from',
                'notice_period_days',
            )
        }),
        ('Redes Sociales', {
            'fields': (
                'linkedin_url',
                'portfolio_url',
                'github_url',
            ),
            'classes': ('collapse',),
        }),
        ('Análisis de IA', {
            'fields': (
                'ai_summary',
                'ai_match_score',
                'ai_analysis',
            ),
            'classes': ('collapse',),
        }),
        ('Gestión', {
            'fields': (
                ('status', 'assigned_to'),
                'source',
                'internal_notes',
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                ('created_at', 'updated_at'),
                'active_applications',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = [
        'mark_as_qualified',
        'mark_as_interview',
        'mark_as_rejected',
    ]
    
    # ============================================================
    # 🆕 AGREGAR ESTA SECCIÓN COMPLETA AQUÍ
    # ============================================================
    
    def get_urls(self):
        """Agregar URL personalizada para carga masiva de CVs"""
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-upload-cvs/',
                self.admin_site.admin_view(self.bulk_upload_cvs_view),
                name='candidates_candidate_bulk_upload_cvs'
            ),
        ]
        return custom_urls + urls
    
    def bulk_upload_cvs_view(self, request):
        """Vista para carga masiva de CVs con IA"""
        if request.method == 'POST':
            files = request.FILES.getlist('cv_files')
            profile_id = request.POST.get('profile_id')
            
            if not files:
                messages.error(request, '❌ No se seleccionaron archivos')
                return redirect('.')
            
            # Importar la tarea de procesamiento
            from .tasks import process_single_cv_for_bulk_upload
            
            # Procesar archivos
            successful = 0
            failed = 0
            errors = []
            results = []
            
            for cv_file in files:
                try:
                    # Validar extensión
                    if not cv_file.name.lower().endswith(('.pdf', '.docx')):
                        errors.append(f"❌ {cv_file.name}: Formato no válido (solo PDF/DOCX)")
                        failed += 1
                        continue
                    
                    # Validar tamaño (máx 10MB)
                    if cv_file.size > 10 * 1024 * 1024:
                        errors.append(f"❌ {cv_file.name}: Archivo muy grande (máx 10MB)")
                        failed += 1
                        continue
                    
                    # Guardar temporalmente
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, cv_file.name)
                    
                    with open(temp_path, 'wb+') as destination:
                        for chunk in cv_file.chunks():
                            destination.write(chunk)
                    
                    # Procesar con IA
                    result = process_single_cv_for_bulk_upload(
                        temp_path,
                        cv_file.name,
                        int(profile_id) if profile_id else None,
                        request.user.id
                    )
                    
                    if result['success']:
                        successful += 1
                        candidate_name = result.get('candidate_name', 'Sin nombre')
                        candidate_email = result.get('candidate_email', '')
                        results.append(f"✅ {cv_file.name} → {candidate_name} ({candidate_email})")
                    else:
                        failed += 1
                        error_msg = result.get('error', 'Error desconocido')
                        errors.append(f"❌ {cv_file.name}: {error_msg}")
                    
                except Exception as e:
                    failed += 1
                    errors.append(f"❌ {cv_file.name}: {str(e)}")
            
            # Mostrar resultados
            if successful > 0:
                messages.success(
                    request, 
                    f'🎉 {successful} CV(s) procesados exitosamente con IA'
                )
                for result in results:
                    messages.success(request, result)
            
            if failed > 0:
                messages.warning(request, f'⚠️ {failed} CV(s) fallaron')
                for error in errors[:5]:  # Mostrar solo primeros 5 errores
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f"... y {len(errors) - 5} errores más")
            
            if successful == 0 and failed == 0:
                messages.info(request, 'ℹ️ No se procesaron archivos')
            
            return redirect('..')
        
        # GET request - mostrar formulario
        from apps.profiles.models import Profile
        profiles = Profile.objects.filter(status='open').order_by('-created_at')[:50]
        
        context = {
            'title': '📤 Carga Masiva de CVs con IA',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'site_url': '/',
            'profiles': profiles,
        }
        return render(request, 'admin/candidates/bulk_upload_cvs.html', context)
    
    def changelist_view(self, request, extra_context=None):
        """Agregar botón de carga masiva en la lista"""
        extra_context = extra_context or {}
        extra_context['show_bulk_upload_button'] = True
        return super().changelist_view(request, extra_context)
    
    # ============================================================
    # FIN DE LA SECCIÓN NUEVA
    # ============================================================
    
    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'new': '#17a2b8',           # Azul claro
            'screening': '#ffc107',      # Amarillo
            'qualified': '#28a745',      # Verde
            'interview': '#007bff',      # Azul
            'offer': '#6f42c1',          # Púrpura
            'hired': '#20c997',          # Verde azulado
            'rejected': '#dc3545',       # Rojo
            'withdrawn': '#6c757d',      # Gris
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    @admin.action(description='Marcar como Calificado')
    def mark_as_qualified(self, request, queryset):
        updated = queryset.update(status=Candidate.STATUS_QUALIFIED)
        self.message_user(request, f'{updated} candidato(s) marcado(s) como Calificado.')
    
    @admin.action(description='Marcar como En Entrevista')
    def mark_as_interview(self, request, queryset):
        updated = queryset.update(status=Candidate.STATUS_INTERVIEW)
        self.message_user(request, f'{updated} candidato(s) marcado(s) como En Entrevista.')
    
    @admin.action(description='Marcar como Rechazado')
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status=Candidate.STATUS_REJECTED)
        self.message_user(request, f'{updated} candidato(s) marcado(s) como Rechazado.')
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que creó el candidato"""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    """Administración de Aplicaciones de Candidatos a Perfiles"""
    
    list_display = [
        'candidate',
        'profile',
        'status_badge',
        'match_percentage',
        'overall_rating',
        'applied_at',
    ]
    
    list_filter = [
        'status',
        'applied_at',
    ]
    
    search_fields = [
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'profile__position_title',
        'profile__client__company_name',
    ]
    
    readonly_fields = ['applied_at']
    
    autocomplete_fields = ['candidate', 'profile']
    
    fieldsets = (
        ('Aplicación', {
            'fields': (
                'candidate',
                'profile',
                'status',
                'applied_at',
            )
        }),
        ('Evaluación', {
            'fields': (
                'match_percentage',
                'overall_rating',
                'notes',
            )
        }),
        ('Fechas', {
            'fields': (
                'interview_date',
                'offer_date',
            )
        }),
        ('Rechazo', {
            'fields': (
                'rejection_reason',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'applied': '#17a2b8',
            'screening': '#ffc107',
            'shortlisted': '#28a745',
            'interview_scheduled': '#007bff',
            'interviewed': '#6f42c1',
            'offered': '#fd7e14',
            'accepted': '#20c997',
            'rejected': '#dc3545',
            'withdrawn': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'


@admin.register(CandidateDocument)
class CandidateDocumentAdmin(admin.ModelAdmin):
    """Administración de Documentos de Candidatos"""
    
    list_display = [
        'candidate',
        'document_type',
        'original_filename',
        'uploaded_by',
        'uploaded_at',
        'file_preview',
    ]
    
    list_filter = [
        'document_type',
        'uploaded_at',
    ]
    
    search_fields = [
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'original_filename',
        'description',
    ]
    
    readonly_fields = [
        'uploaded_by',
        'uploaded_at',
        'file_preview',
    ]
    
    autocomplete_fields = ['candidate']
    
    fieldsets = (
        ('Documento', {
            'fields': (
                'candidate',
                'document_type',
                'file',
                'file_preview',
                'original_filename',
                'description',
            )
        }),
        ('Análisis de IA', {
            'fields': (
                'ai_extracted_text',
                'ai_parsed_data',
            ),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': (
                'uploaded_by',
                'uploaded_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
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
            # Guardar nombre original del archivo
            if obj.file:
                obj.original_filename = obj.file.name
        super().save_model(request, obj, form, change)


@admin.register(CandidateStatusHistory)
class CandidateStatusHistoryAdmin(admin.ModelAdmin):
    """Administración del Historial de Estados"""
    
    list_display = [
        'candidate',
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
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'notes',
    ]
    
    readonly_fields = [
        'candidate',
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
        """Muestra el estado anterior"""
        return format_html(
            '<span style="padding: 2px 8px; background-color: #e9ecef; '
            'border-radius: 3px;">{}</span>',
            obj.get_from_status_display()
        )
    from_status_display.short_description = 'Estado Anterior'
    
    def to_status_display(self, obj):
        """Muestra el estado nuevo"""
        return format_html(
            '<span style="padding: 2px 8px; background-color: #d4edda; '
            'border-radius: 3px; color: #155724;">{}</span>',
            obj.get_to_status_display()
        )
    to_status_display.short_description = 'Estado Nuevo'


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    """Administración de Notas de Candidatos"""
    
    list_display = [
        'candidate',
        'note_preview',
        'is_important',
        'created_by',
        'created_at',
    ]
    
    list_filter = [
        'is_important',
        'created_at',
    ]
    
    search_fields = [
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'note',
    ]
    
    readonly_fields = [
        'created_by',
        'created_at',
    ]
    
    autocomplete_fields = ['candidate']
    
    def note_preview(self, obj):
        """Muestra una vista previa de la nota"""
        if len(obj.note) > 50:
            return obj.note[:50] + '...'
        return obj.note
    note_preview.short_description = 'Nota'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario que creó la nota"""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)