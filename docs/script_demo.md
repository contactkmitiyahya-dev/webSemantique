# Script de la démo (5 minutes) – brouillon

Brouillon préparé par Linda à partir de la partie 8.1 du plan. Chaque membre complète son passage.

**Règle : on n'improvise pas.** Les questions NLP posées sont celles de `docs/questions_types.csv`, déjà testées par `scripts/eval_nlp.py`.

## Avant la démo (la veille et le jour J, 10 minutes avant)

1. Démarrer **Fuseki**, dans une invite de commandes (cmd), pas dans Git Bash :
   ```bat
   cd C:\Users\MSI\Downloads\apache-jena-fuseki-6.2.0\apache-jena-fuseki-6.2.0
   fuseki-server.bat --update --tdb2 --loc=databases\eduparcours /eduparcours
   ```
2. Démarrer le **back-end** :
   ```bat
   cd backend && venv\Scripts\activate && uvicorn app.main:app --port 8000
   ```
3. Démarrer le **front-end** :
   ```bat
   cd frontend && npm run dev
   ```
4. Vérifier :
   - http://localhost:3030 : le dataset `eduparcours` existe (3220 triplets avec les données de Linda) ;
   - http://localhost:8000/docs s'affiche ;
   - http://localhost:5173 s'affiche.
5. Ouvrir à l'avance, dans des onglets : Protégé (ontologie chargée, HermiT lancé), Swagger, l'application et l'interface Fuseki.
6. Vidéo de secours prête sur le bureau.

## Déroulé

| Minute | Qui | Écran | Ce qu'on dit |
|---|---|---|---|
| 0:00 | Linda | Protégé, puis schéma d'architecture | Voir texte ci-dessous |
| 0:45 | Yahya | Apprenants | Création, inscription, 4e inscription refusée (409) |
| 1:15 | Ala | Formateurs | Filtre, recherche, requête SPARQL dans les journaux |
| 1:45 | Imem | Catalogue | Filtre coût et niveau, fiche avec modules |
| 2:15 | Zahra | Modules | Prérequis indirects (`aPourPrerequis+`), cours ordonnés |
| 2:45 | Linda | Compétences, puis Évaluations | Voir texte ci-dessous |
| 3:15 | Chacun | Barre de question | Une question par membre, puis un cas d'échec |
| 4:30 | Tous | Diapositive « Outils » | spaCy, rapidfuzz, FastAPI, React, Fuseki ; difficultés ; conclusion |

### 0:00 – Linda : projet, architecture, ontologie (45 s)

> « EduParcours modélise un parcours de formation en développement web : apprenants, formations, modules, compétences et évaluations. L'ontologie a été construite dans Protégé : 214 classes, 74 propriétés objet, 30 propriétés de données et 82 groupes de disjonction. HermiT la déclare cohérente *(montrer le raisonneur, sans classe en rouge)*.
> L'architecture a trois couches : React sur le port 5173 appelle FastAPI sur le port 8000, qui envoie du SPARQL à Fuseki sur le port 3030. Le front ne parle jamais directement à Fuseki.
> Fuseki ne raisonne pas : ce que HermiT déduit, nous le retrouvons par des chemins de propriété SPARQL, comme `a/rdfs:subClassOf*`, `+` pour la transitivité et `^` pour les inverses. »

### 2:45 – Linda : compétences et évaluations (30 s)

1. **Compétences, onglet « Arbre »** : déplier Programmation Web > Programmation back-end > Conception d'API > GraphQL.
   > « La sous-compétence est transitive. Un seul chemin SPARQL, `estSousCompetenceDe+`, ramène tous les niveaux. »
2. Ouvrir **Programmation back-end** : le compteur « 9 au total » et les modules pour l'acquérir.
3. **Modifier** Programmation back-end et cocher GraphQL comme parent : l'API répond **« Cycle refusé »** (notification rouge).
   > « Fuseki ne vérifie pas les axiomes ; c'est l'API qui contrôle. »
4. **Évaluations**, bouton **« À venir »** : la liste se filtre par date (`FILTER(?date >= …^^xsd:dateTime)`). Montrer aussi la moyenne des notes minimales par type (GROUP BY + AVG).

### 3:15 – Barre de question (Linda pose la sienne, 20 s)

- Question : **« Quelles sont les sous-compétences de Programmation Web ? »**
- À montrer : l'intention `SOUS_COMPETENCES`, l'entité `Programmation Web -> Comp_ProgrammationWeb`, le bouton « Voir la requête SPARQL » et le tableau de résultats.
- Variante faute de frappe : **« Quelles sont les compétences équivalentes à Reakt ? »**. rapidfuzz corrige vers React, et Vue.js et Angular s'affichent.
- **Cas d'échec** (à faire en dernier, par Linda) : **« Quel temps fera-t-il demain ? »**. La réponse est un message d'aide avec des exemples, pas une erreur 500.

## Notes pour l'oral individuel de Linda

**Ma tranche** : Competence, Technologie et Evaluation.
- Données : `data/membre_linda.ttl`, avec 9 compétences, 4 technologies et 5 évaluations.
- SPARQL : `docs/sparql_linda.md`.
- API : `/api/competences`, `/api/technologies` et `/api/evaluations`.
- Front : 9 pages.
- NLP : 8 intentions.
- Tests : 53 tests.

**Requêtes à savoir expliquer :**
1. **Sous-compétences** : `?s (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ edu:C`. Le `+` remplace la transitivité, le `^` lit le lien déclaré dans l'autre sens.
2. **Équivalences** : `edu:estEquivalenteA|^edu:estEquivalenteA`. La propriété est symétrique : à l'écriture, l'API insère les deux sens.
3. **Modules pour acquérir une compétence** : module → cours → `developpeCompetence` → `estSousCompetenceDe*`. Le `*` inclut la compétence elle-même.
4. **Compétences les plus répandues** : `GROUP BY ?c` + `COUNT(DISTINCT ?apprenant)` + `ORDER BY DESC`.
5. **Évaluations à venir** : comparaison de `xsd:dateTime` dans un `FILTER`.

**Contraintes contrôlées par l'API (Fuseki ne le fait pas) :**
- **Cycle de sous-compétences** : avant d'ajouter le parent P à C, l'API vérifie que `P estSousCompetenceDe+ C` est faux.
- **Axiome `Evaluation ⊑ ∃porteSurCompetence.Competence`** : création refusée sans compétence (400), suppression d'une compétence refusée si une évaluation se retrouverait sans compétence (409).
- **Bornes** : score de 0 à 100, note de 0 à 20, coefficient strictement positif.
- **Types** : le type choisi doit être une sous-classe de la bonne classe.
- **Sécurité** : identifiants validés par regex, chaînes échappées (anti-injection SPARQL).

**Pourquoi « intention + entités + gabarit » plutôt qu'une génération libre :**
- La requête est **toujours valide et sûre**, car elle est écrite à la main et testée. Seule l'URI reconnue y est injectée, après validation.
- Le résultat est **explicable** : on montre l'intention, l'entité et la requête.
- Aucune API de LLM, aucune clé, aucun coût.
- Les échecs sont **maîtrisés** : intention inconnue ou entité absente donnent un message d'aide.
- Mesure : `scripts/eval_nlp.py` donne 94 % d'intentions et 100 % de requêtes correctes (objectifs 85 % et 80 %).
- Outils : **spaCy** `fr_core_news_md` (tokenisation, **PhraseMatcher**) et **rapidfuzz** (`fuzz.ratio`, seuil 80, qui tolère « reakt »).

**Difficultés rencontrées (à citer à 4:30) :**
- Le même libellé « React » désigne une compétence, une technologie, un cours et un module. Le type attendu par l'intention sert à choisir.
- Les synonymes (« bdd », « node ») sont ajoutés comme variantes des libellés : réécrire la question cassait « Node.js ».
- Fuseki 6 demande Java 21, et le dossier de la base doit exister avant le premier lancement.
