@echo off
echo Starting web server from frontend directory...
cd /d "C:\Users\USER\Documents\ProcesoReclutamiento\frontend"
echo Current directory: %CD%
echo Files in directory:
dir *.html
echo.
echo Starting Python HTTP server on port 3000...
python -m http.server 3000