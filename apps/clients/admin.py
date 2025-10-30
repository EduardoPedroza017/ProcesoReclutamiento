"""
Admin para la app de Clients
"""
from django.contrib import admin
from .models import Client, ContactPerson


class ContactPersonInline(admin.TabularInline):
    """Inline para contactos dentro del cliente"""
    model = ContactPerson
    extra = 1
    fields = ['name', 'position', 'email', 'phone', 'is_primary']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin para clientes"""
    
    list_display = [
        'company_name', 'contact_name', 'contact_email',
        'industry', 'assigned_to', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'industry', 'assigned_to', 'created_at']
    search_fields = ['company_name', 'rfc', 'contact_name', 'contact_email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [ContactPersonInline]
    
    fieldsets = (
        ('Información de la Empresa', {
            'fields': ('company_name', 'rfc', 'industry', 'website')
        }),
        ('Contacto Principal', {
            'fields': ('contact_name', 'contact_position', 'contact_email', 'contact_phone')
        }),
        ('Dirección', {
            'fields': (
                'address_street', 'address_city', 'address_state',
                'address_zip', 'address_country'
            )
        }),
        ('Gestión', {
            'fields': ('assigned_to', 'is_active', 'notes')
        }),
        ('Información del Sistema', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    """Admin para personas de contacto"""
    
    list_display = ['name', 'client', 'position', 'email', 'phone', 'is_primary']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['name', 'email', 'client__company_name']
    readonly_fields = ['created_at']