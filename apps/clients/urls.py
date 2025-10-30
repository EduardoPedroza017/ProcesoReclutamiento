"""
URLs para la app de Clients
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ContactPersonViewSet

router = DefaultRouter()
router.register(r'', ClientViewSet, basename='client')
router.register(r'contacts', ContactPersonViewSet, basename='contact')

app_name = 'clients'

urlpatterns = [
    path('', include(router.urls)),
]