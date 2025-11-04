#!/bin/bash

# ========================================
# SCRIPT DE INSTALACIÓN AUTOMÁTICA
# Módulo Evaluations v1.1 - CORREGIDO
# ========================================

echo "════════════════════════════════════════════════════════════"
echo "   INSTALACIÓN MÓDULO EVALUATIONS v1.1"
echo "   Sistema de Evaluaciones para Reclutamiento"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar pasos
step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Función para éxito
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Función para error
error() {
    echo -e "${RED}✗${NC} $1"
}

# Función para warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ========================================
# VERIFICACIONES PREVIAS
# ========================================

step "Verificando estructura del proyecto..."

if [ ! -d "apps" ]; then
    error "No se encuentra la carpeta 'apps'. Asegúrate de estar en la raíz del proyecto."
    exit 1
fi

if [ ! -d "apps/accounts" ]; then
    error "No se encuentra la carpeta 'apps/accounts'. Verifica tu proyecto."
    exit 1
fi

success "Estructura del proyecto verificada"
echo ""

# ========================================
# PASO 1: CREAR CARPETA
# ========================================

step "Paso 1: Creando carpeta apps/evaluations..."

if [ -d "apps/evaluations" ]; then
    warning "La carpeta apps/evaluations ya existe"
    read -p "¿Deseas reemplazarla? (s/n): " replace
    if [ "$replace" != "s" ]; then
        error "Instalación cancelada por el usuario"
        exit 1
    fi
    rm -rf apps/evaluations
fi

mkdir -p apps/evaluations
success "Carpeta creada: apps/evaluations"
echo ""

# ========================================
# PASO 2: COPIAR ARCHIVOS
# ========================================

step "Paso 2: Copiando archivos del módulo..."

# Verificar que los archivos fuente existen
if [ ! -f "evaluations_models.py" ]; then
    error "No se encuentran los archivos fuente. Asegúrate de tener todos los archivos descargados."
    exit 1
fi

# Copiar archivos principales
cp evaluations___init__.py apps/evaluations/__init__.py
cp evaluations_apps.py apps/evaluations/apps.py
cp evaluations_models.py apps/evaluations/models.py
cp evaluations_serializers.py apps/evaluations/serializers.py
cp evaluations_views.py apps/evaluations/views.py
cp evaluations_urls.py apps/evaluations/urls.py
cp evaluations_admin.py apps/evaluations/admin.py
cp evaluations_tests.py apps/evaluations/tests.py
cp evaluations_README.md apps/evaluations/README.md

success "Archivos del módulo copiados"

# Copiar archivo de permisos
step "Copiando archivo de permisos..."

if [ -f "apps/accounts/permissions.py" ]; then
    warning "El archivo apps/accounts/permissions.py ya existe"
    read -p "¿Deseas reemplazarlo? (s/n): " replace_perms
    if [ "$replace_perms" == "s" ]; then
        cp accounts_permissions_fixed.py apps/accounts/permissions.py
        success "Archivo de permisos reemplazado"
    else
        warning "Se mantuvo el archivo de permisos existente"
        echo "   IMPORTANTE: Asegúrate de que contenga IsAdminUser, IsDirectorOrAbove, IsSupervisorOrAbove"
    fi
else
    cp accounts_permissions_fixed.py apps/accounts/permissions.py
    success "Archivo de permisos creado"
fi

# Copiar script de datos de prueba (opcional)
if [ ! -d "scripts" ]; then
    mkdir -p scripts
fi
cp evaluations_sample_data.py scripts/populate_evaluations.py
success "Script de datos de prueba copiado a scripts/"

echo ""

# ========================================
# PASO 3: CONFIGURAR SETTINGS
# ========================================

step "Paso 3: Verificando configuración en settings.py..."

if grep -q "apps.evaluations" config/settings.py; then
    success "La app ya está registrada en INSTALLED_APPS"
else
    warning "La app NO está registrada en INSTALLED_APPS"
    echo "   ACCIÓN REQUERIDA: Agrega 'apps.evaluations' a INSTALLED_APPS en config/settings.py"
    echo ""
    echo "   INSTALLED_APPS = ["
    echo "       # ..."
    echo "       'apps.accounts',"
    echo "       'apps.clients',"
    echo "       'apps.profiles',"
    echo "       'apps.candidates',"
    echo "       'apps.evaluations',  # ← AGREGAR ESTA LÍNEA"
    echo "   ]"
    echo ""
    read -p "Presiona Enter cuando hayas agregado la app a settings.py..."
fi

echo ""

# ========================================
# PASO 4: CONFIGURAR URLS
# ========================================

step "Paso 4: Verificando configuración en urls.py..."

if grep -q "api/evaluations/" config/urls.py; then
    success "Las URLs ya están configuradas"
else
    warning "Las URLs NO están configuradas"
    echo "   ACCIÓN REQUERIDA: Agrega la ruta en config/urls.py"
    echo ""
    echo "   urlpatterns = ["
    echo "       # ..."
    echo "       path('api/evaluations/', include('apps.evaluations.urls')),  # ← AGREGAR"
    echo "   ]"
    echo ""
    read -p "Presiona Enter cuando hayas agregado la ruta a urls.py..."
fi

echo ""

# ========================================
# PASO 5: MIGRACIONES
# ========================================

step "Paso 5: Ejecutando migraciones..."
echo ""

# Detectar si usa Docker
if [ -f "docker-compose.yml" ]; then
    echo "¿Usas Docker? (s/n): "
    read use_docker
    
    if [ "$use_docker" == "s" ]; then
        step "Creando migraciones con Docker..."
        docker-compose exec web python manage.py makemigrations evaluations
        
        if [ $? -eq 0 ]; then
            success "Migraciones creadas"
            
            step "Aplicando migraciones con Docker..."
            docker-compose exec web python manage.py migrate evaluations
            
            if [ $? -eq 0 ]; then
                success "Migraciones aplicadas correctamente"
            else
                error "Error al aplicar migraciones"
                exit 1
            fi
        else
            error "Error al crear migraciones"
            exit 1
        fi
    else
        step "Creando migraciones..."
        python manage.py makemigrations evaluations
        
        if [ $? -eq 0 ]; then
            success "Migraciones creadas"
            
            step "Aplicando migraciones..."
            python manage.py migrate evaluations
            
            if [ $? -eq 0 ]; then
                success "Migraciones aplicadas correctamente"
            else
                error "Error al aplicar migraciones"
                exit 1
            fi
        else
            error "Error al crear migraciones"
            exit 1
        fi
    fi
else
    step "Creando migraciones..."
    python manage.py makemigrations evaluations
    
    if [ $? -eq 0 ]; then
        success "Migraciones creadas"
        
        step "Aplicando migraciones..."
        python manage.py migrate evaluations
        
        if [ $? -eq 0 ]; then
            success "Migraciones aplicadas correctamente"
        else
            error "Error al aplicar migraciones"
            exit 1
        fi
    else
        error "Error al crear migraciones"
        exit 1
    fi
fi

echo ""

# ========================================
# PASO 6: VERIFICACIÓN
# ========================================

step "Paso 6: Verificando instalación..."
echo ""

step "Verificando imports..."
python manage.py shell -c "
from apps.evaluations.models import EvaluationTemplate
from apps.accounts.permissions import IsAdminUser
print('✓ Imports correctos')
" 2>/dev/null

if [ $? -eq 0 ]; then
    success "Imports verificados correctamente"
else
    error "Error en imports. Revisa SOLUCION_ERRORES.md"
fi

echo ""

# ========================================
# PASO 7: DATOS DE PRUEBA (OPCIONAL)
# ========================================

step "Paso 7: ¿Deseas generar datos de prueba? (s/n): "
read generate_data

if [ "$generate_data" == "s" ]; then
    step "Generando datos de prueba..."
    python manage.py shell < scripts/populate_evaluations.py
    
    if [ $? -eq 0 ]; then
        success "Datos de prueba generados"
        echo ""
        echo "   Credenciales:"
        echo "   - Admin: admin@recruitment.com / admin123"
        echo "   - Director: director@recruitment.com / director123"
        echo "   - Supervisor: supervisor@recruitment.com / supervisor123"
    else
        warning "Error al generar datos de prueba (puedes hacerlo manualmente después)"
    fi
fi

echo ""

# ========================================
# FINALIZACIÓN
# ========================================

echo "════════════════════════════════════════════════════════════"
echo "   ✅ INSTALACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 RESUMEN:"
echo "   • Archivos copiados: 9 archivos + permisos"
echo "   • Migraciones: Aplicadas correctamente"
echo "   • Datos de prueba: $([ "$generate_data" == "s" ] && echo "Generados" || echo "No generados")"
echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo "   1. Inicia el servidor:"
if [ -f "docker-compose.yml" ] && [ "$use_docker" == "s" ]; then
    echo "      docker-compose up"
else
    echo "      python manage.py runserver"
fi
echo ""
echo "   2. Accede al admin:"
echo "      http://localhost:8000/admin/"
echo ""
echo "   3. Prueba la API:"
echo "      http://localhost:8000/api/evaluations/"
echo ""
echo "📚 DOCUMENTACIÓN:"
echo "   • apps/evaluations/README.md - Documentación completa"
echo "   • SOLUCION_ERRORES.md - Solución de problemas"
echo "   • VERSION_1.1_README.md - Notas de esta versión"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

success "¡Instalación exitosa! 🎉"
echo ""