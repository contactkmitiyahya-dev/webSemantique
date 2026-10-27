# TEMPORAIRE (Ala) – à remplacer par la version d'Imem
"""Étape 2 du pipeline NLP : détection d'intention par registre de motifs (code du plan, section 5.2)."""
from app.nlp.normalisation import normaliser

REGISTRE = {}


def enregistrer(intention, *motifs):
    REGISTRE.setdefault(intention, []).extend(motifs)


def detecter_intention(question):
    txt = normaliser(question)
    scores = {i: sum(m in txt for m in motifs) for i, motifs in REGISTRE.items()}
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] > 0 else "INCONNUE"
