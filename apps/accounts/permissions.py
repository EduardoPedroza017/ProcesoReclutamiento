"""
Permisos personalizados para la app de Accounts
"""
from rest_framework import permissions


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
            request.user.has_permission(request.user.DIRECTOR)
        )


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS