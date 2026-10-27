# Revue croisée : Linda teste la tranche de Yahya

Date : 27/10/2026. Environnement : Fuseki 6.2.0, ontologie et `membre_linda.ttl` chargés, API sur le port 8000.

**Question demandée par le plan :** « les compétences affichées dans la fiche d'un apprenant correspondent-elles à l'arbre ? »

**Réponse : oui pour les données, non pour la présentation.** La fiche (`GET /api/apprenants/{id}`) renvoie exactement les compétences déclarées par `edu:possedeCompetence`. En revanche, elle les affiche à plat, sans lien avec l'arbre des sous-compétences (voir B1).

| N° | Gravité | Page / route | Étapes | Résultat attendu | Résultat obtenu |
|---|---|---|---|---|---|
| B1 | Faible (point de la revue) | Fiche apprenant, `GET /api/apprenants/Omar` | Ouvrir la fiche d'Omar, comparer avec `/competences/arbre` | Les compétences sont situées dans l'arbre : Express.js sous Node.js, sous Programmation back-end | Liste à plat `[Node.js, JavaScript, SQL, Express.js]`. Express.js et Node.js (son parent) sont au même niveau. Les domaines couverts (Programmation back-end, Bases de données, Programmation Web) n'apparaissent pas |
| B2 | Moyenne | Liste, `GET /api/apprenants?taille=2` | Demander une page de 2 | `total` = nombre total d'apprenants (contrat `{total, donnees}`) | `total = 2` : c'est la taille de la page, pas le total. La pagination du front ne peut pas savoir s'il y a une page suivante |
| B3 | Moyenne (lu dans le code) | `POST /api/apprenants/{id}/inscription?formation_id=…` | Inscrire Omar à `formation_id=Comp_CSS` | 404 ou 400 : `Comp_CSS` n'est pas une formation | L'existence est testée avec `edu:X ?p ?o`, donc tout individu est accepté. Correctif : `edu:X a/rdfs:subClassOf* edu:Formation` (`exiger_instance(formation_id, "Formation")` dans `sparql_outils.py`) |
| B4 | Faible | `DELETE /api/apprenants/{id}` | Supprimer un apprenant de test | 204 sans corps (contrat d'API) | 200 avec `{"message": …}`. Même chose pour `DELETE /api/certifications/{id}` |
| B5 | Faible | `routers/apprenants.py`, lignes 156 à 217 | Lire `detail_apprenant` | – | 60 lignes de code mort après le `return` (copie de l'ancienne version de la fonction) |
| B6 | Faible | Fiche apprenant | Créer une compétence sans `edu:intitule` et l'attribuer | Elle s'affiche (repli sur `rdfs:label`) | La requête exige `edu:intitule`, donc la compétence est invisible. Pas de cas dans les données actuelles. Les compétences créées par `/api/competences` ont toujours un intitulé |
| B7 | Faible | `backend/requirements.txt` | `pip install -r requirements.txt` puis `pytest` | Les tests se lancent | `TestClient` exige `httpx`, absent. `spacy` manque aussi pour le NLP |

**Ce qui fonctionne bien (vérifié) :**
- création 201 ;
- id existant refusé (409) ;
- formation inexistante refusée à l'inscription (404) ;
- filtre par niveau (4 apprenants Master) ;
- les 25 tests de `test_yahya.py` et `test_utils.py` passent contre Fuseki.

## Proposition pour B1 (sans modifier la tranche de Yahya)

La fiche peut appeler, pour chaque compétence, `GET /api/competences/{id}` (champ `ancetres`), ou une seule fois `GET /api/competences/arbre`. Elle afficherait alors les compétences regroupées par domaine. Requête SPARQL équivalente :

```sparql
SELECT DISTINCT ?domaine ?competence WHERE {
    edu:Omar edu:possedeCompetence ?competence .
    ?competence (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ ?domaine .
}
```

Pour Omar, le résultat est Programmation back-end (Node.js, Express.js, SQL), Bases de données (SQL) et Programmation Web (tout).
