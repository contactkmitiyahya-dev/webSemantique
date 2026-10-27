"""Dictionnaire d'entités (modules, cours, ressources) chargé depuis Fuseki, avec reconnaissance floue."""

import csv
import unicodedata
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz, process

from app import sparql_client as sp

TYPES_ENTITES = {
    "Module": "edu:Module",
    "Cours": "edu:Cours",
    "Ressource": "edu:RessourcePedagogique",
    "Competence": "edu:Competence",
}
SYNONYMES_CSV = Path(__file__).resolve().parents[3] / "data" / "synonymes.csv"
SEUIL = 80


def normaliser(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte)
    sans_accents = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    return " ".join(sans_accents.lower().split())


def _charger_entites(type_: str, uri_type: str) -> list[dict]:
    rows = sp.select(f"""
        SELECT ?e ?label WHERE {{
            ?e a/rdfs:subClassOf* {uri_type} ;
               rdfs:label ?label .
        }}
    """)
    return [
        {"id": sp.uri_locale(sp.valeur(r, "e")), "label": sp.valeur(r, "label"), "type": type_}
        for r in rows
    ]


def _charger_synonymes() -> dict[str, list[str]]:
    if not SYNONYMES_CSV.exists():
        return {}
    synonymes: dict[str, list[str]] = {}
    with SYNONYMES_CSV.open(encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f):
            synonymes.setdefault(ligne["id"], []).append(ligne["synonyme"])
    return synonymes


@lru_cache(maxsize=1)
def dictionnaire() -> dict[str, dict]:
    synonymes = _charger_synonymes()
    index: dict[str, dict] = {}
    for type_, uri_type in TYPES_ENTITES.items():
        for entite in _charger_entites(type_, uri_type):
            formes = [entite["label"], entite["id"].replace("_", " "), *synonymes.get(entite["id"], [])]
            for forme in formes:
                index[normaliser(forme)] = entite
    return index


def reconnaitre(texte: str) -> list[dict]:
    index = dictionnaire()
    trouvailles = process.extract(
        normaliser(texte),
        list(index),
        scorer=fuzz.partial_ratio,
        score_cutoff=SEUIL,
        limit=None,
    )
    meilleures: dict[str, dict] = {}
    for forme, score, _ in trouvailles:
        entite = index[forme]
        if entite["id"] not in meilleures or score > meilleures[entite["id"]]["score"]:
            meilleures[entite["id"]] = {**entite, "score": score}
    return sorted(meilleures.values(), key=lambda e: -e["score"])
