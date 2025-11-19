"""
Configuración MEJORADA del Admin para Perfiles de Reclutamiento
Este archivo soluciona los problemas de usabilidad del formulario

CAMBIOS:
1. Campos JSON convertidos a campos de texto con TaggingWidget
2. Modalidad de trabajo como campo de selección único
3. Mejores ayudas visuales y validaciones
"""
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
import json
from .models import Profile, ProfileStatusHistory, ProfileDocument


# ============================================
# WIDGETS Y CAMPOS PERSONALIZADOS
# ============================================

class JSONListWidget(forms.Textarea):
    """Widget que permite ingresar listas JSON de forma más amigable"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'rows': 5,
            'placeholder': 'Ingrese cada elemento en una línea nueva\nEjemplo:\nPython\nDjango\nPostgreSQL',
            'style': 'width: 100%; font-family: monospace;'
        })
    
    def format_value(self, value):
        """Convierte lista JSON a texto con líneas"""
        if value is None or value == '':
            return ''
        
        # Si ya es una lista Python
        if isinstance(value, list):
            return '\n'.join(str(item) for item in value)
        
        # Si es un string JSON
        try:
            if isinstance(value, str):
                data = json.loads(value)
                if isinstance(data, list):
                    return '\n'.join(str(item) for item in data)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return value


class JSONListField(forms.CharField):
    """Campo que convierte texto con líneas a lista JSON"""
    
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = JSONListWidget
        kwargs['required'] = False
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Convierte el texto a lista"""
        if not value:
            return []
        
        # Si ya es una lista, devolverla
        if isinstance(value, list):
            return value
        
        # Dividir por líneas y limpiar
        lines = [line.strip() for line in value.split('\n')]
        # Filtrar líneas vacías
        return [line for line in lines if line]
    
    def prepare_value(self, value):
        """Prepara el valor para mostrar en el widget"""
        if not value:
            return ''
        
        if isinstance(value, list):
            return '\n'.join(str(item) for item in value)
        
        return value


class LanguagesWidget(forms.Textarea):
    """Widget especial para idiomas con formato 'Idioma (Nivel)'"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({
            'rows': 5,
            'placeholder': 'Ingrese cada idioma en una línea nueva con el formato:\nIdioma (Nivel)\n\nEjemplo:\nEspañol (Nativo)\nInglés (Avanzado)\nFrancés (Intermedio)',
            'style': 'width: 100%; font-family: monospace;'
        })
    
    def format_value(self, value):
        """Convierte lista JSON a texto con líneas"""
        if value is None or value == '':
            return ''
        
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, dict):
                    # Formato: {"language": "Español", "level": "Nativo"}
                    lang = item.get('language', '')
                    level = item.get('level', '')
                    if lang:
                        lines.append(f"{lang} ({level})" if level else lang)
                else:
                    lines.append(str(item))
            return '\n'.join(lines)
        
        return value


class LanguagesField(forms.CharField):
    """Campo que convierte texto de idiomas a lista JSON con estructura"""
    
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = LanguagesWidget
        kwargs['required'] = False
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Convierte el texto a lista de diccionarios"""
        if not value:
            return []
        
        if isinstance(value, list):
            return value
        
        lines = [line.strip() for line in value.split('\n')]
        result = []
        
        for line in lines:
            if not line:
                continue
            
            # Intentar extraer idioma y nivel
            if '(' in line and ')' in line:
                # Formato: "Inglés (Avanzado)"
                parts = line.split('(')
                language = parts[0].strip()
                level = parts[1].replace(')', '').strip()
                result.append({
                    'language': language,
                    'level': level
                })
            else:
                # Solo idioma sin nivel
                result.append({
                    'language': line,
                    'level': ''
                })
        
        return result


# ============================================
# FORMULARIO PERSONALIZADO
# ============================================

class ProfileAdminForm(forms.ModelForm):
    """Formulario personalizado para Profile con campos mejorados"""
    
    # Reemplazar campos JSON con campos de texto amigables
    technical_skills = JSONListField(
        label='Habilidades Técnicas',
        help_text='Ingrese cada habilidad en una línea nueva. Ejemplo: Python, Django, PostgreSQL'
    )
    
    soft_skills = JSONListField(
        label='Habilidades Blandas',
        help_text='Ingrese cada competencia en una línea nueva. Ejemplo: Liderazgo, Trabajo en equipo'
    )
    
    languages = LanguagesField(
        label='Idiomas',
        help_text='Ingrese cada idioma con su nivel en el formato: Idioma (Nivel). Ejemplo: Inglés (Avanzado)'
    )
    
    # Campo de selección única para modalidad de trabajo
    WORK_MODALITY_CHOICES = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    ]
    
    work_modality = forms.ChoiceField(
        choices=WORK_MODALITY_CHOICES,
        widget=forms.RadioSelect,
        label='Modalidad de Trabajo',
        required=True,
        initial='presencial'
    )
    
    class Meta:
        model = Profile
        fields = '__all__'
        widgets = {
            'position_description': forms.Textarea(attrs={'rows': 4}),
            'benefits': forms.Textarea(attrs={'rows': 3}),
            'additional_requirements': forms.Textarea(attrs={'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
            'meeting_transcription': forms.Textarea(attrs={'rows': 5}),
            'client_feedback': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, determinar la modalidad actual
        if self.instance and self.instance.pk:
            if self.instance.is_remote:
                self.initial['work_modality'] = 'remoto'
            elif self.instance.is_hybrid:
                self.initial['work_modality'] = 'hibrido'
            else:
                self.initial['work_modality'] = 'presencial'
        
        # Ocultar los campos booleanos originales (los manejaremos con work_modality)
        if 'is_remote' in self.fields:
            self.fields['is_remote'].widget = forms.HiddenInput()
        if 'is_hybrid' in self.fields:
            self.fields['is_hybrid'].widget = forms.HiddenInput()
    
    def clean(self):
        """Validaciones personalizadas"""
        cleaned_data = super().clean()
        
        # Convertir work_modality a is_remote e is_hybrid
        work_modality = cleaned_data.get('work_modality')
        if work_modality == 'remoto':
            cleaned_data['is_remote'] = True
            cleaned_data['is_hybrid'] = False
        elif work_modality == 'hibrido':
            cleaned_data['is_remote'] = False
            cleaned_data['is_hybrid'] = True
        else:  # presencial
            cleaned_data['is_remote'] = False
            cleaned_data['is_hybrid'] = False
        
        # Validar que salary_max >= salary_min
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_max < salary_min:
            raise ValidationError({
                'salary_max': 'El salario máximo debe ser mayor o igual al salario mínimo'
            })
        
        # Validar edad
        age_min = cleaned_data.get('age_min')
        age_max = cleaned_data.get('age_max')
        
        if age_min and age_max and age_max < age_min:
            raise ValidationError({
                'age_max': 'La edad máxima debe ser mayor o igual a la edad mínima'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardar con los valores convertidos"""
        instance = super().save(commit=False)
        
        # Asegurar que los campos booleanos estén configurados correctamente
        work_modality = self.cleaned_data.get('work_modality')
        if work_modality == 'remoto':
            instance.is_remote = True
            instance.is_hybrid = False
        elif work_modality == 'hibrido':
            instance.is_remote = False
            instance.is_hybrid = True
        else:
            instance.is_remote = False
            instance.is_hybrid = False
        
        if commit:
            instance.save()
        
        return instance


# ============================================
# INLINES
# ============================================

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


# ============================================
# ADMIN PRINCIPAL MEJORADO
# ============================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Administración MEJORADA de Perfiles de Reclutamiento"""
    
    form = ProfileAdminForm  # Usar el formulario personalizado
    
    list_display = [
        'position_title',
        'client_link',
        'status_badge',
        'priority_badge',
        'service_type',
        'work_modality_display',
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
            ),
            'description': 'Información general de la posición'
        }),
        ('Ubicación y Modalidad', {
            'fields': (
                ('location_city', 'location_state'),
                'work_modality',  # Campo mejorado
                # Campos ocultos pero necesarios
                'is_remote',
                'is_hybrid',
            ),
            'description': 'Seleccione la modalidad de trabajo para la posición'
        }),
        ('Salario', {
            'fields': (
                ('salary_min', 'salary_max'),
                ('salary_currency', 'salary_period'),
                'salary_range',
            ),
            'description': 'Rango salarial ofrecido'
        }),
        ('Requisitos de la Posición', {
            'fields': (
                'education_level',
                'years_experience',
                ('age_min', 'age_max'),
            ),
            'description': 'Requisitos básicos del candidato'
        }),
        ('Habilidades y Competencias', {
            'fields': (
                'technical_skills',  # Campo mejorado
                'soft_skills',       # Campo mejorado
                'languages',         # Campo mejorado
                'additional_requirements',
            ),
            'description': 'Ingrese cada elemento en una línea nueva'
        }),
        ('Beneficios y Otros', {
            'fields': (
                'benefits',
            ),
            'classes': ('collapse',),
        }),
        ('Gestión del Proceso', {
            'fields': (
                ('status', 'priority'),
                ('service_type', 'number_of_positions'),
                ('desired_start_date', 'deadline'),
            )
        }),
        ('Transcripción y Notas', {
            'fields': (
                'meeting_transcription',
                'internal_notes',
            ),
            'classes': ('collapse',),
        }),
        ('Aprobación del Cliente', {
            'fields': (
                'client_approved',
                'client_approval_date',
                'client_feedback',
            ),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
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
    
    # Métodos personalizados para list_display
    def client_link(self, obj):
        """Muestra el cliente como enlace"""
        url = reverse('admin:clients_client_change', args=[obj.client.pk])
        return format_html('<a href="{}">{}</a>', url, obj.client.company_name)
    client_link.short_description = 'Cliente'
    client_link.admin_order_field = 'client__company_name'
    
    def status_badge(self, obj):
        """Muestra el estado con un badge de color"""
        colors = {
            'draft': '#6c757d',
            'pending': '#ffc107',
            'approved': '#28a745',
            'in_progress': '#17a2b8',
            'candidates_found': '#007bff',
            'in_evaluation': '#6f42c1',
            'in_interview': '#e83e8c',
            'finalists': '#fd7e14',
            'completed': '#28a745',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        """Muestra la prioridad con un badge de color"""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="padding: 3px 8px; background-color: {}; color: white; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    priority_badge.admin_order_field = 'priority'
    
    def salary_range_display(self, obj):
        """Muestra el rango salarial formateado"""
        try:
            return obj.salary_range
        except:
            return "No especificado"
    salary_range_display.short_description = 'Rango Salarial'
    
    def work_modality_display(self, obj):
        """Muestra la modalidad de trabajo"""
        if obj.is_remote:
            return format_html('<span style="color: #007bff;">🏠 Remoto</span>')
        elif obj.is_hybrid:
            return format_html('<span style="color: #6f42c1;">🔄 Híbrido</span>')
        else:
            return format_html('<span style="color: #28a745;">🏢 Presencial</span>')
    work_modality_display.short_description = 'Modalidad'
    
    # Actions
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
        updated = queryset.update(status=Profile.STATUS_COMPLETED)
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


# ============================================
# OTROS ADMINS (sin cambios)
# ============================================

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
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def from_status_display(self, obj):
        return format_html(
            '<span style="padding: 2px 8px; background-color: #e9ecef; '
            'border-radius: 3px;">{}</span>',
            obj.get_from_status_display()
        )
    from_status_display.short_description = 'Estado Anterior'
    
    def to_status_display(self, obj):
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
        'description',
    ]
    
    readonly_fields = ['uploaded_by', 'uploaded_at', 'file_preview']
    
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Ver archivo</a>',
                obj.file.url
            )
        return "-"
    file_preview.short_description = 'Archivo'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)