@echo off
echo Iniciando KDP Master Suite en modo desarrollo...
python gui_app.py
if %errorlevel% neq 0 pause