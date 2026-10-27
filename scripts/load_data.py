"""Chargement de l'ontologie et des données dans Fuseki.

Usage (depuis la racine C:\\eduparcours) :
    python scripts/load_data.py           # ajoute ontologie + data/*.ttl
    python scripts/load_data.py --reset   # vide Fuseki (DROP ALL) puis recharge tout

L'URL du dataset se change avec la variable d'environnement FUSEKI_URL
(par défaut http://localhost:3030/eduparcours).
"""
import argparse
import os
import sys
from pathlib import Path

import requests

BASE = os.getenv("FUSEKI_URL", "http://localhost:3030/eduparcours").rstrip("/")

# Chemins calculés à partir de l'emplacement du script : marche quel que soit le dossier courant
RACINE = Path(__file__).resolve().parent.parent
ONTOLOGIE = RACINE / "ontologie" / "EduParcours_final.rdf"
DOSSIER_DATA = RACINE / "data"


def erreur(message: str) -> None:
    """Affiche un message d'erreur clair et arrête le script."""
    print(f"ERREUR : {message}", file=sys.stderr)
    sys.exit(1)


def verifier_fuseki() -> None:
    """Vérifie que Fuseki répond avant de commencer."""
    try:
        requests.get(f"{BASE}/query", params={"query": "ASK {}"}, timeout=5)
    except requests.ConnectionError:
        erreur(f"Fuseki est injoignable sur {BASE}. Est-il lancé ? "
               "(fuseki-server.bat --update --tdb2 --loc=databases\\eduparcours /eduparcours)")


def vider() -> None:
    """Supprime tous les triplets (option --reset)."""
    r = requests.post(f"{BASE}/update", data={"update": "DROP ALL"}, timeout=30)
    if not r.ok:
        erreur(f"DROP ALL refusé ({r.status_code}). Fuseki est-il lancé avec --update ?\n{r.text}")
    print("Fuseki vidé (DROP ALL).")


def charger(fichier: Path, content_type: str) -> None:
    """Envoie un fichier RDF dans le graphe par défaut (POST sur /data)."""
    if not fichier.exists():
        erreur(f"fichier introuvable : {fichier}")
    with open(fichier, "rb") as f:
        r = requests.post(f"{BASE}/data", data=f,
                          headers={"Content-Type": content_type}, timeout=60)
    if not r.ok:
        # 400 = fichier mal formé : Fuseki indique la ligne fautive dans r.text
        erreur(f"chargement de {fichier.name} refusé ({r.status_code}) :\n{r.text}")
    print(f"  OK  {fichier.relative_to(RACINE)}")


def compter() -> int:
    """Renvoie le nombre total de triplets."""
    r = requests.get(f"{BASE}/query",
                     params={"query": "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }"},
                     headers={"Accept": "application/sparql-results+json"}, timeout=30)
    r.raise_for_status()
    return int(r.json()["results"]["bindings"][0]["n"]["value"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Charge l'ontologie et data/*.ttl dans Fuseki")
    parser.add_argument("--reset", action="store_true", help="vider Fuseki avant de charger")
    args = parser.parse_args()

    verifier_fuseki()
    if args.reset:
        vider()

    print("Chargement :")
    charger(ONTOLOGIE, "application/rdf+xml")
    for ttl in sorted(DOSSIER_DATA.glob("*.ttl")):
        charger(ttl, "text/turtle")

    print(f"Nombre de triplets dans Fuseki : {compter()}")


if __name__ == "__main__":
    main()
