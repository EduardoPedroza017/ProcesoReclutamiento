"""
URLs para Candidatos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CandidateViewSet,
    CandidateProfileViewSet,
    CandidateDocumentViewSet,
    CandidateNoteViewSet,
)

app_name = 'candidates'

# Crear router
router = DefaultRouter()
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'applications', CandidateProfileViewSet, basename='candidate-application')
router.register(r'documents', CandidateDocumentViewSet, basename='candidate-document')
router.register(r'notes', CandidateNoteViewSet, basename='candidate-note')

urlpatterns = [
    path('', include(router.urls)),
]