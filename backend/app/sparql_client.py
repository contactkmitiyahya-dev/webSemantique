import os
import logging
from SPARQLWrapper import SPARQLWrapper, JSON, POST

log = logging.getLogger("sparql")

BASE = os.getenv("FUSEKI_URL", "http://localhost:3030/eduparcours")
QUERY_URL = f"{BASE}/query"
UPDATE_URL = f"{BASE}/update"

EDU = "http://www.eduparcours.org/ontologie#"

PREFIXES = """PREFIX edu: <http://www.eduparcours.org/ontologie#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def _local(valeur: str) -> str:
    """Raccourcit une URI : edu:... -> Dr_Benali ; rdf/rdfs/owl/xsd -> "rdfs:label", "owl:NamedIndividual"."""
    if valeur.startswith(EDU):
        return valeur[len(EDU):]
    # Espaces de noms standards : on garde le préfixe pour éviter toute confusion avec un id edu:
    for prefixe, uri in (("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
                         ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
                         ("owl", "http://www.w3.org/2002/07/owl#"),
                         ("xsd", "http://www.w3.org/2001/XMLSchema#")):
        if valeur.startswith(uri):
            return f"{prefixe}:{valeur[len(uri):]}"
    return valeur


def select(query: str) -> list[dict]:
    """Exécute un SELECT et renvoie une liste de dictionnaires simples."""
    log.info("SELECT\n%s", query)
    s = SPARQLWrapper(QUERY_URL)
    s.setQuery(PREFIXES + query)
    s.setReturnFormat(JSON)
    lignes = s.query().convert()["results"]["bindings"]
    return [{cle: _local(v["value"]) for cle, v in ligne.items()} for ligne in lignes]


def select_brut(query: str) -> list[dict]:
    """SELECT au format SPARQL JSON brut : {"var": {"type": ..., "value": ...}}.
    Utilisé par les routeurs de Yahya (r["nom"]["value"]), écrits avant le format simple de select()."""
    log.info("SELECT\n%s", query)
    s = SPARQLWrapper(QUERY_URL)
    s.setQuery(PREFIXES + query)
    s.setReturnFormat(JSON)
    return s.query().convert()["results"]["bindings"]


def ask(query: str) -> bool:
    """Exécute un ASK et renvoie True ou False."""
    log.info("ASK\n%s", query)
    s = SPARQLWrapper(QUERY_URL)
    s.setQuery(PREFIXES + query)
    s.setReturnFormat(JSON)
    return s.query().convert()["boolean"]


def update(query: str) -> None:
    """Exécute un INSERT / DELETE (SPARQL Update)."""
    log.info("UPDATE\n%s", query)
    s = SPARQLWrapper(UPDATE_URL)
    s.setMethod(POST)
    s.setQuery(PREFIXES + query)
    s.query()


# Outils de Zahra (routeurs modules, cours, ressources) : sp.uri_locale(sp.valeur(r, "m"))
def valeur(ligne: dict, cle: str, defaut: str = "") -> str:
    """Valeur d'une colonne, que la ligne vienne de select() (texte) ou de select_brut() ({"value": ...})."""
    v = ligne.get(cle, defaut)
    return v.get("value", defaut) if isinstance(v, dict) else v


def uri_locale(uri: str) -> str:
    """Nom local d'une URI (après le # ou le dernier /) ; un identifiant déjà court est rendu tel quel."""
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
