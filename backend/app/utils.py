# TEMPORAIRE (Ala) – à remplacer par la version d'Imem
"""Utilitaires communs du back : validation d'identifiant, échappement, génération d'id, pagination."""
import re
import unicodedata

_ID_VALIDE = re.compile(r"[A-Za-z0-9_]+")


def valid_id(id) -> bool:
    """True si l'identifiant ne contient que lettres, chiffres et _ (règle ^[A-Za-z0-9_]+$)."""
    # fullmatch : contrairement à "$", n'accepte pas un retour à la ligne final
    return isinstance(id, str) and _ID_VALIDE.fullmatch(id) is not None


def esc(s) -> str:
    """Échappe une chaîne avant de la placer entre guillemets dans une requête SPARQL (anti-injection)."""
    return (str(s).replace("\\", "\\\\")   # d'abord l'antislash, sinon on doublerait les suivants
                  .replace('"', '\\"')
                  .replace("\n", "\\n")
                  .replace("\r", "\\r")
                  .replace("\t", "\\t"))


def make_id(texte: str) -> str:
    """« Sonia Nasri » -> « Sonia_Nasri » : sans accents, underscores, majuscule initiale."""
    sans_accents = "".join(c for c in unicodedata.normalize("NFD", texte)
                           if unicodedata.category(c) != "Mn")
    mots = re.findall(r"[A-Za-z0-9]+", sans_accents)
    return "_".join(m[0].upper() + m[1:] for m in mots)


def pagination(page: int, taille: int) -> tuple[int, int]:
    """Renvoie (LIMIT, OFFSET) ; page >= 1, taille entre 1 et 100."""
    page = max(1, int(page))
    taille = min(max(1, int(taille)), 100)
    return taille, (page - 1) * taille
