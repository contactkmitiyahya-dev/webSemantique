# Mémo SPARQL EduParcours (à lire par tous)

## Préfixes

`backend/app/sparql_client.py` les ajoute automatiquement. Il faut les écrire soi-même seulement dans l'interface de Fuseki (http://localhost:3030).

```sparql
PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
```

## Règle n° 1 : Fuseki ne raisonne pas

Fuseki ne contient que les triplets **écrits**. Tout ce que HermiT déduit dans Protégé (sous-classes, inverses, transitivité, symétrie, chaînes, classes définies) est **absent**. On le reproduit avec des chemins de propriété.

| Ce qu'on veut | ❌ Ne marche pas | ✅ À écrire |
|---|---|---|
| Toutes les compétences | `?c a edu:Competence` | `?c a/rdfs:subClassOf* edu:Competence` |
| Le type précis d'un individu | – | `?x a ?t . ?t rdfs:subClassOf* edu:Competence` |
| Lien déclaré seulement dans l'autre sens | `?f edu:accueilleApprenant ?a` | `?f ^edu:estInscritA ?a` |
| Les deux sens d'un inverse | – | `?c edu:evalue\|^edu:estEvaluePar ?x` |
| Transitivité (tous les niveaux) | `?m edu:aPourPrerequis ?p` | `?m edu:aPourPrerequis+ ?p` |
| Moi + tous les niveaux | – | `?s edu:estSousCompetenceDe* edu:Comp_JavaScript` |
| Symétrie | `?c edu:estEquivalenteA ?e` | `?c edu:estEquivalenteA\|^edu:estEquivalenteA ?e` |
| Chaîne de propriétés | `?a edu:estInscritAuModule ?m` (déduit) | `?a edu:estInscritA/edu:composeDe ?m` |
| Classe définie (ex. ApprenantQualifieFrontend) | `?a a edu:ApprenantQualifieFrontend` | `?a edu:possedeCompetence edu:Comp_HTML , edu:Comp_CSS` |

`+` signifie un ou plusieurs niveaux, `*` zéro ou plusieurs (l'élément lui-même compris), `^` l'inverse et `|` l'un ou l'autre.

Pensez à `SELECT DISTINCT` : les chemins `*` et `|` peuvent renvoyer plusieurs fois le même résultat.

## Libellés à afficher

- Personnes : `edu:nom`, `edu:prenom`.
- Formations, modules, cours, compétences, domaines : `edu:intitule` (sinon `rdfs:label`).
- Technologies, organismes, certifications, évaluations, ressources : `rdfs:label` seulement.
- Libellé générique sûr : `BIND(COALESCE(STR(?i), STR(?l), STRAFTER(STR(?x), "#")) AS ?label)`.

## Types de littéraux

| Propriété | Écriture |
|---|---|
| Dates (`dateNaissance`, `dateEvaluation`…) | `"2026-10-26T00:00:00"^^xsd:dateTime` (jamais une date seule) |
| Entiers (`dureeHeures`, `scoreMaturite`…) | `25` |
| Décimaux (`coutFormation`, `noteMinimale`…) | `10.0` (avec un point) |
| Chaînes (`intitule`, `nom`…) | `"Vue.js"^^xsd:string` |
| `rdfs:label` | `"Vue.js"@fr` |
| Booléen (`estActif`) | `true` |

Comparaison de dates : `FILTER(?d >= "2026-11-01T00:00:00"^^xsd:dateTime)`.

Recherche insensible à la casse : `FILTER(CONTAINS(LCASE(STR(?label)), LCASE("react")))`.

## CRUD en une ligne chacun

```sparql
INSERT DATA { edu:X a owl:NamedIndividual , edu:CoursFrontend ; edu:intitule "X"^^xsd:string . }
DELETE { edu:X edu:dureeHeures ?o } INSERT { edu:X edu:dureeHeures 30 } WHERE { OPTIONAL { edu:X edu:dureeHeures ?o } }
DELETE WHERE { edu:X ?p ?o } ; DELETE WHERE { ?s ?p edu:X }       # sortants puis entrants
SELECT ?p WHERE { edu:X ?p ?o } LIMIT 1                           # existe ? (sinon 404 ; si oui à la création : 409)
```

## Contraintes OWL à vérifier dans l'API (Fuseki ne les vérifie pas)

- Un seul `edu:nom` par personne.
- 3 inscriptions (`estInscritA`) au maximum par apprenant.
- Une seule certification par formation (`meneA`).
- `aPourSuivantDirect` fonctionnelle et inverse-fonctionnelle.
- Pas de cycle de prérequis ni de sous-compétences : `ASK { edu:B edu:aPourPrerequis+ edu:A }` avant d'ajouter `A aPourPrerequis B`.
- Propriétés symétriques (`estCoequipierDe`, `estEquivalenteA`) : **écrire les deux sens**, jamais soi-même.
- Formation : au moins un module et un domaine.
- Cours : un formateur, une technologie et une compétence.
- Évaluation : au moins une compétence (et un module, règle de l'équipe).

## Pièges déjà rencontrés

- Une requête dont **aucune variable n'est liée** (`SELECT ?t WHERE { edu:X a/rdfs:subClassOf* edu:Competence }`) renvoie une ligne vide dans Fuseki mais **zéro ligne** dans d'autres moteurs. Mieux vaut toujours lier une variable : `edu:X a ?t . ?t rdfs:subClassOf* edu:Competence`.
- Les noms locaux ne se devinent pas : `Lina_Master`, pas `Lina`. Vérifiez dans Fuseki.
- Le même libellé peut désigner plusieurs individus de classes différentes : « React » est une compétence, une technologie, un cours et un module.
