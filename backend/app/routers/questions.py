"""Routeur FastAPI — Questions en langage naturel (NLP intégré au back-end)
Route : POST /api/questions
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app import sparql_client as sp
from app.nlp.entities import reconnaitre
from app.nlp.intentions import detecter_intention, lemmes
from app.routers.cours import detail_cours
from app.routers.modules import competences_requises, detail_module, prerequis_module
from app.routers.ressources import lister_ressources

router = APIRouter(prefix="/api/questions", tags=["Questions"])

TYPE_REQUIS = {
    "PREREQUIS": "Module",
    "COURS_MODULE": "Module",
    "COMPETENCES_MODULE": "Module",
    "SUIVANT_MODULE": "Module",
    "TECHNO_COURS": "Cours",
    "NIVEAU_COURS": "Cours",
    "RESSOURCES_COMPETENCE": "Competence",
    "VIDEOS": None,
}


class Question(BaseModel):
    question: str


def _module_suivant(id_module: str) -> list[dict]:
    rows = sp.select(f"""
        SELECT ?s ?label WHERE {{
            edu:{id_module} edu:aPourSuivantDirect ?s .
            OPTIONAL {{ ?s rdfs:label ?label }}
        }}
    """)
    return [
        {"id": sp.uri_locale(sp.valeur(r, "s")), "label": sp.valeur(r, "label")}
        for r in rows
    ]


def _repondre(intention: str, id_entite: str):
    if intention == "PREREQUIS":
        return prerequis_module(id_entite)["prerequis"]
    if intention == "COURS_MODULE":
        return detail_module(id_entite)["cours"]
    if intention == "COMPETENCES_MODULE":
        return competences_requises(id_entite)["competencesRequises"]
    if intention == "SUIVANT_MODULE":
        return _module_suivant(id_entite)
    if intention == "TECHNO_COURS":
        return detail_cours(id_entite)["technologies"]
    if intention == "NIVEAU_COURS":
        return detail_cours(id_entite)["niveauDifficulte"]
    if intention == "RESSOURCES_COMPETENCE":
        return lister_ressources(q="", type_="", langue="", competenceId=id_entite, page=1, taille=100)["donnees"]
    return lister_ressources(q="vidéo", type_="", langue="", competenceId=id_entite, page=1, taille=100)["donnees"]


@router.post("")
def poser_question(body: Question):
    mots = sorted(lemmes(body.question))
    intention = detecter_intention(body.question)
    if intention == "INCONNUE":
        return {"intention": intention, "lemmes": mots, "message": "Question non reconnue."}

    type_requis = TYPE_REQUIS[intention]
    entite = None
    if type_requis:
        entite = next(
            (e for e in reconnaitre(body.question) if e["type"] == type_requis),
            None,
        )
        if entite is None:
            return {"intention": intention, "lemmes": mots, "message": f"Aucun {type_requis.lower()} reconnu dans la question."}

    elif intention == "VIDEOS":
        entite = next((e for e in reconnaitre(body.question) if e["type"] == "Competence"), None)

    return {
        "intention": intention,
        "lemmes": mots,
        "entite": entite,
        "reponse": _repondre(intention, entite["id"] if entite else ""),
    }
