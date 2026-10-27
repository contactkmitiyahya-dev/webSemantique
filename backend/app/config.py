"""
Configuration centrale de l'application EduParcours.
Contient l'URL de Fuseki et les prefixes SPARQL partages.
"""

FUSEKI_URL = "http://localhost:3030/eduparcours"

PREFIXES = """
PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""
