"""
URLs para Perfiles de Reclutamiento
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet,
    ProfileStatusHistoryViewSet,
    ProfileDocumentViewSet,
)

app_name = 'profiles'

# Crear router
router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'profiles/history', ProfileStatusHistoryViewSet, basename='profile-history')
router.register(r'profiles/documents', ProfileDocumentViewSet, basename='profile-document')

urlpatterns = [
    path('', include(router.urls)),
]