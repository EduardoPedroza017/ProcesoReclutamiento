"""
Views para la gestión de Documentos
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django_filters.rest_framework import DjangoFilterBackend
import logging

from .models import (
    DocumentTemplate,
    GeneratedDocument,
    DocumentSection,
    DocumentLog
)
from .serializers import (
    DocumentTemplateSerializer,
    DocumentTemplateSummarySerializer,
    GeneratedDocumentSerializer,
    GeneratedDocumentSummarySerializer,
    GenerateDocumentRequestSerializer,
    DocumentSectionSerializer,
    DocumentLogSerializer,
    BulkGenerateDocumentsSerializer,
    DocumentStatsSerializer,
)
from .tasks import generate_document_task, generate_bulk_documents_task
from apps.profiles.models import Profile
from apps.candidates.models import Candidate
from apps.accounts.permissions import IsAdminOrDirector, IsAdminUser

logger = logging.getLogger(__name__)


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de plantillas de documentos
    
    Endpoints:
    - GET /api/documents/templates/ - Listar plantillas
    - POST /api/documents/templates/ - Crear plantilla
    - GET /api/documents/templates/{id}/ - Detalle de plantilla
    - PUT /api/documents/templates/{id}/ - Actualizar plantilla
    - DELETE /api/documents/templates/{id}/ - Eliminar plantilla
    - POST /api/documents/templates/{id}/set_default/ - Marcar como predeterminada
    - POST /api/documents/templates/{id}/duplicate/ - Duplicar plantilla
    - GET /api/documents/templates/by_type/ - Filtrar por tipo
    """
    queryset = DocumentTemplate.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'document_type']
    ordering = ['document_type', 'name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentTemplateSummarySerializer
        return DocumentTemplateSerializer
    
    def perform_create(self, serializer):
        """Guarda el usuario que creó la plantilla"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Marca la plantilla como predeterminada para su tipo"""
        template = self.get_object()
        template.is_default = True
        template.save()
        
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplica una plantilla existente"""
        original = self.get_object()
        
        # Crear copia
        duplicate = DocumentTemplate.objects.create(
            name=f"{original.name} (Copia)",
            description=original.description,
            document_type=original.document_type,
            header_text=original.header_text,
            footer_text=original.footer_text,
            style_config=original.style_config,
            sections=original.sections,
            is_active=True,
            is_default=False,
            created_by=request.user
        )
        
        # Copiar logo si existe
        if original.logo:
            duplicate.logo = original.logo
            duplicate.save()
        
        serializer = self.get_serializer(duplicate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Filtra plantillas por tipo de documento"""
        doc_type = request.query_params.get('type')
        if not doc_type:
            return Response(
                {"error": "Debe proporcionar el parámetro 'type'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        templates = self.queryset.filter(document_type=doc_type, is_active=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos generados
    
    Endpoints:
    - GET /api/documents/ - Listar documentos
    - POST /api/documents/ - Generar nuevo documento
    - GET /api/documents/{id}/ - Detalle de documento
    - PUT /api/documents/{id}/ - Actualizar documento
    - DELETE /api/documents/{id}/ - Eliminar documento
    - GET /api/documents/{id}/download/ - Descargar documento
    - POST /api/documents/{id}/regenerate/ - Regenerar documento
    - POST /api/documents/generate/ - Generar documento con datos personalizados
    - POST /api/documents/bulk_generate/ - Generar múltiples documentos
    - GET /api/documents/stats/ - Estadísticas de documentos
    - GET /api/documents/my_documents/ - Documentos del usuario actual
    """
    queryset = GeneratedDocument.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'template', 'profile', 'candidate', 'generated_by']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'status', 'download_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'my_documents':
            return GeneratedDocumentSummarySerializer
        return GeneratedDocumentSerializer
    
    def get_queryset(self):
        """Filtra documentos según el rol del usuario"""
        user = self.request.user
        queryset = GeneratedDocument.objects.all()
        
        # Los supervisores solo ven sus documentos
        if user.role == 'supervisor':
            queryset = queryset.filter(generated_by=user)
        
        return queryset.select_related(
            'template', 'profile', 'candidate', 'generated_by'
        )
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Genera un nuevo documento PDF
        
        Body:
        {
            "title": "Perfil de Reclutamiento",
            "description": "Descripción opcional",
            "template_id": 1,
            "profile_id": 5,
            "async_generation": true
        }
        """
        serializer = GenerateDocumentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Obtener objetos relacionados
        template = None
        if data.get('template_id'):
            template = get_object_or_404(DocumentTemplate, id=data['template_id'])
        
        profile = None
        if data.get('profile_id'):
            profile = get_object_or_404(Profile, id=data['profile_id'])
        
        candidate = None
        if data.get('candidate_id'):
            candidate = get_object_or_404(Candidate, id=data['candidate_id'])
        
        # Crear el documento
        document = GeneratedDocument.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            template=template,
            profile=profile,
            candidate=candidate,
            custom_data=data.get('custom_data', {}),
            status=GeneratedDocument.STATUS_PENDING,
            generated_by=request.user
        )
        
        # Generar el PDF
        if data.get('async_generation', True):
            # Generar de forma asíncrona con Celery
            generate_document_task.delay(document.id)
            message = "El documento se está generando en segundo plano"
        else:
            # Generar de forma síncrona
            from .tasks import generate_document_sync
            generate_document_sync(document.id)
            message = "Documento generado exitosamente"
        
        # Log de la acción
        DocumentLog.objects.create(
            document=document,
            action=DocumentLog.ACTION_GENERATED,
            user=request.user,
            details={'async': data.get('async_generation', True)},
            ip_address=self.get_client_ip(request)
        )
        
        doc_serializer = GeneratedDocumentSerializer(document, context={'request': request})
        return Response({
            'message': message,
            'document': doc_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descarga el documento PDF"""
        document = self.get_object()
        
        if not document.file:
            return Response(
                {"error": "El documento aún no ha sido generado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if document.status != GeneratedDocument.STATUS_COMPLETED:
            return Response(
                {"error": f"El documento está en estado: {document.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Incrementar contador de descargas
        document.increment_download_count()
        
        # Log de descarga
        DocumentLog.objects.create(
            document=document,
            action=DocumentLog.ACTION_DOWNLOADED,
            user=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        # Retornar el archivo
        response = FileResponse(
            document.file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
        return response
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenera un documento existente creando una nueva versión"""
        document = self.get_object()
        
        # Crear nueva versión
        new_document = document.create_new_version(request.user)
        
        # Generar el PDF asíncronamente
        generate_document_task.delay(new_document.id)
        
        # Log de la acción
        DocumentLog.objects.create(
            document=new_document,
            action=DocumentLog.ACTION_REGENERATED,
            user=request.user,
            details={'original_document_id': document.id},
            ip_address=self.get_client_ip(request)
        )
        
        serializer = GeneratedDocumentSerializer(new_document, context={'request': request})
        return Response({
            'message': 'El documento se está regenerando',
            'document': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_generate(self, request):
        """
        Genera múltiples documentos de forma masiva
        
        Body:
        {
            "template_id": 1,
            "profile_ids": [1, 2, 3, 4],
            "candidate_ids": [10, 11, 12]
        }
        """
        serializer = BulkGenerateDocumentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        template = get_object_or_404(DocumentTemplate, id=data['template_id'])
        
        documents_created = []
        
        # Generar documentos para perfiles
        if data.get('profile_ids'):
            for profile_id in data['profile_ids']:
                profile = get_object_or_404(Profile, id=profile_id)
                document = GeneratedDocument.objects.create(
                    title=f"{template.name} - {profile.position_title}",
                    template=template,
                    profile=profile,
                    status=GeneratedDocument.STATUS_PENDING,
                    generated_by=request.user
                )
                documents_created.append(document.id)
        
        # Generar documentos para candidatos
        if data.get('candidate_ids'):
            for candidate_id in data['candidate_ids']:
                candidate = get_object_or_404(Candidate, id=candidate_id)
                document = GeneratedDocument.objects.create(
                    title=f"{template.name} - {candidate.get_full_name()}",
                    template=template,
                    candidate=candidate,
                    status=GeneratedDocument.STATUS_PENDING,
                    generated_by=request.user
                )
                documents_created.append(document.id)
        
        # Generar los PDFs de forma asíncrona
        generate_bulk_documents_task.delay(documents_created)
        
        return Response({
            'message': f'Se están generando {len(documents_created)} documentos',
            'document_ids': documents_created
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estadísticas de documentos"""
        queryset = self.get_queryset()
        
        # Estadísticas generales
        stats = {
            'total_documents': queryset.count(),
            'by_status': dict(queryset.values_list('status').annotate(count=Count('id'))),
            'by_type': dict(
                queryset.exclude(template=None)
                .values_list('template__document_type')
                .annotate(count=Count('id'))
            ),
            'total_downloads': queryset.aggregate(total=Avg('download_count'))['total'] or 0,
            'average_generation_time': queryset.filter(
                status=GeneratedDocument.STATUS_COMPLETED
            ).aggregate(avg=Avg('generation_time'))['avg'] or 0,
        }
        
        # Documentos recientes
        recent_docs = queryset.order_by('-created_at')[:5]
        stats['recent_documents'] = GeneratedDocumentSummarySerializer(
            recent_docs,
            many=True,
            context={'request': request}
        ).data
        
        serializer = DocumentStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_documents(self, request):
        """Retorna los documentos del usuario actual"""
        documents = self.get_queryset().filter(generated_by=request.user)
        
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentSectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de secciones de documentos
    
    Endpoints:
    - GET /api/documents/sections/ - Listar secciones
    - POST /api/documents/sections/ - Crear sección
    - GET /api/documents/sections/{id}/ - Detalle de sección
    - PUT /api/documents/sections/{id}/ - Actualizar sección
    - DELETE /api/documents/sections/{id}/ - Eliminar sección
    """
    queryset = DocumentSection.objects.all()
    serializer_class = DocumentSectionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDirector]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['order', 'name']
    ordering = ['order', 'name']


class DocumentLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para logs de documentos
    
    Endpoints:
    - GET /api/documents/logs/ - Listar logs
    - GET /api/documents/logs/{id}/ - Detalle de log
    """
    queryset = DocumentLog.objects.all()
    serializer_class = DocumentLogSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDirector]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'action', 'user']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtra logs según el rol del usuario"""
        user = self.request.user
        queryset = DocumentLog.objects.all()
        
        # Los supervisores solo ven logs de sus documentos
        if user.role == 'supervisor':
            queryset = queryset.filter(document__generated_by=user)
        
        return queryset.select_related('document', 'user')