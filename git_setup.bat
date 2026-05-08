@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cd /d "D:\ANEXOS KDP Y DIGITALES\KDP_MASTER"

echo.
echo [1/5] Verificando configuracion Git...
echo.

:: Git init si no existe
if not exist .git (
    echo [*] Inicializando repositorio Git...
    git init
) else (
    echo [OK] Repositorio ya inicializado
)

echo.
echo [2/5] Configurando remoto...
echo.

:: Verificar si remoto ya existe
git remote -v | findstr /C:"origin" >nul
if errorlevel 1 (
    echo [*] Añadiendo remoto...
    git remote add origin https://pabloalanzahlut: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@github.com/pabloalanzahlut/KDP-Master-Suite.git
) else (
    echo [OK] Remoto ya configurado
)

echo.
echo [3/5] Verificando archivos a subir...
echo.

:: Verificar .gitignore
if not exist .gitignore (
    echo [!] Advertencia: .gitignore no existe, creando...
    (
        echo # Compilados
        echo dist/
        echo build/
        echo *.exe
        echo.
        echo # Datos usuario
        echo outputs/
        echo data/
        echo logs/
        echo backups/
        echo.
        echo # Cache
        echo __pycache__/
        echo *.pyc
    ) > .gitignore
)

:: Listar archivos que se subiran
echo [*] Archivos a subir:
git status --short | findstr /V "???" | head -n 20
echo [*] Archivos Ignorados (no se subiran):
git ls-files --others --exclude-standard | head -n 20

echo.
echo [4/5] Preparando commit...
echo.

git add .
git status --short | findstr "^A" >nul
if errorlevel 1 (
    echo [!] No hay archivos nuevos para commit
)

echo.
echo [*] Commit: Initial commit KDP Master Suite v2.4.3
git commit -m "Initial commit: KDP Master Suite v2.4.3"

echo.
echo [5/5] Subiendo a GitHub...
echo.
git push -u origin main

echo.
echo ========================================
echo [OK] COMPLETADO!
echo.
echo Revisa tu repositorio:
echo https://github.com/pabloalanzahlut/KDP-Master-Suite
echo ========================================

pause