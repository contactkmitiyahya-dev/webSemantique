FUSEKI_BASE    = "http://localhost:3030/eduparcours"
FUSEKI_QUERY   = f"{FUSEKI_BASE}/query"
FUSEKI_UPDATE  = f"{FUSEKI_BASE}/update"

PREFIX = """
PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

EDU_NS = "http://www.eduparcours.org/ontologie#"
