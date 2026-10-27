from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import modules, cours, ressources, questions

app = FastAPI(title="EduParcours API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(modules.router)
app.include_router(cours.router)
app.include_router(ressources.router)
app.include_router(questions.router)


@app.get("/")
def racine():
    return {"message": "EduParcours API — /docs pour la documentation"}
