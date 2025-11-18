"""
URLs de prueba simplificadas para testing del login
"""
from django.contrib import admin
from django.urls import path
from apps.accounts.views import CustomTokenObtainPairView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Auth - solo para testing
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]