#!/bin/bash

echo "🚀 Iniciando Sistema Completo de Reclutamiento"
echo "=============================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para manejar Ctrl+C
cleanup() {
    echo ""
    echo -e "${YELLOW}Deteniendo servicios...${NC}"
    
    # Detener frontend
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Detener backend
    docker-compose down
    
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
    exit 0
}

trap cleanup SIGINT

# Paso 1: Verificar que Docker está corriendo
echo -e "${BLUE}1. Verificando Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo. Por favor inicia Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Docker está activo${NC}"

# Paso 2: Verificar que Node.js está instalado
echo -e "${BLUE}2. Verificando Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js no está instalado${NC}"
    echo -e "${YELLOW}   Instala Node.js desde: https://nodejs.org/${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Node.js $(node --version) instalado${NC}"

# Paso 3: Iniciar Backend Django
echo -e "${BLUE}3. Iniciando Backend Django (Puerto 8000)...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Backend iniciado${NC}"
else
    echo -e "${RED}   ❌ Error al iniciar el backend${NC}"
    exit 1
fi

# Paso 4: Esperar a que el backend esté listo
echo -e "${BLUE}4. Esperando a que el backend esté listo...${NC}"
sleep 8

# Verificar que el backend está respondiendo
for i in {1..30}; do
    if curl -s http://localhost:8000/admin/ > /dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Backend está listo${NC}"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}   ⚠ Backend tardando más de lo esperado, pero continuando...${NC}"
    fi
    
    sleep 1
done

# Paso 5: Instalar dependencias del frontend
echo -e "${BLUE}5. Verificando dependencias del frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}   Instalando dependencias...${NC}"
    npm install
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}   ✓ Dependencias instaladas${NC}"
    else
        echo -e "${RED}   ❌ Error al instalar dependencias${NC}"
        cd ..
        docker-compose down
        exit 1
    fi
else
    echo -e "${GREEN}   ✓ Dependencias ya instaladas${NC}"
fi

# Paso 6: Iniciar Frontend
echo -e "${BLUE}6. Iniciando Frontend (Puerto 3000)...${NC}"
npm start &
FRONTEND_PID=$!

# Dar tiempo para que inicie
sleep 3

# Verificar que el frontend está corriendo
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}   ✓ Frontend iniciado${NC}"
else
    echo -e "${YELLOW}   ⚠ Frontend iniciando...${NC}"
fi

cd ..

# Resumen
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Sistema Iniciado Correctamente         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Acceso al Sistema:${NC}"
echo -e "  🌐 Frontend (Login):      ${GREEN}http://localhost:3000/login.html${NC}"
echo -e "  🌐 Frontend (Dashboard):  ${GREEN}http://localhost:3000/director-dashboard-v2.html${NC}"
echo -e "  🔌 Backend API:           ${GREEN}http://localhost:8000/api/${NC}"
echo -e "  🛠️  Admin Django:          ${GREEN}http://localhost:8000/admin/${NC}"
echo ""
echo -e "${BLUE}Comandos útiles:${NC}"
echo -e "  Ver logs backend:  ${YELLOW}docker-compose logs -f${NC}"
echo -e "  Detener todo:      ${YELLOW}Presiona Ctrl+C${NC}"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener todos los servicios${NC}"
echo ""

# Mantener el script corriendo
wait $FRONTEND_PID