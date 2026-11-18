@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Analisador de Dendrometria

rem 1) Pasta distribuivel (gerada por build_windows.bat) com Python embutido
if exist "%~dp0python\python.exe" (
    set "PY=%~dp0python\python.exe"
    goto executar
)

rem 2) Ambiente virtual local ja criado
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY=%~dp0.venv\Scripts\python.exe"
    goto executar
)

rem 3) Primeira execucao: cria o ambiente virtual com o Python do sistema
echo Primeira execucao: preparando o ambiente local. Requer internet uma unica vez.
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
if not exist "%~dp0.venv\Scripts\python.exe" goto sem_python
set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto falha_pip

:executar
"%PY%" "%~dp0launcher.py"
goto fim

:sem_python
echo.
echo Python 3.10 ou superior nao foi encontrado.
echo Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH",
echo ou use a pasta distribuivel gerada por build_windows.bat.
pause
exit /b 1

:falha_pip
echo.
echo Falha ao instalar as dependencias. Verifique a conexao e tente novamente.
rmdir /s /q .venv
pause
exit /b 1

:fim
endlocal
