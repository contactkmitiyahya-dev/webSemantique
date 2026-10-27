#!/usr/bin/env bash
# Lance toute l'application EduParcours (Ala) : Fuseki, puis back-end, puis front-end.
# Linux / macOS / Git Bash. Fuseki et le back tournent en arrière-plan (journaux dans logs/),
# le front reste au premier plan. Ctrl+C arrête les trois.
# Dossier de Fuseki modifiable : FUSEKI_HOME=/chemin ./start.sh

RACINE="$(cd "$(dirname "$0")" && pwd)"
FUSEKI_HOME="${FUSEKI_HOME:-/c/fuseki/apache-jena-fuseki-5.6.0}"
mkdir -p "$RACINE/logs"

# Activation du venv : Scripts/ sous Windows (Git Bash), bin/ sous Linux / macOS
if [ -f "$RACINE/backend/venv/Scripts/activate" ]; then
  ACTIVATE="$RACINE/backend/venv/Scripts/activate"
else
  ACTIVATE="$RACINE/backend/venv/bin/activate"
fi

# Arrêter Fuseki et le back quand on quitte le script
trap 'kill $PID_FUSEKI $PID_BACK 2>/dev/null' EXIT

echo "[1/3] Fuseki (port 3030)... journal : logs/fuseki.log"
(cd "$FUSEKI_HOME" && ./fuseki-server --update --tdb2 --loc=databases/eduparcours /eduparcours) \
  > "$RACINE/logs/fuseki.log" 2>&1 &
PID_FUSEKI=$!

echo "Attente de 10 secondes que Fuseki démarre..."
sleep 10

echo "[2/3] Back-end FastAPI (port 8000)... journal : logs/backend.log"
(cd "$RACINE/backend" && source "$ACTIVATE" && uvicorn app.main:app --reload --port 8000) \
  > "$RACINE/logs/backend.log" 2>&1 &
PID_BACK=$!

echo "[3/3] Front-end React (port 5173)"
echo "API : http://localhost:8000/docs   Front : http://localhost:5173"
cd "$RACINE/frontend" && npm run dev
