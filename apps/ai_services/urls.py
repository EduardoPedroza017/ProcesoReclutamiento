"""
URLs para Servicios de IA
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CVAnalysisViewSet,
    MatchingViewSet,
    ProfileGenerationViewSet,
    AILogViewSet,
    SummarizationViewSet,
)

app_name = 'ai_services'

# Router
router = DefaultRouter()
router.register(r'cv-analysis', CVAnalysisViewSet, basename='cv-analysis')
router.register(r'matching', MatchingViewSet, basename='matching')
router.register(r'profile-generation', ProfileGenerationViewSet, basename='profile-generation')
router.register(r'logs', AILogViewSet, basename='ai-log')
router.register(r'summarize', SummarizationViewSet, basename='summarize')

urlpatterns = [
    path('', include(router.urls)),
]