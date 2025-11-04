const http = require('http');
const fs = require('fs');
const path = require('path');

// MIME types para diferentes archivos
const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml'
};

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    
    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './login.html'; // Página por defecto
    }

    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = mimeTypes[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                // Archivo no encontrado
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end(`
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>404 - Archivo no encontrado</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }
                            h1 { color: #e74c3c; }
                        </style>
                    </head>
                    <body>
                        <h1>404 - Archivo no encontrado</h1>
                        <p>El archivo <strong>${req.url}</strong> no fue encontrado.</p>
                        <p><a href="/login.html">Ir al Login</a></p>
                        <hr>
                        <p>Archivos disponibles:</p>
                        <ul style="text-align: left; display: inline-block;">
                            <li><a href="/login.html">login.html</a></li>
                            <li><a href="/director-dashboard-v2.html">director-dashboard-v2.html</a></li>
                            <li><a href="/director-dashboard.html">director-dashboard.html</a></li>
                            <li><a href="/styles.css">styles.css</a></li>
                            <li><a href="/api-client.js">api-client.js</a></li>
                            <li><a href="/django-integration.js">django-integration.js</a></li>
                        </ul>
                    </body>
                    </html>
                `);
            } else {
                res.writeHead(500);
                res.end(`Error del servidor: ${error.code}`);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

const PORT = 3000;
server.listen(PORT, () => {
    console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
    console.log(`📁 Sirviendo archivos desde: ${__dirname}`);
    console.log(`🌐 Accede a: http://localhost:${PORT}/login.html`);
});