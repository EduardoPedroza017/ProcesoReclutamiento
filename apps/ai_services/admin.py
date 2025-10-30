"""
Configuración del Admin para AI Services
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from .models import AIAnalysisHistory, AIPromptTemplate, AIConfiguration
import json


@admin.register(AIAnalysisHistory)
class AIAnalysisHistoryAdmin(admin.ModelAdmin):
    """Admin para el historial de análisis de IA"""
    
    list_display = [
        'id',
        'analysis_type_badge',
        'related_object',
        'success_badge',
        'tokens_used',
        'processing_time_formatted',
        'cost_estimate_formatted',
        'created_by',
        'created_at',
    ]
    
    list_filter = [
        'analysis_type',
        'success',
        'model_used',
        'created_at',
    ]
    
    search_fields = [
        'profile__position_title',
        'candidate__first_name',
        'candidate__last_name',
        'candidate__email',
        'error_message',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'formatted_input',
        'formatted_output',
        'cost_estimate',
        'processing_time_formatted',
    ]
    
    autocomplete_fields = ['profile', 'candidate']
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'id',
                'analysis_type',
                'model_used',
                'profile',
                'candidate',
            )
        }),
        ('Estado', {
            'fields': (
                'success',
                'error_message',
            )
        }),
        ('Métricas', {
            'fields': (
                'tokens_used',
                'processing_time',
                'processing_time_formatted',
                'cost_estimate',
            )
        }),
        ('Datos de Entrada', {
            'fields': (
                'formatted_input',
            ),
            'classes': ('collapse',),
        }),
        ('Resultado', {
            'fields': (
                'formatted_output',
            ),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
            )
        }),
    )
    
    def analysis_type_badge(self, obj):
        """Badge colorido para el tipo de análisis"""
        colors = {
            'transcription': '#17a2b8',
            'cv_parsing': '#28a745',
            'profile_generation': '#007bff',
            'candidate_matching': '#ffc107',
            'evaluation_generation': '#6f42c1',
        }
        color = colors.get(obj.analysis_type, '#6c757d')
        icon = {
            'transcription': '🎤',
            'cv_parsing': '📄',
            'profile_generation': '📋',
            'candidate_matching': '🔍',
            'evaluation_generation': '📝',
        }.get(obj.analysis_type, '🤖')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, obj.get_analysis_type_display()
        )
    analysis_type_badge.short_description = 'Tipo'
    analysis_type_badge.admin_order_field = 'analysis_type'
    
    def related_object(self, obj):
        """Enlaces a objetos relacionados"""
        links = []
        
        if obj.profile:
            url = reverse('admin:profiles_profile_change', args=[obj.profile.pk])
            links.append(format_html(
                '<a href="{}" style="color: #007bff;">📋 {}</a>',
                url, obj.profile.position_title[:30]
            ))
        
        if obj.candidate:
            url = reverse('admin:candidates_candidate_change', args=[obj.candidate.pk])
            links.append(format_html(
                '<a href="{}" style="color: #28a745;">👤 {}</a>',
                url, obj.candidate.full_name
            ))
        
        return format_html(' | '.join(links)) if links else '-'
    related_object.short_description = 'Relacionado con'
    
    def success_badge(self, obj):
        """Badge de éxito/error"""
        if obj.success:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 3px; font-size: 11px;">✓ Exitoso</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-size: 11px;">✗ Error</span>'
        )
    success_badge.short_description = 'Estado'
    success_badge.admin_order_field = 'success'
    
    def processing_time_formatted(self, obj):
        """Tiempo de procesamiento formateado"""
        if obj.processing_time < 1:
            return f"{obj.processing_time * 1000:.0f} ms"
        return f"{obj.processing_time:.2f} s"
    processing_time_formatted.short_description = 'Tiempo'
    processing_time_formatted.admin_order_field = 'processing_time'
    
    def cost_estimate_formatted(self, obj):
        """Costo estimado formateado"""
        return f"${obj.cost_estimate:.4f}"
    cost_estimate_formatted.short_description = 'Costo Est.'
    
    def formatted_input(self, obj):
        """JSON de entrada formateado"""
        try:
            data = json.dumps(obj.input_data, indent=2, ensure_ascii=False)
            # Limitar a 5000 caracteres para no sobrecargar la página
            if len(data) > 5000:
                data = data[:5000] + "\n...\n[Truncado - datos muy largos]"
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; '
                'border-radius: 5px; max-height: 400px; overflow-y: auto; '
                'font-family: monospace; font-size: 12px;">{}</pre>',
                data
            )
        except:
            return format_html('<pre>Error al formatear JSON</pre>')
    formatted_input.short_description = 'Datos de Entrada (JSON)'
    
    def formatted_output(self, obj):
        """JSON de salida formateado"""
        try:
            data = json.dumps(obj.output_data, indent=2, ensure_ascii=False)
            # Limitar a 5000 caracteres
            if len(data) > 5000:
                data = data[:5000] + "\n...\n[Truncado - datos muy largos]"
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; '
                'border-radius: 5px; max-height: 400px; overflow-y: auto; '
                'font-family: monospace; font-size: 12px;">{}</pre>',
                data
            )
        except:
            return format_html('<pre>Error al formatear JSON</pre>')
    formatted_output.short_description = 'Resultado (JSON)'
    
    def has_add_permission(self, request):
        """No permitir crear manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo lectura"""
        return False
    
    def get_queryset(self, request):
        """Optimizar queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'profile',
            'candidate',
            'created_by'
        )
    
    # Acciones personalizadas
    actions = ['export_to_csv']
    
    @admin.action(description='Exportar a CSV')
    def export_to_csv(self, request, queryset):
        """Exportar análisis seleccionados a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ai_analysis.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Tipo', 'Perfil', 'Candidato', 'Exitoso', 
            'Tokens', 'Tiempo (s)', 'Costo Est.', 'Fecha'
        ])
        
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.get_analysis_type_display(),
                str(obj.profile) if obj.profile else '',
                str(obj.candidate) if obj.candidate else '',
                'Sí' if obj.success else 'No',
                obj.tokens_used,
                obj.processing_time,
                obj.cost_estimate,
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    """Admin para plantillas de prompts"""
    
    list_display = [
        'name',
        'analysis_type_badge',
        'is_active_badge',
        'max_tokens',
        'temperature',
        'updated_at',
    ]
    
    list_filter = [
        'analysis_type',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'prompt_template',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'preview_prompt']
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'name',
                'analysis_type',
                'is_active',
                'description',
            )
        }),
        ('Configuración del Prompt', {
            'fields': (
                'system_message',
                'prompt_template',
                'preview_prompt',
            )
        }),
        ('Parámetros de IA', {
            'fields': (
                'max_tokens',
                'temperature',
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def analysis_type_badge(self, obj):
        """Badge para tipo de análisis"""
        colors = {
            'transcription': '#17a2b8',
            'cv_parsing': '#28a745',
            'profile_generation': '#007bff',
            'candidate_matching': '#ffc107',
            'evaluation_generation': '#6f42c1',
        }
        color = colors.get(obj.analysis_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_analysis_type_display()
        )
    analysis_type_badge.short_description = 'Tipo'
    
    def is_active_badge(self, obj):
        """Badge de estado activo"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: #dc3545;">✗ Inactivo</span>'
        )
    is_active_badge.short_description = 'Estado'
    
    def preview_prompt(self, obj):
        """Vista previa del prompt"""
        preview = obj.prompt_template[:500] if len(obj.prompt_template) > 500 else obj.prompt_template
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; '
            'border-radius: 5px; font-family: monospace; font-size: 12px; '
            'white-space: pre-wrap;">{}</div>',
            preview + ('...' if len(obj.prompt_template) > 500 else '')
        )
    preview_prompt.short_description = 'Vista Previa del Prompt'
    
    def save_model(self, request, obj, form, change):
        """Guardar el usuario que crea/modifica"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    """Admin para configuración de IA (Singleton)"""
    
    list_display = [
        '__str__',
        'default_model',
        'tokens_used_today_formatted',
        'daily_limit_percentage',
        'features_status',
        'updated_at',
    ]
    
    readonly_fields = [
        'tokens_used_today',
        'last_reset_date',
        'updated_at',
        'daily_usage_chart',
    ]
    
    fieldsets = (
        ('Configuración de API', {
            'fields': (
                'api_key_encrypted',
                'default_model',
            )
        }),
        ('Límites de Uso', {
            'fields': (
                'max_tokens_per_request',
                'daily_token_limit',
                'tokens_used_today',
                'daily_usage_chart',
                'last_reset_date',
            )
        }),
        ('Features Automáticas', {
            'fields': (
                'auto_analyze_cvs',
                'auto_generate_profiles',
                'auto_match_candidates',
            )
        }),
        ('Configuración de Procesamiento', {
            'fields': (
                'enable_async_processing',
                'retry_on_failure',
                'max_retries',
            )
        }),
        ('Información del Sistema', {
            'fields': (
                'updated_at',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def tokens_used_today_formatted(self, obj):
        """Tokens usados hoy formateado"""
        return format_html(
            '<strong>{:,}</strong> tokens',
            obj.tokens_used_today
        )
    tokens_used_today_formatted.short_description = 'Tokens Usados Hoy'
    
    def daily_limit_percentage(self, obj):
        """Porcentaje del límite diario usado"""
        if obj.daily_token_limit == 0:
            return '-'
        
        percentage = (obj.tokens_used_today / obj.daily_token_limit) * 100
        
        # Color según el porcentaje
        if percentage < 50:
            color = '#28a745'  # Verde
        elif percentage < 80:
            color = '#ffc107'  # Amarillo
        else:
            color = '#dc3545'  # Rojo
        
        return format_html(
            '<div style="width: 200px; background: #e9ecef; border-radius: 3px; '
            'overflow: hidden; position: relative;">'
            '<div style="background: {}; height: 20px; width: {}%; '
            'transition: width 0.3s;"></div>'
            '<span style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); '
            'line-height: 20px; font-size: 11px; font-weight: bold;">{:.1f}%</span>'
            '</div>',
            color, min(percentage, 100), percentage
        )
    daily_limit_percentage.short_description = '% Límite Diario'
    
    def features_status(self, obj):
        """Estado de features automáticas"""
        features = []
        if obj.auto_analyze_cvs:
            features.append('📄 CVs')
        if obj.auto_generate_profiles:
            features.append('📋 Perfiles')
        if obj.auto_match_candidates:
            features.append('🔍 Matching')
        
        if features:
            return format_html(
                '<span style="color: #28a745;">✓ {}</span>',
                ' | '.join(features)
            )
        return format_html('<span style="color: #6c757d;">Sin features automáticas</span>')
    features_status.short_description = 'Features Activas'
    
    def daily_usage_chart(self, obj):
        """Gráfico simple del uso diario"""
        # Obtener estadísticas de los últimos 7 días
        from django.utils import timezone
        from django.db.models import Sum
        from datetime import timedelta
        
        today = timezone.now().date()
        last_week = today - timedelta(days=7)
        
        # Obtener análisis de los últimos 7 días
        daily_stats = []
        for i in range(7, -1, -1):
            date = today - timedelta(days=i)
            tokens = AIAnalysisHistory.objects.filter(
                created_at__date=date
            ).aggregate(total=Sum('tokens_used'))['total'] or 0
            daily_stats.append({
                'date': date.strftime('%d/%m'),
                'tokens': tokens
            })
        
        # Crear mini gráfico HTML
        max_tokens = max([s['tokens'] for s in daily_stats]) or 1
        
        bars_html = ''
        for stat in daily_stats:
            height = (stat['tokens'] / max_tokens) * 100 if max_tokens > 0 else 0
            bars_html += f'''
                <div style="display: inline-block; width: 40px; margin: 0 2px; text-align: center;">
                    <div style="height: 100px; position: relative; background: #f8f9fa;">
                        <div style="position: absolute; bottom: 0; width: 100%; 
                            height: {height}%; background: #007bff;"></div>
                    </div>
                    <div style="font-size: 10px; margin-top: 2px;">{stat['date']}</div>
                    <div style="font-size: 9px; color: #6c757d;">{stat['tokens']:,}</div>
                </div>
            '''
        
        return format_html(
            '<div style="padding: 10px; background: white; border: 1px solid #dee2e6; '
            'border-radius: 5px;">'
            '<h4 style="margin: 0 0 10px 0; font-size: 14px;">Uso de Tokens - Últimos 8 días</h4>'
            '<div style="display: flex; align-items: flex-end;">{}</div>'
            '</div>',
            bars_html
        )
    daily_usage_chart.short_description = 'Estadísticas de Uso'
    
    def has_add_permission(self, request):
        """Solo permitir una instancia"""
        return not AIConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Guardar usuario que modifica"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)