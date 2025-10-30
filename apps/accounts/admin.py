"""
Admin para la app de Accounts
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personalizado para el modelo User"""
    
    list_display = [
        'email', 'full_name_display', 'role_badge', 
        'is_active', 'created_at'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Permisos', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'role',
                'password1', 'password2'
            ),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    def full_name_display(self, obj):
        """Mostrar nombre completo"""
        return obj.get_full_name()
    full_name_display.short_description = 'Nombre Completo'
    
    def role_badge(self, obj):
        """Mostrar rol con badge de color"""
        colors = {
            'admin': '#dc3545',
            'director': '#007bff',
            'supervisor': '#28a745',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Rol'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin para actividades de usuario"""
    
    list_display = [
        'user', 'action', 'description_short', 
        'ip_address', 'timestamp'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'action', 'description']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'timestamp']
    ordering = ['-timestamp']
    
    def description_short(self, obj):
        """Mostrar descripción truncada"""
        if len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description
    description_short.short_description = 'Descripción'
    
    def has_add_permission(self, request):
        """No permitir agregar actividades manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar actividades"""
        return False