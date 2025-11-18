@echo off
echo Creando usuarios de prueba...
echo.

cd /d "%~dp0"
python manage.py create_test_users

echo.
echo Presiona cualquier tecla para continuar...
pause >nul