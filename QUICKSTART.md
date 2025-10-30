# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a poner el sistema en funcionamiento en menos de 10 minutos.

## ⚡ Inicio Rápido con Docker (Recomendado)

### 1. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con tu editor favorito
nano .env   # o vim, code, etc.
```

**Configura al menos estas variables:**
```env
ANTHROPIC_API_KEY=sk-ant-tu-api-key-aqui
EMAIL_HOST_USER=tu-email@tudominio.com
EMAIL_HOST_PASSWORD=tu-password
```

### 2. Ejecutar el Script de Inicio

```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x start.sh

# Ejecutar el script
./start.sh
```

El script automáticamente:
- ✅ Construye los contenedores
- ✅ Levanta los servicios
- ✅ Ejecuta las migraciones
- ✅ Te guía para crear el superusuario

### 3. Acceder al Sistema

- **Admin Panel**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/

## 📦 ¿Qué incluye este proyecto?

### ✅ Apps Completadas (Listas para usar)

1. **accounts** - Sistema de usuarios
   - Modelo User personalizado
   - 3 roles: Admin, Director, Supervisor
   - Autenticación JWT
   - Registro de actividades

2. **clients** - Gestión de clientes
   - CRUD completo de clientes
   - Contactos múltiples por cliente
   - Asignación a usuarios

3. **profiles** - Perfiles de reclutamiento
   - Modelo completo con todos los campos
   - Estados del proceso
   - Historial de cambios
   - Documentos adjuntos

### ⏳ Apps por Implementar (Próximos Sprints)

4. **candidates** - Gestión de candidatos
5. **ai_services** - Integración con Claude
6. **evaluations** - Sistema de evaluaciones
7. **notifications** - Notificaciones y correos
8. **documents** - Generación de documentos

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f web

# Detener todos los servicios
docker-compose down

# Reiniciar un servicio
docker-compose restart web

# Ejecutar comandos Django
docker-compose exec web python manage.py [comando]

# Acceder al shell de Django
docker-compose exec web python manage.py shell

# Acceder a la base de datos
docker-compose exec db psql -U postgres -d recruitment_db

# Crear migraciones
docker-compose exec web python manage.py makemigrations

# Aplicar migraciones
docker-compose exec web python manage.py migrate
```

## 📝 Primeros Pasos después de Instalar

### 1. Crear tu primer usuario (además del superusuario)

Accede al admin (http://localhost:8000/admin/) y:
1. Ve a "Usuarios"
2. Haz clic en "Agregar Usuario"
3. Completa los datos
4. Asigna un rol (Director o Supervisor)

### 2. Crear tu primer cliente

1. Ve a "Clientes"
2. Haz clic en "Agregar Cliente"
3. Completa la información de la empresa
4. Guarda

### 3. Crear tu primer perfil de reclutamiento

1. Ve a "Perfiles de Reclutamiento"
2. Haz clic en "Agregar Perfil"
3. Selecciona el cliente
4. Completa los requisitos de la posición
5. Guarda

## 🎯 Probar la API con cURL

### 1. Obtener Token de Autenticación

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@recruitment.com",
    "password": "tu-password"
  }'
```

Respuesta:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Usar el Token para Acceder a la API

```bash
# Guarda el token en una variable
TOKEN="tu-access-token-aqui"

# Obtener lista de usuarios
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/users/

# Obtener tu perfil
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/accounts/users/me/

# Listar clientes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/clients/
```

## 🐛 Solución de Problemas Comunes

### Error: "Port 5432 already in use"

Ya tienes PostgreSQL corriendo en tu máquina. Opciones:
1. Detén tu PostgreSQL local: `sudo service postgresql stop`
2. Cambia el puerto en `docker-compose.yml`

### Error: "Port 8000 already in use"

Ya hay algo corriendo en el puerto 8000:
1. Encuentra el proceso: `lsof -i :8000`
2. Detén el proceso o cambia el puerto en `docker-compose.yml`

### Error al conectar con la base de datos

Espera unos segundos más para que PostgreSQL termine de iniciar:
```bash
docker-compose logs db
```

### Olvidaste tu contraseña de superusuario

Resetea la contraseña:
```bash
docker-compose exec web python manage.py changepassword admin@recruitment.com
```

## 📚 Siguiente Paso: Desarrollo

Lee el README.md completo para:
- Entender la estructura del proyecto
- Ver el roadmap de desarrollo
- Aprender sobre las próximas features
- Documentación de la API

## 🆘 ¿Necesitas Ayuda?

1. Revisa los logs: `docker-compose logs -f`
2. Verifica tu archivo `.env`
3. Asegúrate de tener Docker actualizado
4. Consulta el README.md completo

---

**¡Feliz desarrollo! 🚀**