"""
Permisos personalizados para la app de Accounts
Incluye permisos originales + permisos para módulo de evaluations
"""
from rest_framework import permissions


# ========================================
# PERMISOS ORIGINALES DEL PROYECTO
# ========================================

class IsAdminOrDirector(permissions.BasePermission):
    """
    Permiso para solo Admins y Directores
    """
    message = 'Solo administradores y directores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_director)
        )


class IsAdmin(permissions.BasePermission):
    """
    Permiso solo para Administradores
    """
    message = 'Solo administradores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsDirector(permissions.BasePermission):
    """
    Permiso solo para Directores
    """
    message = 'Solo directores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_director
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso para el propietario del objeto o administradores
    """
    message = 'Solo el propietario o un administrador pueden realizar esta acción.'
    
    def has_object_permission(self, request, view, obj):
        # Admins pueden todo
        if request.user.is_admin:
            return True
        
        # El objeto debe tener un atributo 'user' o ser un User
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Si el objeto ES un User
        return obj == request.user


class IsDirectorOrAbove(permissions.BasePermission):
    """
    Permiso para Directores y Administradores
    """
    message = 'Se requiere rol de director o superior.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_director)
        )


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


# ========================================
# PERMISOS PARA EVALUATIONS (NUEVOS)
# Adaptados para usar is_admin, is_director, is_supervisor
# ========================================

class IsAdminUser(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol 'admin'
    (Usado en apps.evaluations)
    """
    message = 'Solo administradores pueden realizar esta acción.'
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsSupervisorOrAbove(permissions.BasePermission):
    """
    Permiso que permite acceso a usuarios con rol 'supervisor', 'director' o 'admin'
    (Usado en apps.evaluations)
    """
    message = 'Se requiere rol de supervisor o superior.'
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Verificar si tiene alguno de los roles
        return (
            request.user.is_admin or 
            request.user.is_director or
            getattr(request.user, 'is_supervisor', False)
        )


# ========================================
# PERMISOS GENÉRICOS ADICIONALES
# ========================================

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite editar solo al dueño del objeto
    Otros usuarios pueden solo leer
    """
    message = 'Solo el propietario puede editar este objeto.'
    
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura permitidos para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el dueño
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user


class IsOwner(permissions.BasePermission):
    """
    Permiso que solo permite acceso al dueño del objeto
    """
    message = 'Solo el propietario puede acceder a este objeto.'
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user