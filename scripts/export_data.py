"""Sauvegarde Turtle datée du dataset Fuseki (propriétaire : Imem).

Usage :
  python scripts/export_data.py                      # tout le dataset -> backups/eduparcours_AAAA-MM-JJ_HHMM.ttl
  python scripts/export_data.py --sans-ontologie     # seulement les triplets ajoutés (données + créations via l'API)
  python scripts/export_data.py --sortie chemin.ttl

L'URL du dataset se change avec la variable d'environnement FUSEKI_URL (comme load_data.py).

Une sauvegarde chaque soir ; pour la versionner : git add -f backups/<fichier>.ttl
Restauration : python scripts/load_data.py --reset, puis POST du fichier de données sur <url>/data.
"""
import argparse
import os
import sys
from datetime import datetime

import requests
from rdflib import BNode, Graph, Literal

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONTOLOGIE = os.path.join(RACINE, "ontologie", "EduParcours_final.rdf")
BASE = os.getenv("FUSEKI_URL", "http://localhost:3030/eduparcours").rstrip("/")


def cle(triplet):
    """Clé de comparaison : un littéral est comparé par valeur (« 150.00 » = « 150.0 », "x" = "x"^^xsd:string)."""
    s, p, o = triplet
    if isinstance(o, Literal):
        o = (o.toPython() if o.value is not None else str(o), o.language)
    return s, p, o


def telecharger(url: str) -> str:
    r = requests.get(f"{url}/data", headers={"Accept": "text/turtle"}, timeout=60)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sortie", help="fichier de sortie (défaut : backups/eduparcours_<date>.ttl)")
    p.add_argument("--sans-ontologie", action="store_true", help="retire les triplets de l'ontologie")
    a = p.parse_args()

    try:
        turtle = telecharger(BASE)
    except requests.RequestException as e:
        sys.exit(f"Erreur : Fuseki injoignable ({BASE}) : {e}")

    g = Graph()
    g.parse(data=turtle, format="turtle")
    n_total = len(g)
    if a.sans_ontologie:
        onto = Graph()
        onto.parse(ONTOLOGIE, format="xml")
        connus = {cle(t) for t in onto}
        for t in list(g):
            # les nœuds anonymes (restrictions OWL) ne se comparent pas entre graphes : on les retire
            if cle(t) in connus or isinstance(t[0], BNode) or isinstance(t[2], BNode):
                g.remove(t)

    g.bind("edu", "http://www.eduparcours.org/ontologie#")
    suffixe = "_donnees" if a.sans_ontologie else ""
    sortie = a.sortie or os.path.join(RACINE, "backups", f"eduparcours{suffixe}_{datetime.now():%Y-%m-%d_%H%M}.ttl")
    os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True)
    g.serialize(destination=sortie, format="turtle", encoding="utf-8")
    print(f"{len(g)} triplets exportés (dataset : {n_total}) -> {sortie}")


if __name__ == "__main__":
    main()
