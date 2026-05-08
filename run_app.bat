@echo off
echo Iniciando KDP Master Suite...
echo.
python gui_app.py
if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un error. Presiona cualquier tecla para salir...
    pause >nul
)
