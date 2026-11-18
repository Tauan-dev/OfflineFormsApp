@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0criar_atalho.ps1"
if errorlevel 1 (
    echo Nao foi possivel criar o atalho.
    pause
    exit /b 1
)
echo.
echo Pronto. Use o atalho "Analisador de Dendrometria" na Area de Trabalho.
pause
