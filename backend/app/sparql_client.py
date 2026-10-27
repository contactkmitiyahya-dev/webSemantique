"""
Client SPARQL - Interface avec le triplestore Apache Jena Fuseki.
Fournit deux fonctions : select() pour les lectures, update() pour les ecritures.
"""

from SPARQLWrapper import SPARQLWrapper, JSON
from .config import FUSEKI_URL, PREFIXES


def select(query: str) -> list:
    """Execute une requete SELECT SPARQL et retourne les bindings JSON."""
    sparql = SPARQLWrapper(FUSEKI_URL + "/query")
    sparql.setQuery(PREFIXES + query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def update(query: str) -> None:
    """Execute une requete UPDATE SPARQL (INSERT/DELETE) sur Fuseki."""
    sparql = SPARQLWrapper(FUSEKI_URL + "/update")
    sparql.setQuery(PREFIXES + query)
    sparql.method = "POST"
    sparql.query()
