"""
Views para Perfiles de Reclutamiento
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta

from .models import Profile, ProfileStatusHistory, ProfileDocument
from .serializers import (
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileCreateUpdateSerializer,
    ProfileStatusHistorySerializer,
    ProfileDocumentSerializer,
    ProfileApprovalSerializer,
    ProfileStatusChangeSerializer,
    ProfileStatsSerializer,
)
from apps.accounts.permissions import IsAdmin, IsDirector, IsAdminOrDirector


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Perfiles de Reclutamiento
    
    Endpoints:
    - GET /api/profiles/ - Listar perfiles
    - POST /api/profiles/ - Crear perfil
    - GET /api/profiles/{id}/ - Detalle de perfil
    - PUT /api/profiles/{id}/ - Actualizar perfil completo
    - PATCH /api/profiles/{id}/ - Actualizar parcial
    - DELETE /api/profiles/{id}/ - Eliminar perfil
    
    Acciones personalizadas:
    - POST /api/profiles/{id}/approve/ - Aprobar/rechazar perfil
    - POST /api/profiles/{id}/change_status/ - Cambiar estado
    - GET /api/profiles/{id}/history/ - Historial de estados
    - GET /api/profiles/{id}/documents/ - Documentos del perfil
    - POST /api/profiles/{id}/upload_document/ - Subir documento
    - GET /api/profiles/stats/ - Estadísticas generales
    - GET /api/profiles/my_profiles/ - Perfiles asignados al usuario
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    filterset_fields = {
        'status': ['exact', 'in'],
        'priority': ['exact', 'in'],
        'service_type': ['exact'],
        'client': ['exact'],
        'assigned_to': ['exact'],
        'client_approved': ['exact'],
        'is_remote': ['exact'],
        'is_hybrid': ['exact'],
        'created_at': ['gte', 'lte'],
        'location_city': ['exact', 'icontains'],
        'location_state': ['exact', 'icontains'],
    }
    
    # Búsqueda
    search_fields = [
        'position_title',
        'position_description',
        'department',
        'location_city',
        'location_state',
        'client__company_name',
    ]
    
    # Ordenamiento
    ordering_fields = [
        'created_at',
        'updated_at',
        'priority',
        'position_title',
        'deadline',
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna el queryset según el rol del usuario:
        - Admin: Ve todos los perfiles
        - Director: Ve todos los perfiles
        - Supervisor: Solo ve los perfiles asignados a él
        """
        user = self.request.user
        queryset = Profile.objects.select_related(
            'client',
            'assigned_to',
            'created_by'
        ).prefetch_related(
            'status_history',
            'documents'
        )
        
        # Supervisores solo ven sus perfiles asignados
        if user.role == 'supervisor':
            queryset = queryset.filter(assigned_to=user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna el serializer según la acción"""
        if self.action == 'list':
            return ProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProfileCreateUpdateSerializer
        return ProfileDetailSerializer
    
    def get_permissions(self):
        """Define permisos según la acción"""
        if self.action in ['create', 'destroy']:
            # Solo Admin y Director pueden crear/eliminar
            permission_classes = [IsAuthenticated, IsAdminOrDirector]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Al crear, asigna el usuario creador"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Al actualizar, verifica cambios de estado"""
        instance = self.get_object()
        old_status = instance.status
        
        # Guarda el perfil
        profile = serializer.save()
        
        # Si cambió el estado, ya se registró en el serializer
        # Aquí podemos agregar notificaciones u otras lógicas
        new_status = profile.status
        if old_status != new_status:
            # TODO: Enviar notificación de cambio de estado
            pass
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """
        Aprobar o rechazar un perfil por el cliente
        
        Body:
        {
            "approved": true/false,
            "feedback": "Comentarios del cliente (opcional si approved=true, requerido si false)"
        }
        """
        profile = self.get_object()
        serializer = ProfileApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            approved = serializer.validated_data['approved']
            feedback = serializer.validated_data.get('feedback', '')
            
            # Actualizar el perfil
            profile.client_approved = approved
            profile.client_feedback = feedback
            
            if approved:
                profile.status = Profile.STATUS_APPROVED
                profile.client_approval_date = timezone.now()
                message = "Perfil aprobado exitosamente"
            else:
                profile.status = Profile.STATUS_PENDING
                message = "Perfil rechazado. Se requieren cambios"
            
            profile.save()
            
            # Registrar en historial
            ProfileStatusHistory.objects.create(
                profile=profile,
                from_status=Profile.STATUS_PENDING,
                to_status=profile.status,
                changed_by=request.user,
                notes=f"Cliente {'aprobó' if approved else 'rechazó'} el perfil. {feedback}"
            )
            
            # TODO: Enviar notificación al equipo
            
            return Response({
                'message': message,
                'profile': ProfileDetailSerializer(profile, context={'request': request}).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_status(self, request, pk=None):
        """
        Cambiar el estado de un perfil
        
        Body:
        {
            "status": "in_progress",
            "notes": "Notas del cambio (opcional)"
        }
        """
        profile = self.get_object()
        serializer = ProfileStatusChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            old_status = profile.status
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            # Actualizar estado
            profile.status = new_status
            
            # Si se completa, registrar fecha
            if new_status == Profile.STATUS_COMPLETED and not profile.completed_at:
                profile.completed_at = timezone.now()
            
            profile.save()
            
            # Registrar en historial
            ProfileStatusHistory.objects.create(
                profile=profile,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                notes=notes
            )
            
            return Response({
                'message': f'Estado cambiado a {profile.get_status_display()}',
                'profile': ProfileDetailSerializer(profile, context={'request': request}).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Obtener el historial de cambios de estado del perfil"""
        profile = self.get_object()
        history = profile.status_history.all()
        serializer = ProfileStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Obtener todos los documentos del perfil"""
        profile = self.get_object()
        documents = profile.documents.all()
        serializer = ProfileDocumentSerializer(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_document(self, request, pk=None):
        """
        Subir un documento al perfil
        
        Form-data:
        - document_type: Tipo de documento
        - file: Archivo
        - description: Descripción (opcional)
        """
        profile = self.get_object()
        
        serializer = ProfileDocumentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(
                profile=profile,
                uploaded_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Obtener estadísticas generales de perfiles
        
        Retorna:
        - Total de perfiles
        - Perfiles por estado
        - Perfiles por prioridad
        - Perfiles por tipo de servicio
        - Perfiles urgentes
        - Perfiles aprobados
        - Perfiles completados este mes
        """
        queryset = self.get_queryset()
        
        # Total de perfiles
        total_profiles = queryset.count()
        
        # Por estado
        by_status = {}
        for status_code, status_name in Profile.STATUS_CHOICES:
            count = queryset.filter(status=status_code).count()
            by_status[status_code] = {
                'count': count,
                'display': status_name
            }
        
        # Por prioridad
        by_priority = {}
        for priority_code, priority_name in [
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ]:
            count = queryset.filter(priority=priority_code).count()
            by_priority[priority_code] = {
                'count': count,
                'display': priority_name
            }
        
        # Por tipo de servicio
        by_service_type = {}
        for service_code, service_name in Profile.SERVICE_CHOICES:
            count = queryset.filter(service_type=service_code).count()
            by_service_type[service_code] = {
                'count': count,
                'display': service_name
            }
        
        # Perfiles urgentes
        urgent_profiles = queryset.filter(priority='urgent').count()
        
        # Perfiles aprobados
        approved_profiles = queryset.filter(client_approved=True).count()
        
        # Completados este mes
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completed_this_month = queryset.filter(
            status=Profile.STATUS_COMPLETED,
            completed_at__gte=start_of_month
        ).count()
        
        stats_data = {
            'total_profiles': total_profiles,
            'by_status': by_status,
            'by_priority': by_priority,
            'by_service_type': by_service_type,
            'urgent_profiles': urgent_profiles,
            'approved_profiles': approved_profiles,
            'completed_this_month': completed_this_month,
        }
        
        serializer = ProfileStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_profiles(self, request):
        """Obtener perfiles asignados al usuario actual"""
        profiles = self.get_queryset().filter(assigned_to=request.user)
        
        page = self.paginate_queryset(profiles)
        if page is not None:
            serializer = ProfileListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class ProfileStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para historial de estados
    
    Endpoints:
    - GET /api/profiles/history/ - Listar historial
    - GET /api/profiles/history/{id}/ - Detalle de historial
    """
    queryset = ProfileStatusHistory.objects.select_related(
        'profile',
        'changed_by'
    ).all()
    serializer_class = ProfileStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'profile': ['exact'],
        'from_status': ['exact'],
        'to_status': ['exact'],
        'timestamp': ['gte', 'lte'],
    }
    
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class ProfileDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos de perfiles
    
    Endpoints:
    - GET /api/profiles/documents/ - Listar documentos
    - POST /api/profiles/documents/ - Subir documento
    - GET /api/profiles/documents/{id}/ - Detalle de documento
    - DELETE /api/profiles/documents/{id}/ - Eliminar documento
    """
    queryset = ProfileDocument.objects.select_related(
        'profile',
        'uploaded_by'
    ).all()
    serializer_class = ProfileDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'profile': ['exact'],
        'document_type': ['exact'],
        'uploaded_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        """Al crear, asigna el usuario que subió el documento"""
        serializer.save(uploaded_by=self.request.user)