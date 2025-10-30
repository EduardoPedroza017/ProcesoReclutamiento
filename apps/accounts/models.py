"""
Modelos de Usuario y Autenticación
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Crear y guardar un usuario regular"""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Crear y guardar un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de Usuario personalizado con roles
    """
    
    # Roles del sistema
    ADMIN = 'admin'
    DIRECTOR = 'director'
    SUPERVISOR = 'supervisor'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrador'),
        (DIRECTOR, 'Director de Reclutamiento'),
        (SUPERVISOR, 'Supervisor'),
    ]
    
    # Campos personalizados
    username = None  # No usaremos username, solo email
    email = models.EmailField(_('email'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=SUPERVISOR,
        verbose_name='Rol'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    @property
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.role == self.ADMIN
    
    @property
    def is_director(self):
        """Verifica si el usuario es director"""
        return self.role == self.DIRECTOR
    
    @property
    def is_supervisor(self):
        """Verifica si el usuario es supervisor"""
        return self.role == self.SUPERVISOR
    
    def has_permission(self, required_role):
        """
        Verifica si el usuario tiene el permiso requerido
        Jerarquía: ADMIN > DIRECTOR > SUPERVISOR
        """
        role_hierarchy = {
            self.ADMIN: 3,
            self.DIRECTOR: 2,
            self.SUPERVISOR: 1,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)


class UserActivity(models.Model):
    """
    Modelo para registrar actividad de usuarios
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Usuario'
    )
    action = models.CharField(
        max_length=100,
        verbose_name='Acción'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora'
    )
    
    class Meta:
        verbose_name = 'Actividad de Usuario'
        verbose_name_plural = 'Actividades de Usuarios'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"