"""
Point d'entree principal de l'API EduParcours.
Lance le serveur avec : uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import apprenants, certifications

app = FastAPI(
    title="EduParcours API",
    description="API REST pour la tranche Yahya - Apprenants et Certifications",
    version="1.0.0",
)

# Middleware CORS — Vite peut choisir 5173, 5174 ou 5175 si le port est deja pris
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs metier
app.include_router(apprenants.router, prefix="/api/apprenants", tags=["Apprenants"])
app.include_router(certifications.router, prefix="/api/certifications", tags=["Certifications"])


@app.get("/api/sante", tags=["Sante"])
def sante():
    """Endpoint de health-check pour verifier que l'API est operationnelle."""
    return {"status": "ok", "service": "EduParcours API v1.0"}
