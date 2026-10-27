# TEMPORAIRE (Ala) – à remplacer par la version de Yahya
"""Point d'entrée FastAPI : uvicorn app.main:app --reload --port 8000 (depuis backend/)."""
import logging
from urllib.error import URLError

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import domaines, formateurs, formations, nlp, organismes, parcours, recherche, responsables

# Niveau INFO : chaque requête SPARQL exécutée s'affiche dans le terminal (logger "sparql")
logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="EduParcours API", description="Projet Web sémantique – 5TWIN")


# TEMPORAIRE (Ala) – gestionnaire d'erreurs {detail} à remplacer par celui de Zahra
@app.exception_handler(RequestValidationError)
async def erreur_validation(request: Request, exc: RequestValidationError):
    """Corps de requête mal formé (ex. texte à la place d'un entier) : 400 au lieu de 422."""
    messages = [f"{'.'.join(str(x) for x in e['loc'][1:])} : {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": " ; ".join(messages)})


@app.middleware("http")
async def erreurs_serveur(request: Request, call_next):
    """Toute exception non prévue (Fuseki éteint, requête SPARQL refusée...) -> 500 {"detail"}."""
    try:
        return await call_next(request)
    except URLError:
        log.exception("Fuseki injoignable")
        return JSONResponse(status_code=500, content={"detail": "Fuseki est injoignable (port 3030) : est-il lancé ?"})
    except Exception as e:
        log.exception("Erreur interne")
        return JSONResponse(status_code=500, content={"detail": f"Erreur interne : {e}"})


# Ajouté APRÈS le middleware d'erreurs : CORS l'englobe, donc les réponses 500 ont aussi les en-têtes CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (formateurs, responsables, organismes, domaines, formations, parcours, recherche, nlp):
    app.include_router(module.router)
