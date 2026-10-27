"""
Outils communs aux routeurs CRUD (tranche Linda, reutilisables par tous).
Lecture des bindings SPARQLWrapper, litteraux echappes, verifications d'existence,
listes de relations {id, label} et suppression complete d'un individu.
"""

import re
import unicodedata
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from .sparql_client import select, update
from .utils import valid_id, make_id

# Libelle affiche d'une ressource ?x : intitule, sinon rdfs:label, sinon nom local
LABEL_X = """
    OPTIONAL { ?x edu:intitule ?_i }
    OPTIONAL { ?x rdfs:label ?_l }
    BIND(COALESCE(STR(?_i), STR(?_l), STRAFTER(STR(?x), "#")) AS ?label)
"""


def local(uri: str) -> str:
    """URI complete -> nom local (http://...#Comp_CSS -> Comp_CSS)."""
    return uri.split("#")[-1]


def val(row: dict, cle: str, defaut=None):
    """Valeur brute d'une variable d'un binding SPARQLWrapper."""
    return row[cle]["value"] if cle in row else defaut


def num(row: dict, cle: str):
    """Valeur numerique (int si possible) d'une variable, ou None."""
    v = val(row, cle)
    if v is None:
        return None
    f = float(v)
    return int(f) if f.is_integer() else round(f, 2)


def lit(texte: str) -> str:
    """Litteral SPARQL entre guillemets, echappe contre l'injection."""
    t = (texte or "").replace("\\", "\\\\").replace('"', '\\"')
    t = t.replace("\n", "\\n").replace("\r", "\\r")
    return f'"{t}"'


def lit_date(valeur: str) -> str:
    """Date ISO (2026-10-26 ou 2026-10-26T00:00:00) -> litteral xsd:dateTime ; 400 sinon."""
    try:
        d = datetime.fromisoformat(valeur)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Date invalide '{valeur}' (format attendu : 2026-10-26T00:00:00).")
    return f'"{d.strftime("%Y-%m-%dT%H:%M:%S")}"^^xsd:dateTime'


def verifier_id(identifiant: str, champ: str = "id") -> None:
    if not identifiant or not valid_id(identifiant):
        raise HTTPException(status_code=400, detail=f"{champ} invalide : '{identifiant}'.")


def generer_id(prefixe: str, libelle: str) -> str:
    """'Conception d'API' -> 'Comp_Conception_DAPI' (sans accents, majuscule initiale)."""
    sans_accents = unicodedata.normalize("NFKD", libelle).encode("ascii", "ignore").decode()
    base = make_id(re.sub(r"[^A-Za-z0-9]+", " ", sans_accents))
    if not base:
        raise HTTPException(status_code=400, detail="Impossible de generer un identifiant a partir du libelle.")
    return f"{prefixe}_{base}"


def existe(identifiant: str) -> bool:
    return bool(select(f"SELECT ?p WHERE {{ edu:{identifiant} ?p ?o }} LIMIT 1"))


def est_instance(identifiant: str, classe: str) -> bool:
    """Vrai si l'individu est de la classe (ou d'une sous-classe), sans raisonneur."""
    return bool(select(f"SELECT ?t WHERE {{ edu:{identifiant} a ?t . ?t rdfs:subClassOf* edu:{classe} }} LIMIT 1"))


def exiger_instance(identifiant: str, classe: str, code: int = 404) -> None:
    """400 si l'id est mal forme, `code` (404 par defaut) s'il n'est pas de la classe."""
    verifier_id(identifiant)
    if not est_instance(identifiant, classe):
        raise HTTPException(status_code=code, detail=f"{classe} '{identifiant}' introuvable.")


def exiger_instances(ids: List[str], classe: str) -> None:
    """Chaque id lie doit exister et etre de la bonne classe (sinon 400)."""
    for i in ids:
        exiger_instance(i, classe, code=400)


def exiger_sous_classe(type_: str, racine: str) -> None:
    """Le type choisi doit etre la racine ou l'une de ses sous-classes declarees."""
    verifier_id(type_, "type")
    if type_ == racine:
        return
    if not select(f"SELECT ?c WHERE {{ edu:{type_} rdfs:subClassOf+ ?c . FILTER(?c = edu:{racine}) }} LIMIT 1"):
        raise HTTPException(status_code=400, detail=f"Le type '{type_}' n'est pas une sous-classe de {racine}.")


def sous_classes(racine: str) -> list:
    """Classes utilisables comme type (racine comprise) : [{id, label}]."""
    res = select(f"""
    SELECT DISTINCT ?x ?label WHERE {{
        ?x rdfs:subClassOf* edu:{racine} .
        FILTER(isIRI(?x))
        {LABEL_X}
    }} ORDER BY ?label
    """)
    return [{"id": local(val(r, "x")), "label": val(r, "label")} for r in res]


def type_direct(identifiant: str, racine: str) -> Optional[str]:
    """Type le plus precis de l'individu parmi les sous-classes de la racine."""
    res = select(f"""
    SELECT ?t WHERE {{
        edu:{identifiant} a ?t . ?t rdfs:subClassOf* edu:{racine} .
        FILTER NOT EXISTS {{ edu:{identifiant} a ?t2 . ?t2 rdfs:subClassOf+ ?t . FILTER(?t2 != ?t) }}
    }} LIMIT 1
    """)
    return local(val(res[0], "t")) if res else None


def relations(motif: str) -> list:
    """Liste [{id, label}] des ?x qui verifient le motif SPARQL donne."""
    res = select(f"""
    SELECT DISTINCT ?x ?label WHERE {{
        {motif}
        FILTER(isIRI(?x))
        {LABEL_X}
    }} ORDER BY ?label
    """)
    return [{"id": local(val(r, "x")), "label": val(r, "label")} for r in res]


def compter(where: str, variable: str = "?id") -> int:
    res = select(f"SELECT (COUNT(DISTINCT {variable}) AS ?n) WHERE {{ {where} }}")
    return int(val(res[0], "n", 0)) if res else 0


def supprimer_individu(identifiant: str) -> None:
    """Supprime les triplets sortants puis entrants (contrat d'API : DELETE 204)."""
    update(f"DELETE WHERE {{ edu:{identifiant} ?p ?o }} ; DELETE WHERE {{ ?s ?p edu:{identifiant} }}")


def pagination(page: int, taille: int) -> str:
    return f"LIMIT {taille} OFFSET {(page - 1) * taille}"
