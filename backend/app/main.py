# TEMPORAIRE (Ala) – à remplacer par la version de Yahya
"""Point d'entrée FastAPI : uvicorn app.main:app --reload --port 8000 (depuis backend/)."""
import logging
from urllib.error import URLError

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import (apprenants, certifications, competences, cours, domaines, evaluations, formateurs,
                         formations, modules, nlp, organismes, parcours, questions, recherche, responsables,
                         ressources, technologies)

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
# Vite peut choisir 5174 ou 5175 si 5173 est déjà pris (Yahya)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routeurs de Yahya et de Linda : préfixe donné ici (APIRouter() sans préfixe)
app.include_router(apprenants.router, prefix="/api/apprenants", tags=["Apprenants"])
app.include_router(certifications.router, prefix="/api/certifications", tags=["Certifications"])
app.include_router(competences.router, prefix="/api/competences", tags=["Competences"])
app.include_router(technologies.router, prefix="/api/technologies", tags=["Technologies"])
app.include_router(evaluations.router, prefix="/api/evaluations", tags=["Evaluations"])
# Routeurs d'Ala, d'Imem et de Zahra : préfixe déclaré dans APIRouter(prefix=...)
for module in (formateurs, responsables, organismes, domaines, formations, parcours, recherche, nlp,
               modules, cours, ressources, questions):
    app.include_router(module.router)


@app.get("/api/sante", tags=["Sante"])
def sante():
    """Health-check (Yahya) : l'API est opérationnelle."""
    return {"status": "ok", "service": "EduParcours API v1.0"}
