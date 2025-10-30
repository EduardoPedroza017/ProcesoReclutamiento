"""
Views para la app de Clients
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Client, ContactPerson
from .serializers import (
    ClientSerializer,
    ClientCreateSerializer,
    ContactPersonSerializer
)
from apps.accounts.permissions import IsAdminOrDirector


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de clientes"""
    
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'industry', 'assigned_to']
    search_fields = ['company_name', 'rfc', 'contact_name', 'contact_email']
    ordering_fields = ['company_name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
    def get_queryset(self):
        """Filtrar clientes según permisos"""
        user = self.request.user
        queryset = Client.objects.select_related('assigned_to', 'created_by')
        
        # Supervisores solo ven sus clientes asignados
        if user.is_supervisor:
            return queryset.filter(assigned_to=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Asignar created_by al crear"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def profiles(self, request, pk=None):
        """Obtener perfiles del cliente"""
        client = self.get_object()
        from apps.profiles.serializers import ProfileSerializer
        profiles = client.profiles.all()
        serializer = ProfileSerializer(profiles, many=True)
        return Response(serializer.data)


class ContactPersonViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de contactos"""
    
    queryset = ContactPerson.objects.all()
    serializer_class = ContactPersonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'position']
    
    def get_queryset(self):
        """Filtrar contactos por cliente si se especifica"""
        queryset = ContactPerson.objects.select_related('client')
        client_id = self.request.query_params.get('client', None)
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        return queryset