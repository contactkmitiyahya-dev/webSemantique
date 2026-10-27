# EduParcours

Projet Web Sémantique – 5TWIN – thématique Éducation et Formation.
Équipe : Yahya, Ala, Linda, Imem, Zahra.

Chaîne : **React :5173 → HTTP/JSON → FastAPI :8000 → SPARQL → Fuseki :3030**.
Le front ne parle jamais directement à Fuseki.

## Structure

```
ontologie/   EduParcours_final.rdf (.ttl)       ← modifié uniquement avec l'accord des 5
data/        membre_<prenom>.ttl                ← individus de chaque tranche
scripts/     load_data.py export_data.py
backend/app/ main.py config.py sparql_client.py utils.py <prenom>_commun.py
  routers/   un fichier par ressource (formations.py, parcours.py, formateurs.py…)
  nlp/       normalisation.py intents.py + un fichier de motifs/gabarits par membre (ala.py, imem.py…)
backend/tests/ test_<prenom>.py
frontend/src/ api/ components/ pages/<prenom>/
docs/        questions_types.csv sparql_<prenom>.md
backups/     sauvegardes Turtle datées (export_data.py)
```

## Démarrage (ordre : Fuseki, back, front)

`start.bat` (Windows) ou `start.sh` lance les trois services. À la main :

```bash
# 1. Fuseki – depuis le dossier de Fuseki
fuseki-server.bat --update --tdb2 --loc=databases\eduparcours /eduparcours

# 2. Chargement : ontologie + tous les data/*.ttl (--reset vide le dataset avant)
python scripts/load_data.py --reset

# 3. Back-end
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download fr_core_news_md
uvicorn app.main:app --reload --port 8000      # Swagger : http://localhost:8000/docs

# 4. Front-end
cd frontend && npm install && npm run dev       # http://localhost:5173

# Tests (Fuseki lancé, données chargées), depuis la racine
python -m pytest backend/tests -q

# Sauvegarde du soir
python scripts/export_data.py                   # backups/eduparcours_AAAA-MM-JJ_HHMM.ttl
python scripts/export_data.py --sans-ontologie  # seulement les données (sans les 3087 triplets de l'ontologie)
```

Contrôle : ontologie seule dans Fuseki → `SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` = **3087**.

Sous Windows, si `vite build` signale « Cannot find native binding » (bogue npm sur les dépendances
optionnelles), installer la liaison sans toucher au `package-lock.json` :
`npm install --no-save @rolldown/binding-win32-x64-msvc@<version de rolldown>`.

## Règles Git

- On ne pousse jamais directement sur la branche commune, **jamais de `push --force`**.
- Une branche par personne : `yahya`, `ala`, `imem`, `zahra`, `linda`.
- Fusion **deux fois par jour** (midi et soir), **après avoir lancé l'application** (Fuseki + back + front) et les tests.
- Avant de fusionner : récupérer la branche commune dans sa branche, résoudre les conflits chez soi, relancer.
- Messages de commit : `feat(imem): formations, filtre coût` (prénom entre parenthèses, puis ce qui change).
- On modifie d'abord **ses propres fichiers**. Les fichiers communs ont un propriétaire, toute modification passe par lui :

| Fichier commun | Propriétaire |
|---|---|
| `backend/app/main.py`, `config.py`, `routers/nlp.py`, `frontend/src/App.jsx`, `index.css` | Yahya |
| `backend/app/sparql_client.py`, `nlp/normalisation.py`, `scripts/load_data.py`, `frontend/src/api/client.js`, `useApi.js`, `start.bat/sh` | Ala |
| `backend/app/utils.py`, `nlp/intents.py`, `scripts/export_data.py`, `components/DataTable.jsx`, `README.md`, `.gitignore` | Imem |
| `nlp/entities.py` (dictionnaire), `FilterBar`, `SearchBox`, `RelationSelect` | Zahra |
| `nlp/entities.py` (matcher), `FormModal`, `ConfirmDialog`, `Notification`, `QuestionBar` | Linda |

- Un fichier marqué `TEMPORAIRE (X) – à remplacer par la version de Y` est une doublure : Y la remplace en gardant
  les mêmes fonctions et props (les pages des autres en dépendent).
- Le fichier d'ontologie n'est modifié par personne sans l'accord des 5.
- Aucune clé d'API (LLM ou autre) dans le dépôt : vérifier avec `git grep -i "api_key\|sk-"` avant la démo.

## Contrat d'API (rappel)

- Toutes les routes commencent par `/api`.
- Liste : `GET /api/{ressource}?q=&type=&tri=&ordre=asc|desc&page=1&taille=20` → `{"total": n, "donnees": [...]}`.
- Détail : `GET /api/{ressource}/{id}` ; création `POST` → 201 (409 si l'id existe) ;
  modification `PUT` → 200 ; suppression `DELETE` → 204 (triplets sortants **et** entrants).
- Erreurs : `{"detail": "message"}` avec 400, 404, 409, 500.
- Identifiants : `^[A-Z][A-Za-z0-9_]*$` (`utils.valid_id`) ; chaînes échappées avec `utils.esc()` avant insertion.
- Dates : ISO `2026-10-26T00:00:00`, stockées en `xsd:dateTime`.
- Relations : toujours lues dans les deux sens (`edu:p|^edu:inverse`), les données déclarant tantôt l'un, tantôt l'autre.

## NLP (question en français → SPARQL, sans API de LLM)

`POST /api/nlp/question {"question": "..."}` : normalisation spaCy → intention (`intents.py`) → entité
(rapidfuzz) → gabarit SPARQL → résultats. Chaque membre ajoute ses intentions dans `nlp/<prenom>.py`
(`MOTIFS`, `ENTITE_ATTENDUE`, `EXEMPLES`, `GABARITS`) et ses questions dans `docs/questions_types.csv`
(sans en-tête : `auteur,question,intention,entites,requete_attendue`).

## Outils utilisés (à citer dans la présentation)

Protégé + HermiT, Apache Jena Fuseki (TDB2), Python, FastAPI, SPARQLWrapper, RDFLib, pytest,
spaCy (`fr_core_news_md`), rapidfuzz, React, Vite, Axios, React Router. Aucune API de LLM.
