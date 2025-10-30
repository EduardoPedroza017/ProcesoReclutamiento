"""
URLs principales del proyecto
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Auth
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Endpoints
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/clients/', include('apps.clients.urls')),
    path('api/profiles/', include('apps.profiles.urls')),
    path('api/candidates/', include('apps.candidates.urls')),
    path('api/evaluations/', include('apps.evaluations.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/', include('apps.profiles.urls')),
    path('api/', include('apps.profiles.urls')),
    path('api/', include('apps.candidates.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar el admin
admin.site.site_header = "Administración - Sistema de Reclutamiento"
admin.site.site_title = "Sistema de Reclutamiento"
admin.site.index_title = "Panel de Control"