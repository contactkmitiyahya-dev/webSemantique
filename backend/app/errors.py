"""
Gestionnaire d'erreurs commun — Tâche Phase 0 de Zahra.
Toutes les erreurs renvoient {"detail": "message"}.
"""

import re
from fastapi import HTTPException


ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def valider_id(id_: str) -> str:
    """Vérifie que l'identifiant ne contient que des caractères sûrs."""
    if not ID_PATTERN.match(id_):
        raise HTTPException(
            status_code=400,
            detail=f"Identifiant invalide : '{id_}'. Utilisez uniquement lettres, chiffres et underscores."
        )
    return id_


def echapper(valeur: str) -> str:
    """Échappe les guillemets dans une chaîne avant insertion SPARQL."""
    return valeur.replace("\\", "\\\\").replace('"', '\\"')


def non_trouve(type_: str, id_: str):
    raise HTTPException(status_code=404, detail=f"{type_} '{id_}' introuvable.")


def deja_existe(type_: str, id_: str):
    raise HTTPException(status_code=409, detail=f"{type_} '{id_}' existe déjà.")


def donnee_invalide(message: str):
    raise HTTPException(status_code=400, detail=message)


def erreur_serveur(message: str):
    raise HTTPException(status_code=500, detail=f"Erreur serveur : {message}")
