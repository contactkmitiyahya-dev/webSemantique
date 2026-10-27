"""Fonctions communes aux routeurs d'Imem : formations, parcours, recherche.

Rappel : Fuseki ne raisonne pas. Sous-classes via a/rdfs:subClassOf*, inverses via ^,
transitivité via +. Les relations inverses étant déclarées tantôt dans un sens, tantôt
dans l'autre dans les données, on lit toujours les deux : edu:p|^edu:pInverse.

sparql_client.select() renvoie des chaînes : les nombres et booleens sont convertis ici (typer).
"""
from fastapi import HTTPException

from app.sparql_client import ask, select
from app.utils import valid_id


# ----------------------------------------------------------------------------- identifiants

def verifier_id(id_: str, champ: str = "id") -> str:
    """Renvoie l'identifiant s'il est valide (utils.valid_id), sinon 400."""
    if not valid_id(id_):
        raise HTTPException(400, f"Identifiant invalide pour « {champ} » : {id_!r} "
                                 "(majuscule initiale, puis lettres, chiffres et _ uniquement).")
    return id_


def uri(id_: str, champ: str = "id") -> str:
    """Forme préfixée edu:Id, après validation."""
    return "edu:" + verifier_id(id_, champ)


# ----------------------------------------------------------------------------- conversion des valeurs

def entier(v) -> int | None:
    return None if v is None else int(float(v))


def reel(v) -> float | None:
    return None if v is None else float(v)


def booleen(v) -> bool | None:
    return None if v is None else v in ("true", "1")


def liste(total, donnees: list, **extra) -> dict:
    """Format de liste commun : {"total": n, "donnees": [...]} (+ champs facultatifs, ex. sparql)."""
    return {"total": int(total), "donnees": donnees, **extra}


# ----------------------------------------------------------------------------- fragments SPARQL

def libelle(var: str) -> str:
    """Motif qui lie ?<var>_label au nom affichable de ?<var>.

    Ordre : edu:intitule, rdfs:label, « prénom nom », nom, nom local de l'URI.
    """
    v = var.lstrip("?")
    return f"""
    OPTIONAL {{ ?{v} edu:intitule ?{v}_i }}
    OPTIONAL {{ ?{v} rdfs:label ?{v}_l }}
    OPTIONAL {{ ?{v} edu:prenom ?{v}_p }}
    OPTIONAL {{ ?{v} edu:nom ?{v}_n }}
    BIND(COALESCE(?{v}_i, STR(?{v}_l), CONCAT(?{v}_p, " ", ?{v}_n), ?{v}_n, STRAFTER(STR(?{v}), "#")) AS ?{v}_label)"""


def individus_de(classe: str) -> list[dict]:
    """Tous les individus d'une classe (sous-classes comprises) : [{id, label}] triés par libellé."""
    lignes = select(f"""
SELECT ?x (SAMPLE(?x_label) AS ?label) WHERE {{
  ?x a/rdfs:subClassOf* {uri(classe)} .
  {libelle('x')}
}} GROUP BY ?x ORDER BY LCASE(?label)""")
    return [{"id": l["x"], "label": l["label"]} for l in lignes]


def sous_classes(classe: str) -> list[dict]:
    """La classe et toutes ses sous-classes : [{id, label}]."""
    lignes = select(f"""
SELECT ?c (SAMPLE(?l) AS ?label) WHERE {{
  ?c rdfs:subClassOf* {uri(classe)} .
  FILTER(isIRI(?c))
  OPTIONAL {{ ?c rdfs:label ?l }}
}} GROUP BY ?c ORDER BY ?label""")
    return [{"id": l["c"], "label": l.get("label") or l["c"]} for l in lignes]


# ----------------------------------------------------------------------------- contrôles

def est_de_classe(id_: str, classe: str) -> bool:
    return ask(f"ASK {{ {uri(id_)} a/rdfs:subClassOf* {uri(classe)} }}")


def est_sous_classe(c: str, classe: str) -> bool:
    return ask(f"ASK {{ {uri(c)} rdfs:subClassOf* {uri(classe)} }}")


def id_utilise(id_: str) -> bool:
    """Vrai si l'URI apparaît déjà dans le graphe (sujet ou objet) -> 409 à la création."""
    u = uri(id_)
    return ask(f"ASK {{ {{ {u} ?p ?o }} UNION {{ ?s ?p {u} }} }}")


def exiger(id_: str, classe: str, nom: str) -> None:
    """400 si l'identifiant est invalide, 404 si l'individu n'existe pas dans la classe."""
    verifier_id(id_)
    if not est_de_classe(id_, classe):
        raise HTTPException(404, f"{nom} introuvable : {id_}")


def verifier_refs(ids: list[str], classe: str, champ: str) -> None:
    """400 si un des identifiants n'est pas un individu de la classe attendue."""
    if not ids:
        return
    valeurs = " ".join(uri(i, champ) for i in ids)
    trouves = {l["x"] for l in select(
        f"SELECT DISTINCT ?x WHERE {{ VALUES ?x {{ {valeurs} }} ?x a/rdfs:subClassOf* {uri(classe)} }}")}
    manquants = [i for i in ids if i not in trouves]
    if manquants:
        raise HTTPException(400, f"« {champ} » : {', '.join(manquants)} n'est pas un(e) {classe} existant(e)")


def supprimer_individu(id_: str) -> str:
    """Requête de suppression : triplets sortants puis entrants (aucun lien orphelin)."""
    u = uri(id_)
    return f"DELETE WHERE {{ {u} ?p ?o }} ;\nDELETE WHERE {{ ?s ?p {u} }}"
