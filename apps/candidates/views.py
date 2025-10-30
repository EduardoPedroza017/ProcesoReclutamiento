"""
Views para Candidatos
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import csv
import io

from .models import (
    Candidate,
    CandidateProfile,
    CandidateDocument,
    CandidateStatusHistory,
    CandidateNote,
)
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateCreateUpdateSerializer,
    CandidateProfileSerializer,
    CandidateDocumentSerializer,
    CandidateStatusHistorySerializer,
    CandidateNoteSerializer,
    CandidateStatusChangeSerializer,
    CandidateAssignSerializer,
    CandidateStatsSerializer,
    CandidateMatchSerializer,
    BulkCandidateUploadSerializer,
)
from apps.accounts.permissions import IsAdminOrDirector


class CandidateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Candidatos
    
    Endpoints:
    - GET /api/candidates/ - Listar candidatos
    - POST /api/candidates/ - Crear candidato
    - GET /api/candidates/{id}/ - Detalle de candidato
    - PUT /api/candidates/{id}/ - Actualizar candidato
    - PATCH /api/candidates/{id}/ - Actualizar parcial
    - DELETE /api/candidates/{id}/ - Eliminar candidato
    
    Acciones personalizadas:
    - POST /api/candidates/{id}/change_status/ - Cambiar estado
    - POST /api/candidates/{id}/assign_to_profile/ - Asignar a perfil
    - GET /api/candidates/{id}/applications/ - Ver aplicaciones
    - GET /api/candidates/{id}/documents/ - Ver documentos
    - POST /api/candidates/{id}/upload_document/ - Subir documento
    - GET /api/candidates/{id}/notes/ - Ver notas
    - POST /api/candidates/{id}/add_note/ - Agregar nota
    - POST /api/candidates/{id}/match_with_profile/ - Matching con perfil
    - GET /api/candidates/stats/ - Estadísticas
    - GET /api/candidates/my_candidates/ - Candidatos asignados
    - POST /api/candidates/bulk_upload/ - Carga masiva CSV
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    filterset_fields = {
        'status': ['exact', 'in'],
        'education_level': ['exact', 'icontains'],
        'years_of_experience': ['exact', 'gte', 'lte'],
        'city': ['exact', 'icontains'],
        'state': ['exact', 'icontains'],
        'country': ['exact'],
        'assigned_to': ['exact'],
        'created_at': ['gte', 'lte'],
    }
    
    # Búsqueda
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'current_position',
        'current_company',
        'city',
        'state',
    ]
    
    # Ordenamiento
    ordering_fields = [
        'created_at',
        'updated_at',
        'last_name',
        'first_name',
        'years_of_experience',
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Retorna el queryset según el rol del usuario:
        - Admin/Director: Ve todos los candidatos
        - Supervisor: Solo ve los candidatos asignados a él
        """
        user = self.request.user
        queryset = Candidate.objects.select_related(
            'assigned_to',
            'created_by'
        ).prefetch_related(
            'documents',
            'candidate_profiles',
            'status_history',
            'notes'
        )
        
        # Supervisores solo ven sus candidatos asignados
        if user.role == 'supervisor':
            queryset = queryset.filter(assigned_to=user)
        
        return queryset
    
    def get_serializer_class(self):
        """Retorna el serializer según la acción"""
        if self.action == 'list':
            return CandidateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CandidateCreateUpdateSerializer
        return CandidateDetailSerializer
    
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
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Cambiar el estado de un candidato
        
        Body:
        {
            "status": "qualified",
            "notes": "Notas del cambio (opcional)"
        }
        """
        candidate = self.get_object()
        serializer = CandidateStatusChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            old_status = candidate.status
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            # Actualizar estado
            candidate.status = new_status
            candidate.save()
            
            # Registrar en historial
            CandidateStatusHistory.objects.create(
                candidate=candidate,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                notes=notes
            )
            
            return Response({
                'message': f'Estado cambiado a {candidate.get_status_display()}',
                'candidate': CandidateDetailSerializer(candidate, context={'request': request}).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign_to_profile(self, request, pk=None):
        """
        Asignar candidato a un perfil
        
        Body:
        {
            "profile_id": 1,
            "notes": "Notas de la asignación (opcional)"
        }
        """
        candidate = self.get_object()
        serializer = CandidateAssignSerializer(data=request.data)
        
        if serializer.is_valid():
            profile_id = serializer.validated_data['profile_id']
            notes = serializer.validated_data.get('notes', '')
            
            # Verificar si ya existe la aplicación
            existing = CandidateProfile.objects.filter(
                candidate=candidate,
                profile_id=profile_id
            ).first()
            
            if existing:
                return Response(
                    {'error': 'El candidato ya está asignado a este perfil'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear la aplicación
            application = CandidateProfile.objects.create(
                candidate=candidate,
                profile_id=profile_id,
                notes=notes
            )
            
            return Response({
                'message': 'Candidato asignado exitosamente',
                'application': CandidateProfileSerializer(application).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """Obtener todas las aplicaciones del candidato"""
        candidate = self.get_object()
        applications = candidate.candidate_profiles.all()
        serializer = CandidateProfileSerializer(applications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Obtener todos los documentos del candidato"""
        candidate = self.get_object()
        documents = candidate.documents.all()
        serializer = CandidateDocumentSerializer(
            documents,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """
        Subir un documento al candidato
        
        Form-data:
        - document_type: Tipo de documento
        - file: Archivo
        - description: Descripción (opcional)
        """
        candidate = self.get_object()
        
        serializer = CandidateDocumentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Guardar nombre original del archivo
            file_obj = request.FILES.get('file')
            original_filename = file_obj.name if file_obj else ''
            
            serializer.save(
                candidate=candidate,
                uploaded_by=request.user,
                original_filename=original_filename
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def notes(self, request, pk=None):
        """Obtener todas las notas del candidato"""
        candidate = self.get_object()
        notes = candidate.notes.all()
        serializer = CandidateNoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """
        Agregar una nota al candidato
        
        Body:
        {
            "note": "Texto de la nota",
            "is_important": false
        }
        """
        candidate = self.get_object()
        serializer = CandidateNoteSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                candidate=candidate,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def match_with_profile(self, request, pk=None):
        """
        Calcular matching de candidato con un perfil usando IA
        
        Body:
        {
            "profile_id": 1
        }
        
        TODO: Integrar con Claude API para análisis
        """
        candidate = self.get_object()
        serializer = CandidateMatchSerializer(data=request.data)
        
        if serializer.is_valid():
            profile_id = serializer.validated_data['profile_id']
            
            # TODO: Aquí iría la lógica de matching con IA
            # Por ahora retornamos un placeholder
            match_score = 75  # Placeholder
            
            return Response({
                'candidate_id': candidate.id,
                'profile_id': profile_id,
                'match_score': match_score,
                'message': 'Matching calculado (placeholder - integrar con IA)'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Obtener estadísticas generales de candidatos
        """
        queryset = self.get_queryset()
        
        # Total de candidatos
        total_candidates = queryset.count()
        
        # Por estado
        by_status = {}
        for status_code, status_name in Candidate.STATUS_CHOICES:
            count = queryset.filter(status=status_code).count()
            by_status[status_code] = {
                'count': count,
                'display': status_name
            }
        
        # Por experiencia
        by_experience = {
            '0-2': queryset.filter(years_of_experience__lt=3).count(),
            '3-5': queryset.filter(years_of_experience__gte=3, years_of_experience__lte=5).count(),
            '6-10': queryset.filter(years_of_experience__gte=6, years_of_experience__lte=10).count(),
            '10+': queryset.filter(years_of_experience__gt=10).count(),
        }
        
        # Aplicaciones activas
        active_applications = CandidateProfile.objects.filter(
            candidate__in=queryset
        ).exclude(
            status__in=['rejected', 'withdrawn']
        ).count()
        
        # Nuevos este mes
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = queryset.filter(created_at__gte=start_of_month).count()
        
        # Contratados este mes
        hired_this_month = queryset.filter(
            status=Candidate.STATUS_HIRED,
            updated_at__gte=start_of_month
        ).count()
        
        stats_data = {
            'total_candidates': total_candidates,
            'by_status': by_status,
            'by_experience': by_experience,
            'active_applications': active_applications,
            'new_this_month': new_this_month,
            'hired_this_month': hired_this_month,
        }
        
        serializer = CandidateStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_candidates(self, request):
        """Obtener candidatos asignados al usuario actual"""
        candidates = self.get_queryset().filter(assigned_to=request.user)
        
        page = self.paginate_queryset(candidates)
        if page is not None:
            serializer = CandidateListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CandidateListSerializer(candidates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Carga masiva de candidatos desde archivo CSV
        
        Form-data:
        - file: Archivo CSV
        
        Formato CSV esperado:
        first_name,last_name,email,phone,city,state,current_position,years_of_experience,education_level
        """
        serializer = BulkCandidateUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Verificar si ya existe el email
                if Candidate.objects.filter(email=row['email']).exists():
                    errors.append(f"Fila {row_num}: Email {row['email']} ya existe")
                    continue
                
                # Crear candidato
                Candidate.objects.create(
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row['email'],
                    phone=row.get('phone', ''),
                    city=row.get('city', ''),
                    state=row.get('state', ''),
                    current_position=row.get('current_position', ''),
                    years_of_experience=int(row.get('years_of_experience', 0)),
                    education_level=row.get('education_level', ''),
                    created_by=request.user
                )
                created_count += 1
                
            except Exception as e:
                errors.append(f"Fila {row_num}: {str(e)}")
        
        return Response({
            'message': f'{created_count} candidatos creados exitosamente',
            'created': created_count,
            'errors': errors
        })


class CandidateProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de aplicaciones de candidatos a perfiles
    """
    queryset = CandidateProfile.objects.select_related(
        'candidate',
        'profile'
    ).all()
    serializer_class = CandidateProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'candidate': ['exact'],
        'profile': ['exact'],
        'status': ['exact', 'in'],
        'applied_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['applied_at', 'match_percentage', 'overall_rating']
    ordering = ['-applied_at']


class CandidateDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos de candidatos
    """
    queryset = CandidateDocument.objects.select_related(
        'candidate',
        'uploaded_by'
    ).all()
    serializer_class = CandidateDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'candidate': ['exact'],
        'document_type': ['exact'],
        'uploaded_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        """Al crear, asigna el usuario que subió y el nombre original"""
        file_obj = self.request.FILES.get('file')
        original_filename = file_obj.name if file_obj else ''
        serializer.save(
            uploaded_by=self.request.user,
            original_filename=original_filename
        )


class CandidateNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de notas de candidatos
    """
    queryset = CandidateNote.objects.select_related(
        'candidate',
        'created_by'
    ).all()
    serializer_class = CandidateNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = {
        'candidate': ['exact'],
        'is_important': ['exact'],
        'created_at': ['gte', 'lte'],
    }
    
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Al crear, asigna el usuario que creó la nota"""
        serializer.save(created_by=self.request.user)