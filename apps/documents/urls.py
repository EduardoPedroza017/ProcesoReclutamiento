"""
URLs para la API de Documentos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentTemplateViewSet,
    GeneratedDocumentViewSet,
    DocumentSectionViewSet,
    DocumentLogViewSet,
)

app_name = 'documents'

# Router para los ViewSets
router = DefaultRouter()
router.register(r'templates', DocumentTemplateViewSet, basename='template')
router.register(r'generated', GeneratedDocumentViewSet, basename='generated')
router.register(r'sections', DocumentSectionViewSet, basename='section')
router.register(r'logs', DocumentLogViewSet, basename='log')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
]

# URLs disponibles:
# 
# Plantillas:
# GET    /api/documents/templates/                    - Listar plantillas
# POST   /api/documents/templates/                    - Crear plantilla
# GET    /api/documents/templates/{id}/               - Detalle de plantilla
# PUT    /api/documents/templates/{id}/               - Actualizar plantilla
# DELETE /api/documents/templates/{id}/               - Eliminar plantilla
# POST   /api/documents/templates/{id}/set_default/   - Marcar como predeterminada
# POST   /api/documents/templates/{id}/duplicate/     - Duplicar plantilla
# GET    /api/documents/templates/by_type/            - Filtrar por tipo
#
# Documentos Generados:
# GET    /api/documents/generated/                    - Listar documentos
# POST   /api/documents/generated/                    - Crear documento
# GET    /api/documents/generated/{id}/               - Detalle de documento
# PUT    /api/documents/generated/{id}/               - Actualizar documento
# DELETE /api/documents/generated/{id}/               - Eliminar documento
# GET    /api/documents/generated/{id}/download/      - Descargar PDF
# POST   /api/documents/generated/{id}/regenerate/    - Regenerar documento
# POST   /api/documents/generated/generate/           - Generar nuevo documento
# POST   /api/documents/generated/bulk_generate/      - Generación masiva
# GET    /api/documents/generated/stats/              - Estadísticas
# GET    /api/documents/generated/my_documents/       - Mis documentos
#
# Secciones:
# GET    /api/documents/sections/                     - Listar secciones
# POST   /api/documents/sections/                     - Crear sección
# GET    /api/documents/sections/{id}/                - Detalle de sección
# PUT    /api/documents/sections/{id}/                - Actualizar sección
# DELETE /api/documents/sections/{id}/                - Eliminar sección
#
# Logs:
# GET    /api/documents/logs/                         - Listar logs
# GET    /api/documents/logs/{id}/                    - Detalle de log