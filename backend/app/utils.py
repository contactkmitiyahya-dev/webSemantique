"""Utilitaires communs du back-end (propriétaire : Imem).

- valid_id()   : True si l'identifiant respecte ^[A-Z][A-Za-z0-9_]*$ (anti-injection SPARQL)
- esc()        : échappement d'une chaîne avant insertion dans un littéral SPARQL
- make_id()    : génération d'un identifiant à partir d'un libellé
- pagination() : conversion page/taille -> (LIMIT, OFFSET)
- lit_*()      : littéraux typés xsd (les dates sont stockées en xsd:dateTime)
"""
import re
import unicodedata
from datetime import datetime

# Individus et classes commencent tous par une majuscule (seules les propriétés commencent par une minuscule)
_ID_VALIDE = re.compile(r"[A-Z][A-Za-z0-9_]*")
TAILLE_MAX = 100


# ----------------------------------------------------------------------------- identifiants

def valid_id(id) -> bool:
    """True si l'identifiant commence par une majuscule puis ne contient que lettres, chiffres et _."""
    # fullmatch : contrairement à "$", n'accepte pas un retour à la ligne final
    return isinstance(id, str) and _ID_VALIDE.fullmatch(id) is not None


def sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def make_id(texte: str, prefixe: str | None = None) -> str:
    """« Sonia Nasri » -> « Sonia_Nasri » ; (« Atelier Vue.js avancé », "Formation") -> « Formation_Atelier_Vue_Js_Avance ».

    Sans accents, underscores, majuscule initiale à chaque mot. Le préfixe n'est pas répété
    si le libellé commence déjà par lui. Renvoie "" si le libellé ne contient ni lettre ni chiffre.
    """
    mots = re.findall(r"[A-Za-z0-9]+", sans_accents(texte or ""))
    corps = "_".join(m[0].upper() + m[1:] for m in mots)
    if corps and prefixe and not corps.lower().startswith(prefixe.lower()):
        corps = f"{prefixe}_{corps}"
    return corps


# ----------------------------------------------------------------------------- échappement et littéraux

def esc(s) -> str:
    """Échappe une chaîne avant de la placer entre guillemets dans une requête SPARQL (anti-injection).
    None donne une chaîne vide."""
    if s is None:
        return ""
    return (str(s).replace("\\", "\\\\")   # d'abord l'antislash, sinon on doublerait les suivants
                  .replace('"', '\\"')
                  .replace("\n", "\\n")
                  .replace("\r", "\\r")
                  .replace("\t", "\\t"))


def lit_str(texte, lang: str | None = None) -> str:
    return f'"{esc(texte)}"@{lang}' if lang else f'"{esc(texte)}"^^xsd:string'


def lit_int(n) -> str:
    return f'"{int(n)}"^^xsd:integer'


def lit_dec(x) -> str:
    return f'"{float(x)}"^^xsd:decimal'


def lit_bool(b) -> str:
    return '"true"^^xsd:boolean' if b else '"false"^^xsd:boolean'


def lit_date(d: datetime) -> str:
    """datetime -> "2026-10-26T00:00:00"^^xsd:dateTime (fuseau horaire ignoré)."""
    return f'"{d.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")}"^^xsd:dateTime'


# ----------------------------------------------------------------------------- pagination

def pagination(page: int, taille: int) -> tuple[int, int]:
    """Renvoie (LIMIT, OFFSET) ; page >= 1, taille entre 1 et 100."""
    page = max(1, int(page))
    taille = min(max(1, int(taille)), TAILLE_MAX)
    return taille, (page - 1) * taille
