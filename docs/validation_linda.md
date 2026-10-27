# Validation finale – fiche de Linda

Tranche : **Competence, Technologie, Evaluation**. Note individuelle sur 20, selon la grille officielle.

---

## 1. Avant la validation (30 minutes avant)

Ouvrir **3 invites de commandes (cmd)**, pas Git Bash.

**Fenêtre 1 – Fuseki**
```bat
cd C:\Users\MSI\Downloads\apache-jena-fuseki-6.2.0\apache-jena-fuseki-6.2.0
fuseki-server.bat --update --tdb2 --loc=databases\eduparcours /eduparcours
```
Dans PowerShell (le terminal de VS Code), écrire `.\fuseki-server.bat …` avec le `.\` devant.

Si `fuseki-server.bat` ou `java` n'est pas reconnu, lancer Java avec son chemin complet (PowerShell) :
```powershell
& "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot\bin\java.exe" -Xmx2G -cp fuseki-server.jar org.apache.jena.fuseki.main.cmds.FusekiServerUICmd --update --tdb2 --loc=databases\eduparcours /eduparcours
```
Fuseki est prêt quand la fenêtre affiche une ligne avec `Start Fuseki (http=3030)`.

**Fenêtre 2 – API**
```bat
cd C:\Users\MSI\Desktop\webSemantique\backend
venv\Scripts\activate
uvicorn app.main:app --port 8000
```

**Fenêtre 3 – Front**
```bat
cd C:\Users\MSI\Desktop\webSemantique\frontend
npm run dev
```

**Contrôles (2 minutes)**
- [ ] http://localhost:3030 : le dataset `eduparcours` est là. Dans l'onglet *query*, `SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` donne **3220** (3087 pour l'ontologie + tes données)
- [ ] http://localhost:8000/docs : Swagger s'affiche
- [ ] http://localhost:5173 : l'application s'affiche
- [ ] Lancer les tests une fois : `cd backend` puis `venv\Scripts\python -m pytest tests/test_linda.py -q` → **53 passed**

**Onglets à ouvrir à l'avance**, dans l'ordre de la présentation :
1. Protégé (ontologie)
2. Fuseki (onglet query)
3. Application : Compétences
4. Swagger
5. VS Code : `data/membre_linda.ttl`, `docs/sparql_linda.md`, `backend/app/nlp/linda.py`

Si les données ont été abîmées pendant une répétition, les recharger :
```bat
curl -X POST -H "Content-Type: text/turtle; charset=utf-8" --data-binary @data/membre_linda.ttl http://localhost:3030/eduparcours/data
```
(Recharger le même fichier ne crée pas de doublons : un triplet RDF n'existe qu'une fois.)

---

## 2. Critère par critère : quoi montrer, quoi dire

### Requêtes SPARQL (4 pts)

**Montrer** : `docs/sparql_linda.md`, puis exécuter une ou deux requêtes **directement dans Fuseki** (onglet *query*). Ensuite, montrer la même chose dans l'application.

Requête 1, la plus parlante : les sous-compétences à tous les niveaux.
```sparql
PREFIX edu: <http://www.eduparcours.org/ontologie#>
SELECT DISTINCT ?sous ?intitule WHERE {
  ?sous (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ edu:Comp_DeveloppementBackend ;
        edu:intitule ?intitule .
}
```
→ 9 résultats (Conception d'API, GraphQL, REST, Bases de données, PostgreSQL, SQL, NoSQL, Node.js, Express.js).

Requête 2 : agrégat GROUP BY.
```sparql
PREFIX edu: <http://www.eduparcours.org/ontologie#>
SELECT ?c (COUNT(DISTINCT ?a) AS ?nb) WHERE { ?a edu:possedeCompetence ?c } GROUP BY ?c ORDER BY DESC(?nb)
```

**À dire** :
- « Fuseki ne raisonne pas. `+` remplace la transitivité, `^` lit une relation déclarée dans l'autre sens, et `a/rdfs:subClassOf*` retrouve les instances des sous-classes. »
- « J'ai le CRUD complet sur mes 3 classes : INSERT DATA, DELETE/INSERT pour la modification, et DELETE des triplets sortants puis entrants pour la suppression. »
- « J'ai des filtres (type, score, module, dates avec `xsd:dateTime`), une recherche (`CONTAINS(LCASE(...))`) et des agrégats (GROUP BY, COUNT, AVG). »
- « Avant de modifier une compétence, une requête vérifie qu'elle ne crée pas de cycle. »

### Individus (2 pts)

**Montrer** : `data/membre_linda.ttl` dans VS Code. Puis, dans l'application, Compétences > onglet **Arbre**, et déplier Programmation Web > Programmation back-end > Conception d'API > GraphQL.

**À dire** :
- « 9 compétences sur 4 niveaux, 2 équivalences écrites dans les deux sens (PostgreSQL ≡ SQL, Vue.js ≡ React), 4 technologies de types différents et 5 évaluations de types différents : quiz, examen final, projet, soutenance, auto-évaluation. »
- « Chaque individu n'a qu'un type feuille, pour respecter les disjonctions. J'ai aussi complété les évaluations de l'ontologie qui n'avaient pas de module, et rattaché les compétences orphelines (Node.js, SQL, REST…). »
- « J'ai vérifié avec HermiT que l'ensemble est cohérent. »

### Scénario (2 pts) – voir la partie 3 ci-dessous

### Api IA (4 pts)

**Montrer** : la barre de question en haut de l'application. Dans l'ordre :
1. « Quelles sont les sous-compétences de Programmation Web ? » → montrer l'intention, l'entité, puis **« Voir la requête SPARQL »**.
2. « Quelles sont les compétences équivalentes à **Reakt** ? » → la faute est corrigée (« reakt », 80 %), et Vue.js et Angular s'affichent.
3. « Quelles évaluations ont lieu après le 1er février 2027 ? » → la date est extraite de la phrase.
4. **Échec** : « Quel temps fera-t-il demain ? » → message d'aide, pas d'erreur.

Ensuite, dans un terminal : `python scripts/eval_nlp.py` → **94 % d'intentions, 100 % de requêtes**.

**À dire** :
- « Aucune API de LLM ni clé. L'approche est : intention + entités + gabarit SPARQL. »
- Les étapes :
  1. normalisation (minuscules, accents) ;
  2. intention par registre de motifs pondérés ;
  3. entités avec le **PhraseMatcher de spaCy** (`fr_core_news_md`), sur un dictionnaire chargé depuis Fuseki à chaque question, donc toujours à jour ;
  4. si rien n'est trouvé, **rapidfuzz** pour les fautes ;
  5. gabarit SPARQL écrit à la main, où on injecte l'URI validée.
- « C'est plus fiable qu'une génération libre : la requête est toujours valide, sûre (pas d'injection) et explicable. »
- « Une difficulté : "React" désigne une compétence, une technologie, un cours et un module. C'est le type attendu par l'intention qui tranche. »

### Interfaces Graphiques (3 pts)

**Montrer**, en 1 minute :
- Compétences : recherche « sql », filtre par type, score minimal, pagination.
- Les 3 onglets : Liste, Arbre, Les plus répandues (graphique).
- Fiche Programmation back-end : ancêtres, arbre, équivalences, technologies, modules, évaluations ; bouton **« + Sous-compétence »** (fenêtre modale).
- Évaluations : bouton **« À venir »**, dates futures en vert, graphique des moyennes par type.
- Suppression : **boîte de confirmation**, puis notification.

**À dire** : « React avec Vite et React Router. J'ai fait les composants communs à toute l'équipe : ConfirmDialog, Notification, FormModal et la barre de question. »

### Communication BE et FE (3 pts)

**Montrer** :
1. Dans le navigateur, **F12 > onglet Réseau (Network)** : cliquer sur une compétence et montrer la requête `GET http://localhost:8000/api/competences/Comp_GraphQL` et sa réponse JSON.
2. Provoquer une erreur : supprimer **Autonomie** → la réponse **409** arrive avec `{"detail": "..."}`, et la notification rouge affiche ce message.
3. Swagger : exécuter **POST /api/evaluations** avec `"competences": []` → **400**.

**À dire** :
- « React (Axios) → FastAPI → SPARQLWrapper → Fuseki. Le front ne parle jamais directement à Fuseki. »
- « Toutes les erreurs ont le même format `{detail}` avec des codes HTTP justes : 201 création, 204 suppression, 400 donnée invalide, 404 introuvable, 409 conflit. »
- « La barre de question montre aussi la requête SPARQL produite par le back. »

### Valeur ajoutée (2 pts)

À citer :
- **HermiT** : cohérence vérifiée, avec un **contre-test**. Une compétence typée exprès dans deux classes disjointes est bien détectée comme incohérente.
- **53 tests automatiques** (pytest) sur toutes les routes et contraintes, plus le script `eval_nlp.py` qui mesure le NLP.
- **Axiomes OWL contrôlés par l'API**, puisque Fuseki ne les applique pas : cycle refusé ; évaluation sans compétence refusée ; suppression bloquée si elle viole `Evaluation ⊑ ∃porteSurCompetence` ou `Cours ⊑ ∃utiliseTechnologie`.
- **Tolérance aux fautes et aux synonymes** dans le NLP (« Reakt », « bdd », « node »).
- **Arbre interactif** des compétences.
- **Pour l'équipe** : le mémo SPARQL et le guide « ajouter un routeur en 10 minutes ».

---

## 3. Le scénario (2 pts) – environ 2 minutes, à répéter ce soir

> « Un responsable pédagogique veut ajouter la compétence *Tests unitaires* au programme JavaScript et l'évaluer. »

1. **Compétences > + Nouvelle compétence** : intitulé « Tests unitaires », type *Compétence JavaScript*, score 40, sous-compétence de **JavaScript**, technologie **JavaScript (ES6)**. Cliquer sur Créer : la fiche s'ouvre et l'id `Comp_Tests_Unitaires` a été généré.
2. **Fuseki**, onglet query :
   `SELECT ?p ?o WHERE { <http://www.eduparcours.org/ontologie#Comp_Tests_Unitaires> ?p ?o }`
   → montrer les triplets **écrits par l'application**.
3. **Onglet Arbre** : la compétence apparaît sous Programmation Web > JavaScript (transitivité).
4. **Modifier JavaScript** et cocher « Tests unitaires » comme parent → **« Cycle refusé »**.
5. **Évaluations > + Nouvelle évaluation** : « Quiz tests unitaires », Quiz en ligne, une date à venir, note 10, coefficient 1, compétence Tests unitaires, module JavaScript. Puis filtrer avec **« À venir »** : le quiz est dans la liste.
6. **Barre de question** : « Quelles sont les sous-compétences de JavaScript ? » → Tests unitaires apparaît (le NLP voit tout de suite la nouvelle donnée).
7. **Supprimer Tests unitaires** → **refusé (409)**, parce que le quiz ne porterait plus sur aucune compétence. Supprimer d'abord le quiz, puis la compétence : la confirmation s'affiche et tout disparaît de Fuseki.

À la fin, la base est revenue à son état initial et on peut recommencer.

---

## 4. Questions probables du validateur

| Question | Réponse courte |
|---|---|
| Pourquoi `a/rdfs:subClassOf*` ? | Fuseki ne déduit pas les sous-classes. Comp_GraphQL est typée CompetenceGraphQL, pas Competence |
| Différence entre `+` et `*` ? | `+` : un niveau ou plus. `*` : zéro ou plus, l'élément lui-même compris (utile pour « la compétence ou ses sous-compétences ») |
| estEquivalenteA est symétrique : pourquoi écrire les deux sens ? | Fuseki ne déduit pas la symétrie. Sans le second triplet, la requête dans l'autre sens ne trouve rien. À la lecture j'utilise aussi `\|^` par sécurité |
| Comment évitez-vous l'injection SPARQL ? | Les ids sont validés par regex (sinon 400). Les chaînes sont échappées (`\`, `"`, retours à la ligne). Le type est vérifié comme sous-classe de la bonne classe |
| Où est l'IA ? Avez-vous utilisé ChatGPT / une API ? | Non, c'est interdit par le sujet. spaCy (PhraseMatcher, modèle `fr_core_news_md`) et rapidfuzz, en local, sans clé |
| Pourquoi un seuil de 80 et pas 85 ? | « reakt » contre « react » donne exactement 80 avec `fuzz.ratio`. À 85, la correction ne marcherait pas. WRatio donnait des faux positifs (« module » ≈ « module react ») |
| Que se passe-t-il si la question n'est pas comprise ? | Intention inconnue ou entité absente : message d'aide avec des exemples, jamais une erreur 500 (testé automatiquement) |
| Comment mesurez-vous la qualité du NLP ? | `scripts/eval_nlp.py` rejoue les questions de `docs/questions_types.csv`. Il compare l'intention et vérifie que la requête renvoie les résultats attendus |
| Que vérifie HermiT que Fuseki ne vérifie pas ? | Les disjonctions, cardinalités et restrictions. Fuseki stocke sans contrôler, donc c'est l'API qui applique les règles importantes |

---

## 5. En cas de panne pendant la validation

| Problème | Solution |
|---|---|
| Fuseki ne démarre pas | Vérifier `java -version` (21). Utiliser la commande `java -cp fuseki-server.jar …` ci-dessus |
| Le front affiche « L'API ne répond pas » | La fenêtre 2 (uvicorn) est fermée : la relancer |
| Une liste est vide | Les données ne sont pas chargées : relancer la commande `curl … membre_linda.ttl` |
| La question NLP n'est pas comprise | Ne pas improviser. Reprendre une question de la partie 2 |
