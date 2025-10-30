
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Client(models.Model):
    company_name = models.CharField(max_length=200, verbose_name='Nombre de la Empresa')
    rfc = models.CharField(max_length=13, unique=True, verbose_name='RFC')
    industry = models.CharField(max_length=100, verbose_name='Industria/Sector')
    website = models.URLField(blank=True, null=True, verbose_name='Sitio Web')
    
    contact_name = models.CharField(max_length=200, verbose_name='Nombre del Contacto')
    contact_email = models.EmailField(verbose_name='Email del Contacto')
    contact_phone = models.CharField(max_length=20, verbose_name='Teléfono')
    contact_position = models.CharField(max_length=100, verbose_name='Puesto')
    
    address_street = models.CharField(max_length=200, verbose_name='Calle')
    address_city = models.CharField(max_length=100, verbose_name='Ciudad')
    address_state = models.CharField(max_length=100, verbose_name='Estado')
    address_zip = models.CharField(max_length=10, verbose_name='Código Postal')
    address_country = models.CharField(max_length=100, default='México')
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_clients')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_clients')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company_name}"


class ContactPerson(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.client.company_name}"