"""
Permisos personalizados para el sistema de reclutamiento
Define permisos basados en roles de usuario
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol 'admin'
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'admin'
        )


class IsDirectorOrAbove(permissions.BasePermission):
    """
    Permiso que permite acceso a usuarios con rol 'director' o 'admin'
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role in ['director', 'admin']
        )


class IsSupervisorOrAbove(permissions.BasePermission):
    """
    Permiso que permite acceso a usuarios con rol 'supervisor', 'director' o 'admin'
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role in ['supervisor', 'director', 'admin']
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso que permite editar solo al dueño del objeto
    Otros usuarios pueden solo leer
    """
    def has_object_permission(self, request, view, obj):
        # Permisos de lectura permitidos para cualquier request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permisos de escritura solo para el dueño
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Permiso que solo permite acceso al dueño del objeto
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user