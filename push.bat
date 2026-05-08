@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

echo.
echo ========================================
echo GitHub Push - KDP Master Suite
echo ========================================
echo.

echo [*] Token requerido:
echo     Ve a: https://github.com/settings/tokens/new
echo     Marca: [X] repo
echo.
set /p GH_TOKEN="Ingresa token: "

echo.
echo [*] Configurando variable temporal...
setx GH_TOKEN "%GH_TOKEN%" >nul

echo [*] Ejecutando sincronización de archivos Core...
python github_push.py

echo [*] Sincronizando documentación y reglas...
python push_md.py %GH_TOKEN%

echo.
echo [OK] Completado!
echo.
pause