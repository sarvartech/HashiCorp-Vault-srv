@echo off
title Vault Enterprise Web Console - SarvarTech
echo ========================================================
echo   🔐 VAULT ENTERPRISE WEB MANAGEMENT CONSOLE
echo   SarvarTech Secure Core System
echo ========================================================
echo.
echo Brauzerda ochilmoqda: http://localhost:5000
start http://localhost:5000
python web_server.py 5000
pause
