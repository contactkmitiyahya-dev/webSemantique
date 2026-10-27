# Comparaison avec les exigences de la professeure

Responsable : Linda (Phase 0, colonne Qualité). État au 27/10/2026, branche `feature/linda`.

La **grille officielle n'a pas encore été transmise**. Ce tableau reprend les exigences de son email (partie 2.1 du plan) et la check-list de validation (partie 9.4). Dès réception de la grille, ajouter ses critères exacts dans la dernière section.

Légende : ✅ fait et vérifié · 🟡 partiel · ❌ à faire · ❓ dépend d'un autre membre.

## 1. Exigences de l'email

| Exigence | État | Preuve / où le montrer |
|---|---|---|
| Thématique Éducation et Formation | ✅ | Ontologie EduParcours |
| Ontologie : ObjectProperty, DataProperty, individus, axiomes | ✅ | 214 classes, 74 ObjectProperty, 30 DataProperty, 82 groupes de disjonction. Ouvrir dans Protégé |
| Ontologie cohérente (HermiT) | ✅ (ontologie + `membre_linda.ttl`) | Vérifié par HermiT, avec un contre-test : une incohérence volontaire est bien détectée. À refaire avec les 5 fichiers `data/` |
| Interfaces graphiques front et back, technologies libres | ✅ | React (Vite) et FastAPI avec Swagger sur `/docs` |
| Requêtes SPARQL : CRUD | ✅ Linda · ❓ autres | `docs/sparql_linda.md` : CRUD complet sur Competence, Technologie et Evaluation |
| Requêtes SPARQL : filtrage | ✅ | Type, score, module, compétence, dates (`/api/evaluations?date_min=…`) |
| Requêtes SPARQL : recherche | ✅ | `?q=` sur les 3 classes (`CONTAINS(LCASE(…))`) |
| Communication front-end / back-end | ✅ | Axios (port 5173) → FastAPI (8000) → Fuseki (3030). Le front ne parle jamais à Fuseki |
| NLP : question en langage naturel → requête SPARQL exécutable | ✅ Linda · 🟡 équipe | 8 intentions. QuestionBar : intention, entités, requête affichée et résultat |
| Bibliothèques NLP citées explicitement | 🟡 | spaCy (`fr_core_news_md`, PhraseMatcher) et rapidfuzz, à citer sur une diapositive |
| Aucune API de LLM | ✅ | Aucune clé ni appel externe dans le code |

## 2. Check-list de validation (partie 9.4)

| Domaine | Point | État |
|---|---|---|
| Ontologie | Chargée dans Fuseki (COUNT = 3087) | ✅ vérifié avec Fuseki 6.2.0 |
| Ontologie | HermiT sans incohérence | ✅ (ontologie + données de Linda) |
| SPARQL | CRUD complet pour au moins une classe par membre | ✅ Linda (3 classes) · ✅ Yahya · ❓ Ala, Imem, Zahra |
| SPARQL | Filtres, recherches, chemins de propriété expliqués | ✅ `docs/memo_sparql.md`, `docs/sparql_linda.md` |
| Back-end | API documentée, codes d'erreur corrects, entrées validées et échappées | ✅ Linda (400, 404, 409, 201, 204 testés) · 🟡 Yahya (DELETE renvoie 200 au lieu de 204) |
| Front-end | Listes, fiches, formulaires, filtres, recherche, messages d'erreur | ✅ Linda (9 pages + ConfirmDialog et Notification) |
| Communication | Action front, requête SPARQL visible, résultat affiché | ✅ QuestionBar (bouton « Voir la requête SPARQL ») |
| NLP | 5 questions de membres différents, outils cités, pas de LLM | 🟡 Linda 10 questions, Yahya 8. Il manque Ala, Imem et Zahra |
| NLP | 85 % d'intentions, 80 % de requêtes (`scripts/eval_nlp.py`) | ✅ 94 % / 100 % sur 18 questions. Objectif : 40 questions |
| Intégration | Tout fonctionne après démarrage à froid | 🟡 testé sur le poste de Linda ; à refaire sur un second poste |
| Présentation | Outils NLP cités, rôle de chaque membre | ❌ diapositives à faire |
| Oral individuel | Chacun explique sa tranche, ses requêtes et l'architecture | 🟡 notes de Linda dans `docs/script_demo.md` |
| Grille officielle | Critères exacts ajoutés | ❌ grille pas encore reçue |

## 3. Tests automatiques (tranche Linda)

| Fichier | Résultat contre Fuseki 6.2.0 |
|---|---|
| `backend/tests/test_linda.py` | 53 / 53 passent |
| `scripts/eval_nlp.py` | 17/18 intentions (le seul échec est une question de Yahya : `MODULES_CERTIF_MULTIPLE` au lieu de `MODULES_CERTIF`), 18/18 requêtes |

## 4. Points d'attention pour l'équipe

1. **Fuseki 6.2.0** (version actuelle sur le site) demande **Java 21** et un dossier `databases\eduparcours` **déjà créé**. Sinon : « Directory does not exist ».
2. `backend/requirements.txt` ne contient pas `spacy` ni `httpx` (ce dernier est requis par `TestClient`). Propriétaire : Yahya.
3. Il n'y a pas de `.gitignore` à la racine (tâche d'Imem). Linda a ajouté `backend/.gitignore` (venv, caches).
4. Les intentions NLP doivent être uniques dans toute l'équipe : celles de Linda sont SOUS_COMPETENCES, MODULES_COMPETENCE, TECHNO_COMPETENCE, EVALUATIONS_MODULE, EVALUATIONS_APRES, NOTE_MINIMALE, COMPETENCES_REPANDUES et EQUIVALENTES.

## 5. Critères de la grille officielle (reçue le 27/10/2026)

La grille note **chaque membre individuellement** sur 20 points. Pour Linda, la démonstration détaillée est dans `docs/validation_linda.md`.

| Critère (texte exact de la grille) | Barème | Où Linda le démontre | État |
|---|---|---|---|
| Requêtes SPARQL | 4 | `docs/sparql_linda.md`, CRUD des 3 classes, filtres, recherche, chemins `+ * ^ \|`, GROUP BY / AVG, contrôle de cycle | ✅ |
| Individus | 2 | `data/membre_linda.ttl` : 9 compétences sur 4 niveaux, 4 technologies, 5 évaluations ; cohérent avec HermiT | ✅ |
| Scénario | 2 | Scénario « nouvelle compétence → arbre → cycle refusé → évaluation → filtre → question NLP » (`docs/validation_linda.md`, partie 3) | ✅ |
| Api IA | 4 | Module NLP sans LLM : spaCy PhraseMatcher + rapidfuzz, 8 intentions, `eval_nlp.py` (94 % / 100 %) | ✅ |
| Interfaces Graphiques | 3 | 9 pages React + ConfirmDialog, Notification, FormModal, QuestionBar | ✅ (vérification visuelle à faire) |
| Communication BE et FE | 3 | React (Axios) → FastAPI → Fuseki ; erreurs `{detail}` affichées ; requête SPARQL visible ; Swagger | ✅ |
| Valeur ajoutée | 2 | HermiT avec contre-test, 53 tests automatiques, contrôle de cycle, tolérance aux fautes, arbre interactif | ✅ |
