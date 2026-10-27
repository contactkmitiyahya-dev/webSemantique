"""Étape 2 du pipeline NLP : détection d'intention par registre de motifs (propriétaire : Imem).

Chaque membre enregistre ses motifs dans son propre fichier (nlp/ala.py, nlp/imem.py…),
sans toucher au noyau :

    enregistrer("ENSEIGNANT", "qui enseigne", "professeur")
    enregistrer("LISTER_FORMATIONS", "liste de formation", poids=0.5)   # intention générique

Les motifs s'écrivent sous la forme produite par normaliser() (minuscules, lemmatisés, sans
accents) : « quelles formations coûtent » devient « quel formation couter ».

Score d'une intention = somme, sur ses motifs présents dans la question normalisée, du nombre
de mots du motif × poids. Un motif long (« combien de module ») pèse donc plus qu'un motif
court (« module »). Un motif est reconnu en début de mot : « specialis » reconnaît
« specialiste », mais « actif » ne reconnaît pas « inactif ».
"""
import re

from app.nlp.normalisation import normaliser

REGISTRE: dict[str, list[tuple[str, re.Pattern, float]]] = {}


def enregistrer(intention: str, *motifs: str, poids: float = 1.0) -> None:
    """Ajoute des motifs à une intention (nom en MAJUSCULES_AVEC_UNDERSCORES)."""
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", intention):
        raise ValueError(f"Nom d'intention invalide : {intention}")
    liste = REGISTRE.setdefault(intention, [])
    for m in motifs:
        # sans lemmatisation : le motif est déjà écrit sous forme normalisée
        norm = normaliser(m, lemmes=False)
        if norm and all(norm != x[0] for x in liste):
            liste.append((norm, re.compile(r"(?<![a-z0-9])" + re.escape(norm)), poids))


def scores(question: str) -> dict[str, float]:
    """Score de chaque intention ayant au moins un motif reconnu (utile pour le débogage)."""
    txt = normaliser(question)
    resultat = {}
    for intention, motifs in REGISTRE.items():
        s = sum(len(norm.split()) * poids for norm, motif, poids in motifs if motif.search(txt))
        if s > 0:
            resultat[intention] = s
    return resultat


def classer_intentions(question: str) -> list[str]:
    """Intentions candidates, de la plus probable à la moins probable.

    Égalité de score : l'intention dont le plus long motif reconnu est le plus long l'emporte.
    """
    txt = normaliser(question)
    sc = scores(question)

    def plus_long(intention):
        return max((len(n.split()) for n, motif, _ in REGISTRE[intention] if motif.search(txt)), default=0)

    return sorted(sc, key=lambda i: (sc[i], plus_long(i)), reverse=True)


def detecter_intention(question: str) -> str:
    candidates = classer_intentions(question)
    return candidates[0] if candidates else "INCONNUE"
