@echo off
rem =====================================================================
rem  Empacotamento local para Windows (x64)
rem  Gera dist\AnalisadorDendrometria\ com Python embutido + dependencias,
rem  e dist\AnalisadorDendrometria.zip. O usuario final so precisa
rem  descompactar e executar iniciar_analises.bat (sem instalar Python e
rem  sem internet). A internet e necessaria apenas AQUI, no empacotamento.
rem =====================================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PYVER=3.12.10"
set "PYTAG=312"
set "DIST=%~dp0dist\AnalisadorDendrometria"
set "CACHE=%~dp0dist\_cache"

if exist "%DIST%" rmdir /s /q "%DIST%"
mkdir "%DIST%" || goto erro
if not exist "%CACHE%" mkdir "%CACHE%"

echo [1/6] Baixando Python %PYVER% embutido...
if not exist "%CACHE%\python-%PYVER%-embed-amd64.zip" (
    powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-embed-amd64.zip -OutFile '%CACHE%\python-%PYVER%-embed-amd64.zip'" || goto erro
)
powershell -NoProfile -Command "Expand-Archive -Force '%CACHE%\python-%PYVER%-embed-amd64.zip' '%DIST%\python'" || goto erro

echo [2/6] Habilitando site-packages no Python embutido...
powershell -NoProfile -Command "$p='%DIST%\python\python%PYTAG%._pth'; (Get-Content $p) -replace '^#\s*import site','import site' | Set-Content $p; Add-Content $p '..'" || goto erro

echo [3/6] Instalando pip...
if not exist "%CACHE%\get-pip.py" (
    powershell -NoProfile -Command "Invoke-WebRequest -UseBasicParsing https://bootstrap.pypa.io/get-pip.py -OutFile '%CACHE%\get-pip.py'" || goto erro
)
"%DIST%\python\python.exe" "%CACHE%\get-pip.py" --no-warn-script-location -q || goto erro

echo [4/6] Instalando dependencias fixadas...
"%DIST%\python\python.exe" -m pip install --no-warn-script-location -q -r requirements.txt || goto erro

echo [5/6] Copiando aplicacao...
xcopy /e /i /q /y analytics "%DIST%\analytics" >nul || goto erro
xcopy /e /i /q /y .streamlit "%DIST%\.streamlit" >nul || goto erro
xcopy /e /i /q /y assets "%DIST%\assets" >nul || goto erro
xcopy /e /i /q /y static "%DIST%\static" >nul || goto erro
rem componente React: so o build compilado; node_modules nao vai para o pacote
robocopy componentes "%DIST%\componentes" /e /xd node_modules /njh /njs /nfl /ndl /np >nul
if errorlevel 8 goto erro
copy /y criar_atalho.bat "%DIST%\" >nul
copy /y criar_atalho.ps1 "%DIST%\" >nul
copy /y app.py "%DIST%\" >nul
copy /y launcher.py "%DIST%\" >nul
copy /y iniciar_analises.bat "%DIST%\" >nul
copy /y requirements.txt "%DIST%\" >nul
copy /y README.md "%DIST%\" >nul
for /d /r "%DIST%\analytics" %%d in (__pycache__) do if exist "%%d" rmdir /s /q "%%d"

echo [6/6] Verificando e compactando...
"%DIST%\python\python.exe" -c "import streamlit, pandas, plotly, openpyxl, sys; sys.path.insert(0, r'%DIST%'); import analytics; print('OK', streamlit.__version__)" || goto erro
if exist "%~dp0dist\AnalisadorDendrometria.zip" del /q "%~dp0dist\AnalisadorDendrometria.zip"
powershell -NoProfile -Command "Compress-Archive -Path '%DIST%' -DestinationPath '%~dp0dist\AnalisadorDendrometria.zip'" || goto erro

echo.
echo Pacote pronto:
echo   %DIST%
echo   %~dp0dist\AnalisadorDendrometria.zip
echo Para usar: descompacte e execute iniciar_analises.bat
pause
exit /b 0

:erro
echo.
echo FALHA no empacotamento. Veja a mensagem acima.
pause
exit /b 1
