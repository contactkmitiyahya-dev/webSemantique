"""
Client SPARQL — utilise SPARQLWrapper pour communiquer avec Fuseki.
"""

from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST
from app.config import FUSEKI_QUERY, FUSEKI_UPDATE, PREFIX


def select(query: str) -> list[dict]:
    """Exécute une requête SELECT et renvoie la liste des résultats."""
    client = SPARQLWrapper(FUSEKI_QUERY)
    client.setQuery(PREFIX + query)
    client.setReturnFormat(JSON)
    data = client.query().convert()
    return data["results"]["bindings"]


def ask(query: str) -> bool:
    """Exécute une requête ASK et renvoie True ou False."""
    client = SPARQLWrapper(FUSEKI_QUERY)
    client.setQuery(PREFIX + query)
    client.setReturnFormat(JSON)
    return client.query().convert()["boolean"]


def update(query: str) -> None:
    """Exécute une requête INSERT/DELETE/UPDATE."""
    client = SPARQLWrapper(FUSEKI_UPDATE)
    client.setMethod(POST)
    client.setQuery(PREFIX + query)
    client.query()


def valeur(binding: dict, cle: str, defaut: str = "") -> str:
    """Extrait la valeur d'un binding SPARQL de façon sûre."""
    return binding.get(cle, {}).get("value", defaut)


def uri_locale(uri: str) -> str:
    """Extrait le nom local d'une URI (après le #)."""
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
