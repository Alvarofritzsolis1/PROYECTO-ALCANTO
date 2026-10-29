@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo      PROYECTO ALCANTO - DOCUMENTOS PDF
echo ================================================
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Instalar Python desde python.org y activar el lanzador py.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  if errorlevel 1 goto fallo
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fallo
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
if errorlevel 1 goto fallo
exit /b 0
:fallo
echo No se pudo iniciar ALCANTO. Revisa la instalacion de Python, las dependencias y Excel.
pause
exit /b 1
