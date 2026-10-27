"""Détection de l'intention d'une question par règles de mots-clés, dans l'ordre de priorité."""

from functools import lru_cache

import spacy

from app.nlp.entities import normaliser


@lru_cache(maxsize=1)
def _modele():
    return spacy.load("fr_core_news_md")


def lemmes(question: str) -> set[str]:
    return {normaliser(t.lemma_) for t in _modele()(question) if not t.is_punct}


def detecter_intention(question: str) -> str:
    l = lemmes(question)
    if "niveau" in l:
        return "NIVEAU_COURS"
    if "suivant" in l or ("suivre" in l and "qui" in l):
        return "SUIVANT_MODULE"
    if "prerequis" in l:
        return "PREREQUIS"
    if "technologie" in l:
        return "TECHNO_COURS"
    if "video" in l:
        return "VIDEOS"
    if "ressource" in l and "competence" in l:
        return "RESSOURCES_COMPETENCE"
    if "competence" in l:
        return "COMPETENCES_MODULE"
    if "cours" in l:
        return "COURS_MODULE"
    return "INCONNUE"
