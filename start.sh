#!/bin/bash

echo "🚀 Script de Inicio Rápido - Sistema de Reclutamiento"
echo "======================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Verificando archivo .env...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}   Copiando .env.example a .env${NC}"
    cp .env.example .env
    echo -e "${YELLOW}   ⚠️  Por favor, edita el archivo .env con tus credenciales antes de continuar${NC}"
    echo -e "${YELLOW}   Especialmente importante:${NC}"
    echo -e "${YELLOW}   - ANTHROPIC_API_KEY${NC}"
    echo -e "${YELLOW}   - EMAIL_HOST_USER y EMAIL_HOST_PASSWORD${NC}"
    echo ""
    read -p "Presiona Enter cuando hayas configurado el archivo .env..."
fi

echo -e "${BLUE}2. Construyendo contenedores Docker...${NC}"
docker-compose build

echo -e "${BLUE}3. Levantando servicios...${NC}"
docker-compose up -d

echo -e "${BLUE}4. Esperando a que PostgreSQL esté listo...${NC}"
sleep 5

echo -e "${BLUE}5. Ejecutando migraciones...${NC}"
docker-compose exec web python manage.py migrate

echo -e "${BLUE}6. Creando superusuario...${NC}"
echo -e "${YELLOW}   Ingresa los datos del superusuario:${NC}"
docker-compose exec web python manage.py createsuperuser

echo ""
echo -e "${GREEN}✅ ¡Sistema iniciado correctamente!${NC}"
echo ""
echo -e "${GREEN}Acceso al sistema:${NC}"
echo -e "  🌐 Admin: ${BLUE}http://localhost:8000/admin/${NC}"
echo -e "  🔌 API: ${BLUE}http://localhost:8000/api/${NC}"
echo ""
echo -e "${GREEN}Comandos útiles:${NC}"
echo -e "  Ver logs:        ${BLUE}docker-compose logs -f${NC}"
echo -e "  Detener:         ${BLUE}docker-compose down${NC}"
echo -e "  Reiniciar:       ${BLUE}docker-compose restart${NC}"
echo -e "  Shell Django:    ${BLUE}docker-compose exec web python manage.py shell${NC}"
echo ""