"""
Views para la app de Accounts
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import UserActivity
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserActivitySerializer
)
from .permissions import IsAdminOrDirector, IsOwnerOrAdmin

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """
        Permisos personalizados por acción
        - list, retrieve: Usuarios autenticados
        - create, destroy: Solo admins y directores
        - update: Owner o admin
        """
        if self.action in ['create', 'destroy']:
            return [IsAdminOrDirector()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """Filtrar usuarios según permisos"""
        user = self.request.user
        
        # Admins y directores ven todos
        if user.is_admin or user.is_director:
            return User.objects.all()
        
        # Supervisores solo se ven a sí mismos
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambiar contraseña del usuario actual"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Registrar actividad
        UserActivity.objects.create(
            user=user,
            action='change_password',
            description='Cambió su contraseña',
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'Contraseña actualizada exitosamente.'
        })
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Obtener actividades de un usuario"""
        user = self.get_object()
        
        # Solo admins, directores o el propio usuario pueden ver actividades
        if not (request.user.is_admin or 
                request.user.is_director or 
                request.user.id == user.id):
            return Response(
                {'error': 'No tiene permisos para ver estas actividades.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        activities = user.activities.all()[:50]  # Últimas 50 actividades
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def perform_create(self, serializer):
        """Registrar actividad al crear usuario"""
        user = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            action='create_user',
            description=f'Creó el usuario {user.email}',
            ip_address=self.get_client_ip(self.request)
        )
    
    def perform_update(self, serializer):
        """Registrar actividad al actualizar usuario"""
        user = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            action='update_user',
            description=f'Actualizó el usuario {user.email}',
            ip_address=self.get_client_ip(self.request)
        )
    
    def perform_destroy(self, instance):
        """Registrar actividad al eliminar usuario (soft delete)"""
        instance.is_active = False
        instance.save()
        
        UserActivity.objects.create(
            user=self.request.user,
            action='delete_user',
            description=f'Desactivó el usuario {instance.email}',
            ip_address=self.get_client_ip(self.request)
        )


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para actividades de usuarios
    Solo admins y directores pueden ver todas las actividades
    """
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [IsAdminOrDirector]
    
    def get_queryset(self):
        """Filtrar por usuario si se especifica"""
        queryset = UserActivity.objects.all()
        user_id = self.request.query_params.get('user', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.select_related('user')