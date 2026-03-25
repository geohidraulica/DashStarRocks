@echo off
title Servidor Waitress - Mi App
echo ========================================
echo Iniciando servidor Waitress...
echo ========================================
echo.

:: Cambia a la carpeta del proyecto
cd /d "C:\Users\Administrador\Desktop\web-api\DashStarRocks"

:: Usar Python con el módulo waitress (alternativa)
"C:\Users\Administrador\AppData\Local\Programs\Python\Python310\python.exe" -m waitress --host=0.0.0.0 --port=8080 app:server

echo.
echo ========================================
echo Servidor detenido
echo ========================================
pause

