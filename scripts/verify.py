"""
verify.py — Tâche Phase 0 de Zahra
Vérifie l'état des données chargées dans Fuseki :
  - Compte les triplets
  - Signale les individus sans type
  - Signale les individus sans nom (ni rdfs:label, ni intitule, ni nom)
  - Vérifie les contraintes de l'ontologie
Usage : python scripts/verify.py
"""

import sys
from SPARQLWrapper import SPARQLWrapper, JSON

FUSEKI_URL = "http://localhost:3030/eduparcours/query"
PREFIX = """
PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

erreurs = 0


def sparql(query: str) -> list[dict]:
    client = SPARQLWrapper(FUSEKI_URL)
    client.setQuery(PREFIX + query)
    client.setReturnFormat(JSON)
    resultats = client.query().convert()
    return resultats["results"]["bindings"]


def ok(msg: str):
    print(f"  [OK]  {msg}")


def erreur(msg: str):
    global erreurs
    erreurs += 1
    print(f"  [!!]  {msg}")


# ------------------------------------------------------------------
# 1. Nombre de triplets
# ------------------------------------------------------------------
def verifier_triplets():
    print("\n=== 1. Nombre de triplets ===")
    rows = sparql("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")
    n = int(rows[0]["n"]["value"])
    print(f"  Total : {n} triplets")
    if n < 3087:
        erreur(f"Attendu >= 3087 (ontologie seule = 3087), obtenu {n}")
    else:
        ok(f"{n} triplets chargés")


# ------------------------------------------------------------------
# 2. Individus sans type (pas de rdf:type)
# ------------------------------------------------------------------
def verifier_sans_type():
    print("\n=== 2. Individus sans type ===")
    rows = sparql("""
        SELECT ?s WHERE {
            ?s ?p ?o .
            FILTER(isIRI(?s))
            FILTER(STRSTARTS(STR(?s), "http://www.eduparcours.org/ontologie#"))
            FILTER NOT EXISTS { ?s rdf:type ?t }
        }
    """)
    if rows:
        for r in rows:
            erreur(f"Sans type : {r['s']['value'].split('#')[1]}")
    else:
        ok("Tous les individus ont un type")


# ------------------------------------------------------------------
# 3. Individus sans nom (ni rdfs:label, ni edu:intitule, ni edu:nom)
# ------------------------------------------------------------------
def verifier_sans_nom():
    print("\n=== 3. Individus sans nom ===")
    rows = sparql("""
        SELECT ?s WHERE {
            ?s rdf:type owl:NamedIndividual .
            FILTER NOT EXISTS { ?s rdfs:label ?l }
            FILTER NOT EXISTS { ?s edu:intitule ?i }
            FILTER NOT EXISTS { ?s edu:nom ?n }
        }
    """)
    if rows:
        for r in rows:
            erreur(f"Sans nom : {r['s']['value'].split('#')[1]}")
    else:
        ok("Tous les individus nommés ont un label ou un nom")


# ------------------------------------------------------------------
# 4. Contrainte : un seul edu:nom par personne
# ------------------------------------------------------------------
def verifier_nom_unique():
    print("\n=== 4. Unicité de edu:nom (une seule valeur par personne) ===")
    rows = sparql("""
        SELECT ?p (COUNT(?n) AS ?nb) WHERE {
            ?p edu:nom ?n .
        }
        GROUP BY ?p
        HAVING (COUNT(?n) > 1)
    """)
    if rows:
        for r in rows:
            erreur(f"{r['p']['value'].split('#')[1]} a {r['nb']['value']} valeurs pour edu:nom")
    else:
        ok("Chaque personne a au plus un edu:nom")


# ------------------------------------------------------------------
# 5. Contrainte : edu:aPourSuivantDirect fonctionnelle
#    (un module a au plus un suivant direct)
# ------------------------------------------------------------------
def verifier_suivant_direct():
    print("\n=== 5. Fonctionnalité de edu:aPourSuivantDirect ===")
    rows = sparql("""
        SELECT ?m (COUNT(?s) AS ?nb) WHERE {
            ?m edu:aPourSuivantDirect ?s .
        }
        GROUP BY ?m
        HAVING (COUNT(?s) > 1)
    """)
    if rows:
        for r in rows:
            erreur(f"{r['m']['value'].split('#')[1]} a {r['nb']['value']} suivants directs")
    else:
        ok("edu:aPourSuivantDirect est fonctionnelle")


# ------------------------------------------------------------------
# 6. Contrainte : pas de cycle dans edu:aPourPrerequis
# ------------------------------------------------------------------
def verifier_cycles():
    print("\n=== 6. Cycles dans edu:aPourPrerequis ===")
    rows = sparql("""
        SELECT ?m WHERE {
            ?m edu:aPourPrerequis+ ?m .
        }
    """)
    if rows:
        for r in rows:
            erreur(f"Cycle détecté : {r['m']['value'].split('#')[1]}")
    else:
        ok("Aucun cycle dans les prérequis")


# ------------------------------------------------------------------
# 7. Résumé : classes et individus de la tranche de Zahra
# ------------------------------------------------------------------
def resume_tranche():
    print("\n=== 7. Résumé de la tranche Zahra (Module / Cours / Ressource) ===")
    for classe, label in [
        ("edu:Module", "Modules"),
        ("edu:Cours", "Cours"),
        ("edu:RessourcePedagogique", "Ressources"),
    ]:
        rows = sparql(f"""
            SELECT (COUNT(?x) AS ?n) WHERE {{
                ?x a/rdfs:subClassOf* {classe} .
            }}
        """)
        n = rows[0]["n"]["value"]
        print(f"  {label} : {n}")


# ------------------------------------------------------------------
# Point d'entrée
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("  EduParcours — verify.py (Zahra)")
    print(f"  Fuseki : {FUSEKI_URL}")
    print("=" * 50)

    try:
        verifier_triplets()
        verifier_sans_type()
        verifier_sans_nom()
        verifier_nom_unique()
        verifier_suivant_direct()
        verifier_cycles()
        resume_tranche()
    except Exception as e:
        print(f"\n[ERREUR CONNEXION] Fuseki est-il démarré ? {e}")
        sys.exit(1)

    print("\n" + "=" * 50)
    if erreurs == 0:
        print("  RESULTAT : tout est correct")
    else:
        print(f"  RESULTAT : {erreurs} problème(s) détecté(s)")
    print("=" * 50)
