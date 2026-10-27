"""
Modèles Pydantic partagés — Tâche Phase 0 de Zahra.
Toutes les listes de l'API renvoient {total, donnees}.
"""

from pydantic import BaseModel
from typing import Any


class ListeReponse(BaseModel):
    total: int
    donnees: list[dict[str, Any]]


class RelationItem(BaseModel):
    id: str
    label: str


# ---------- Module ----------

class ModuleCreation(BaseModel):
    intitule: str
    dureeHeures: int
    niveauDifficulte: str
    prerequisId: str | None = None


class ModuleModification(BaseModel):
    intitule: str | None = None
    dureeHeures: int | None = None
    niveauDifficulte: str | None = None


class PrerequisAjout(BaseModel):
    prerequisId: str


# ---------- Cours ----------

class CoursCreation(BaseModel):
    intitule: str
    dureeHeures: int
    niveauDifficulte: str
    ordreDansModule: int
    moduleId: str
    formateurId: str
    competenceId: str
    technologieId: str


class CoursModification(BaseModel):
    intitule: str | None = None
    dureeHeures: int | None = None
    niveauDifficulte: str | None = None
    ordreDansModule: int | None = None


# ---------- Ressource ----------

class RessourceCreation(BaseModel):
    intitule: str
    urlRessource: str
    langue: str
    type: str
    competenceId: str
    nombrePages: int | None = None
    dureeMinutes: int | None = None


class RessourceModification(BaseModel):
    intitule: str | None = None
    urlRessource: str | None = None
    langue: str | None = None
