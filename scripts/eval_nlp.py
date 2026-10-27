"""
Evaluation du module NLP sur docs/questions_types.csv
(colonnes : auteur, question, intention, entites, requete attendue ; en-tete facultatif).

Pour chaque question : POST /api/nlp/question (via TestClient, sans lancer uvicorn), puis
  - intention correcte  : intention renvoyee == intention attendue ;
  - requete correcte    : resultats non vides venant de Fuseki, et chaque resultat de la
                          requete attendue (1re colonne) se retrouve dans la reponse.
Objectifs du plan : 85 % d'intentions correctes, 80 % de requetes correctes.

Usage (depuis la racine du depot, Fuseki demarre) :
    python scripts/eval_nlp.py
    python scripts/eval_nlp.py --auteur Linda
"""

import argparse
import csv
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.sparql_client import select  # noqa: E402

OBJECTIF_INTENTIONS = 0.85
OBJECTIF_REQUETES = 0.80


def lire_questions(chemin, auteur=None):
    with open(chemin, encoding="utf-8") as f:
        lignes = [l for l in csv.reader(f) if l and len(l) >= 3]
    if lignes and lignes[0][0].strip().lower() == "auteur":
        lignes = lignes[1:]
    if auteur:
        lignes = [l for l in lignes if l[0].strip().lower() == auteur.lower()]
    return [
        {"auteur": l[0], "question": l[1], "intention": l[2],
         "requete": l[4] if len(l) > 4 else ""}
        for l in lignes
    ]


def valeurs_attendues(requete):
    """Valeurs (noms locaux) de la 1re variable de la requete attendue, ou None si erreur."""
    try:
        res = select(requete)
    except Exception:
        return None
    valeurs = set()
    for r in res:
        if r:
            premiere = next(iter(r.values()))
            valeurs.add(premiere["value"].split("#")[-1])
    return valeurs


def evaluer(questions):
    client = TestClient(app)
    echecs = []
    ok_int = ok_req = 0
    for q in questions:
        rep = client.post("/api/nlp/question", json={"question": q["question"]}).json()
        intention_ok = rep.get("intention") == q["intention"]
        obtenues = {v for r in rep.get("resultats", []) for v in r.values()}
        requete_ok = bool(obtenues) and rep.get("source", "fuseki") == "fuseki"
        if requete_ok and q["requete"]:
            attendues = valeurs_attendues(q["requete"])
            requete_ok = attendues is not None and attendues <= obtenues
        ok_int += intention_ok
        ok_req += requete_ok
        if not (intention_ok and requete_ok):
            echecs.append({**q, "obtenue": rep.get("intention"), "nb": len(rep.get("resultats", [])),
                           "intention_ok": intention_ok, "requete_ok": requete_ok})
    return ok_int, ok_req, echecs


def main():
    parser = argparse.ArgumentParser(description="Evalue le module NLP sur les questions types.")
    parser.add_argument("--csv", default=os.path.join(RACINE, "docs", "questions_types.csv"))
    parser.add_argument("--auteur", help="Ne garder que les questions d'un membre (ex. Linda)")
    args = parser.parse_args()

    questions = lire_questions(args.csv, args.auteur)
    if not questions:
        sys.exit("Aucune question trouvee.")
    ok_int, ok_req, echecs = evaluer(questions)
    n = len(questions)
    taux_int, taux_req = ok_int / n, ok_req / n

    print(f"Questions evaluees : {n}")
    print(f"Intentions correctes : {ok_int}/{n} = {taux_int:.0%} (objectif {OBJECTIF_INTENTIONS:.0%})")
    print(f"Requetes correctes   : {ok_req}/{n} = {taux_req:.0%} (objectif {OBJECTIF_REQUETES:.0%})")
    if echecs:
        print("\nEchecs :")
        for e in echecs:
            raison = []
            if not e["intention_ok"]:
                raison.append(f"intention {e['obtenue']} au lieu de {e['intention']}")
            if not e["requete_ok"]:
                raison.append(f"requete incorrecte ({e['nb']} resultat(s))")
            print(f"  [{e['auteur']}] {e['question']}\n      -> {' ; '.join(raison)}")
    sys.exit(0 if taux_int >= OBJECTIF_INTENTIONS and taux_req >= OBJECTIF_REQUETES else 1)


if __name__ == "__main__":
    main()
