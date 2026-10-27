@echo off
REM Lance toute l'application EduParcours (Ala) : Fuseki, puis back-end, puis front-end.
REM Chaque service s'ouvre dans sa propre fenetre. A lancer depuis n'importe ou.
REM Dossier de Fuseki modifiable : set FUSEKI_HOME=... avant de lancer.

if "%FUSEKI_HOME%"=="" set "FUSEKI_HOME=C:\fuseki\apache-jena-fuseki-5.6.0"
set "RACINE=%~dp0"

echo [1/3] Fuseki (port 3030)...
start "Fuseki" cmd /k "cd /d "%FUSEKI_HOME%" && fuseki-server.bat --update --tdb2 --loc=databases\eduparcours /eduparcours"

echo Attente de 10 secondes que Fuseki demarre...
timeout /t 10 /nobreak >nul

echo [2/3] Back-end FastAPI (port 8000)...
start "Back-end" cmd /k "cd /d "%RACINE%backend" && call venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [3/3] Front-end React (port 5173)...
start "Front-end" cmd /k "cd /d "%RACINE%frontend" && npm run dev"

echo.
echo Fuseki : http://localhost:3030
echo API    : http://localhost:8000/docs
echo Front  : http://localhost:5173
