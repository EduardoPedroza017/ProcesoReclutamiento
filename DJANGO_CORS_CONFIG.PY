# ====================================================================
# CONFIGURACIÓN CORS PARA DJANGO
# Agrega estas líneas a tu archivo config/settings.py
# ====================================================================

"""
Este archivo contiene las configuraciones necesarias para habilitar CORS
(Cross-Origin Resource Sharing) en tu backend Django, permitiendo que el
frontend en el puerto 3000 pueda comunicarse con el backend en el puerto 8000.
"""

# ====================================================================
# PASO 1: Agregar corsheaders a INSTALLED_APPS
# ====================================================================

# Busca la variable INSTALLED_APPS en tu settings.py y asegúrate de que
# incluya 'corsheaders'. Debe verse así:

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',  # ← AGREGA ESTA LÍNEA
    'channels',
    'celery',
    
    # Local apps
    'apps.accounts',
    'apps.clients',
    'apps.profiles',
    'apps.candidates',
    'apps.ai_services',
    'apps.evaluations',
    'apps.notifications',
    'apps.documents',
]

# ====================================================================
# PASO 2: Agregar CorsMiddleware a MIDDLEWARE
# ====================================================================

# Busca la variable MIDDLEWARE y asegúrate de que CorsMiddleware esté
# ANTES de CommonMiddleware. Debe verse así:

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← DEBE ESTAR PRIMERO
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ====================================================================
# PASO 3: Configurar CORS
# ====================================================================

# Agrega estas líneas al final de tu settings.py o en la sección de
# configuraciones de seguridad:

# CORS Configuration
# Permite peticiones desde el frontend en localhost:3000
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Permite enviar cookies y credenciales en las peticiones
CORS_ALLOW_CREDENTIALS = True

# Headers permitidos en las peticiones
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# ====================================================================
# PASO 4 (OPCIONAL): Configuración adicional para desarrollo
# ====================================================================

# Si estás en desarrollo y quieres permitir TODAS las origins
# (NO RECOMENDADO PARA PRODUCCIÓN), puedes usar:

# CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo

# ====================================================================
# NOTAS IMPORTANTES
# ====================================================================

"""
1. SEGURIDAD EN PRODUCCIÓN:
   - En producción, NUNCA uses CORS_ALLOW_ALL_ORIGINS = True
   - Solo especifica los dominios exactos de tu frontend
   - Ejemplo para producción:
     CORS_ALLOWED_ORIGINS = [
         "https://tu-dominio.com",
         "https://www.tu-dominio.com",
     ]

2. PROBLEMAS COMUNES:
   - Si recibes errores de CORS después de hacer estos cambios:
     * Reinicia el servidor Docker: docker-compose restart
     * Limpia la caché del navegador
     * Verifica que corsheaders esté en requirements.txt

3. VERIFICAR INSTALACIÓN:
   - Asegúrate de que django-cors-headers esté en requirements.txt:
     django-cors-headers==4.3.1
   
   - Si no está, agrégalo y reconstruye el contenedor:
     docker-compose down
     docker-compose up --build

4. DEBUGGING:
   - Si las peticiones siguen fallando, revisa los logs:
     docker-compose logs -f web
   
   - Verifica en el navegador (F12 > Network tab) el error exacto

5. FRONTEND_URL EN .env:
   - También asegúrate de que tu archivo .env tenga:
     FRONTEND_URL=http://localhost:3000
"""

# ====================================================================
# EJEMPLO COMPLETO DE CONFIGURACIÓN
# ====================================================================

"""
# --- Agregar al principio del archivo settings.py ---
import os
from pathlib import Path

# --- En INSTALLED_APPS ---
INSTALLED_APPS = [
    # ... Django apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',  # CORS Headers
    'channels',
    # ... tus apps
]

# --- En MIDDLEWARE ---
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # PRIMERO
    'django.middleware.security.SecurityMiddleware',
    # ... resto de middleware
]

# --- Al final del archivo o en sección de seguridad ---
# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
"""

# ====================================================================
# FIN DE LA CONFIGURACIÓN
# ====================================================================