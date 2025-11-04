@echo off
echo ========================================
echo  Sistema de Reclutamiento
echo  Iniciando Servicios...
echo ========================================
echo.

REM Verificar Docker
echo 1. Verificando Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta corriendo
    echo Por favor inicia Docker Desktop
    pause
    exit /b 1
)
echo    [OK] Docker esta activo
echo.

REM Verificar Node.js
echo 2. Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no esta instalado
    echo Descargalo de: https://nodejs.org/
    pause
    exit /b 1
)
echo    [OK] Node.js instalado
echo.

REM Iniciar Backend
echo 3. Iniciando Backend Django (Puerto 8000)...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] No se pudo iniciar el backend
    pause
    exit /b 1
)
echo    [OK] Backend iniciado
echo.

REM Esperar a que el backend este listo
echo 4. Esperando a que el backend este listo...
timeout /t 10 /nobreak >nul
echo    [OK] Backend listo
echo.

REM Instalar dependencias del frontend
echo 5. Verificando dependencias del frontend...
cd frontend

if not exist "node_modules" (
    echo    Instalando dependencias...
    call npm install
    if errorlevel 1 (
        echo [ERROR] No se pudieron instalar las dependencias
        cd ..
        docker-compose down
        pause
        exit /b 1
    )
    echo    [OK] Dependencias instaladas
) else (
    echo    [OK] Dependencias ya instaladas
)
echo.

REM Iniciar Frontend
echo 6. Iniciando Frontend (Puerto 3000)...
start "Frontend Server" cmd /k npm start
timeout /t 3 /nobreak >nul
echo    [OK] Frontend iniciado
echo.

cd ..

REM Resumen
echo ========================================
echo  Sistema Iniciado Correctamente!
echo ========================================
echo.
echo Acceso al Sistema:
echo   Frontend (Login):     http://localhost:3000/login.html
echo   Frontend (Dashboard): http://localhost:3000/director-dashboard-v2.html
echo   Backend API:          http://localhost:8000/api/
echo   Admin Django:         http://localhost:8000/admin/
echo.
echo Comandos utiles:
echo   Ver logs backend:  docker-compose logs -f
echo   Detener backend:   docker-compose down
echo   Detener frontend:  Cierra la ventana del servidor frontend
echo.
echo Para detener todos los servicios:
echo   1. Cierra la ventana del servidor frontend
echo   2. Ejecuta: docker-compose down
echo.
pause