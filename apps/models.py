"""
Modelos para la gestión de Clientes
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Client(models.Model):
    """
    Modelo para representar a un Cliente/Empresa
    """
    
    # Información básica
    company_name = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Empresa'
    )
    rfc = models.CharField(
        max_length=13,
        unique=True,
        verbose_name='RFC'
    )
    industry = models.CharField(
        max_length=100,
        verbose_name='Industria/Sector'
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='Sitio Web'
    )
    
    # Información de contacto
    contact_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del Contacto Principal'
    )
    contact_email = models.EmailField(
        verbose_name='Email del Contacto'
    )
    contact_phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono del Contacto'
    )
    contact_position = models.CharField(
        max_length=100,
        verbose_name='Puesto del Contacto'
    )
    
    # Dirección
    address_street = models.CharField(
        max_length=200,
        verbose_name='Calle y Número'
    )
    address_city = models.CharField(
        max_length=100,
        verbose_name='Ciudad'
    )
    address_state = models.CharField(
        max_length=100,
        verbose_name='Estado'
    )
    address_zip = models.CharField(
        max_length=10,
        verbose_name='Código Postal'
    )
    address_country = models.CharField(
        max_length=100,
        default='México',
        verbose_name='País'
    )
    
    # Gestión
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_clients',
        verbose_name='Asignado a'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    
    # Notas adicionales
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    
    # Fechas
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients',
        verbose_name='Creado por'
    )
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['rfc']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.contact_name}"
    
    @property
    def full_address(self):
        """Retorna la dirección completa"""
        return (f"{self.address_street}, {self.address_city}, "
                f"{self.address_state}, {self.address_zip}, {self.address_country}")
    
    @property
    def active_profiles_count(self):
        """Cuenta los perfiles activos del cliente"""
        return self.profiles.filter(status__in=['pending', 'approved', 'in_progress']).count()


class ContactPerson(models.Model):
    """
    Modelo para contactos adicionales de un cliente
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='Cliente'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Nombre'
    )
    position = models.CharField(
        max_length=100,
        verbose_name='Puesto'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Contacto Principal'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Persona de Contacto'
        verbose_name_plural = 'Personas de Contacto'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.client.company_name}"