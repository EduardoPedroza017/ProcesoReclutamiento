#!/bin/bash

# ════════════════════════════════════════════════════════════════════
# Script de Prueba - Endpoints del Director
# ════════════════════════════════════════════════════════════════════

echo "════════════════════════════════════════════════════════════"
echo "  🧪 PRUEBA DE ENDPOINTS DEL DIRECTOR"
echo "════════════════════════════════════════════════════════════"
echo ""

# Configuración
API_URL="http://localhost:8000"
EMAIL="test.director@bechapra.com"
PASSWORD="DirectorPass123"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ════════════════════════════════════════════════════════════════════
# PASO 1: Obtener Token JWT
# ════════════════════════════════════════════════════════════════════

echo -e "${BLUE}Paso 1:${NC} Obteniendo token JWT..."

TOKEN_RESPONSE=$(curl -s -X POST $API_URL/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access":"[^"]*' | grep -o '[^"]*$')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗${NC} Error: No se pudo obtener el token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓${NC} Token obtenido exitosamente"
echo ""

# ════════════════════════════════════════════════════════════════════
# FUNCIÓN PARA PROBAR ENDPOINTS
# ════════════════════════════════════════════════════════════════════

test_endpoint() {
    local name=$1
    local url=$2
    
    echo -e "${BLUE}Probando:${NC} $name"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "$url")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓${NC} Status: $http_code OK"
        echo "Response preview:"
        echo "$body" | head -n 5
    else
        echo -e "${RED}✗${NC} Status: $http_code FAILED"
        echo "Response: $body"
    fi
    
    echo ""
    echo "────────────────────────────────────────────────────────"
    echo ""
}

# ════════════════════════════════════════════════════════════════════
# PASO 2: PROBAR TODOS LOS ENDPOINTS
# ════════════════════════════════════════════════════════════════════

echo -e "${YELLOW}INICIANDO PRUEBAS DE ENDPOINTS${NC}"
echo ""

# 1. Dashboard Principal
test_endpoint \
    "1. Dashboard Principal" \
    "$API_URL/api/director/dashboard/"

# 2. Vista General de Perfiles
test_endpoint \
    "2. Vista General de Perfiles" \
    "$API_URL/api/director/profiles/overview/"

# 3. Vista General de Candidatos
test_endpoint \
    "3. Vista General de Candidatos" \
    "$API_URL/api/director/candidates/overview/"

# 4. Rendimiento del Equipo
test_endpoint \
    "4. Rendimiento del Equipo" \
    "$API_URL/api/director/team/performance/"

# 5. Analytics de Clientes
test_endpoint \
    "5. Analytics de Todos los Clientes" \
    "$API_URL/api/director/clients/analytics/"

# 6. Reporte Mensual
test_endpoint \
    "6. Reporte Mensual (Actual)" \
    "$API_URL/api/director/reports/monthly/"

# 7. Acciones Pendientes
test_endpoint \
    "7. Acciones Pendientes" \
    "$API_URL/api/director/pending-actions/"

# 8. Embudo de Reclutamiento
test_endpoint \
    "8. Embudo de Reclutamiento" \
    "$API_URL/api/director/funnel/"

# ════════════════════════════════════════════════════════════════════
# PRUEBAS CON FILTROS
# ════════════════════════════════════════════════════════════════════

echo -e "${YELLOW}PRUEBAS CON FILTROS${NC}"
echo ""

test_endpoint \
    "9. Perfiles filtrados por estado" \
    "$API_URL/api/director/profiles/overview/?status=in_progress"

test_endpoint \
    "10. Reporte de Octubre 2024" \
    "$API_URL/api/director/reports/monthly/?month=10&year=2024"

# ════════════════════════════════════════════════════════════════════
# RESUMEN
# ════════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ PRUEBAS COMPLETADAS${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Si todos los endpoints retornaron 200 OK, ¡todo funciona correctamente!"
echo ""
echo "Próximos pasos:"
echo "  1. Revisa los datos retornados en cada endpoint"
echo "  2. Prueba con diferentes filtros y parámetros"
echo "  3. Integra los endpoints en tu frontend"
echo ""