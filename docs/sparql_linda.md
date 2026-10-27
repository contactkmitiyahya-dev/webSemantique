# Requêtes SPARQL – tranche Linda (Competence, Technologie, Evaluation)

Toutes les requêtes sont envoyées par `backend/app/sparql_client.py`, qui ajoute les préfixes :

```sparql
PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
```

Fuseki ne raisonne pas. Trois règles sont donc appliquées partout :

| Besoin | Chemin SPARQL utilisé | Pourquoi |
|---|---|---|
| Toutes les instances d'une classe | `?x a/rdfs:subClassOf* edu:Competence` | `Comp_GraphQL` est typée `CompetenceGraphQL`, pas `Competence` |
| Sous-compétences indirectes | `(edu:estSousCompetenceDe\|^edu:aPourSousCompetence)+` | propriété transitive, et le lien peut être déclaré par l'inverse |
| Équivalences | `edu:estEquivalenteA\|^edu:estEquivalenteA` | propriété symétrique : on lit les deux sens |
| Lien évaluation → cours | `edu:evalue\|^edu:estEvaluePar` | `Cours_Intro_HTML estEvaluePar Quiz_HTML` n'est déclaré que dans ce sens |

Données : `data/membre_linda.ttl`, avec 9 compétences, 4 technologies et 5 évaluations nouvelles, plus des compléments sur des individus existants.

---

## 1. Competence – `/api/competences`

### Liste, filtre par type et score, recherche (GET /api/competences?q=sql&type=CompetenceBackend&score_min=50)

```sparql
SELECT ?id (SAMPLE(?intitule) AS ?lib) (SAMPLE(?score) AS ?sc)
       (COUNT(DISTINCT ?sous) AS ?nbSous) WHERE {
    ?id a ?t . ?t rdfs:subClassOf* edu:Competence .
    OPTIONAL { ?id edu:intitule ?i } OPTIONAL { ?id rdfs:label ?l }
    BIND(COALESCE(STR(?i), STR(?l), STRAFTER(STR(?id), "#")) AS ?intitule)
    OPTIONAL { ?id edu:scoreMaturite ?score }
    ?id a/rdfs:subClassOf* edu:CompetenceBackend .                 # filtre type
    FILTER(BOUND(?score) && ?score >= 50)                           # filtre score
    FILTER(CONTAINS(LCASE(?intitule), LCASE("sql")))                # recherche
    OPTIONAL { ?sous (edu:estSousCompetenceDe|^edu:aPourSousCompetence) ?id }
} GROUP BY ?id ORDER BY ?lib LIMIT 20 OFFSET 0
```

Le `total` est calculé à part avec `SELECT (COUNT(DISTINCT ?id) AS ?n) WHERE { … mêmes motifs … }`.

### Détail (GET /api/competences/Comp_DeveloppementBackend)

```sparql
# Sous-compétences directes, puis toutes (chemin transitif +)
SELECT DISTINCT ?x WHERE { ?x (edu:estSousCompetenceDe|^edu:aPourSousCompetence) edu:Comp_DeveloppementBackend }
SELECT DISTINCT ?x WHERE { ?x (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ edu:Comp_DeveloppementBackend }

# Ancêtres
SELECT DISTINCT ?x WHERE { edu:Comp_DeveloppementBackend (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ ?x }

# Modules pour acquérir la compétence : un cours du module développe la compétence
# ou l'une de ses sous-compétences (chemin * = zéro ou plusieurs)
SELECT DISTINCT ?x WHERE {
    ?x edu:contientCours|^edu:appartientAuModule ?cours .
    ?cours edu:developpeCompetence|^edu:estDeveloppeePar ?s .
    ?s (edu:estSousCompetenceDe|^edu:aPourSousCompetence)* edu:Comp_DeveloppementBackend .
}
```

Résultat sur les données : `toutesSousCompetences` contient GraphQL, REST, PostgreSQL, SQL, NoSQL, Node.js et Express.js (Express est sous Node.js, lui-même sous Programmation back-end).

### Arbre (GET /api/competences/arbre?racine=Comp_ProgrammationWeb)

```sparql
SELECT DISTINCT ?e ?p WHERE { ?e (edu:estSousCompetenceDe|^edu:aPourSousCompetence) ?p }
```

L'arbre est construit en Python à partir de ces arêtes. Les racines sont les compétences sans parent.

### Compétences les plus répandues (GET /api/competences/repandues) – GROUP BY

```sparql
SELECT ?x ?label (COUNT(DISTINCT ?a) AS ?nb) WHERE {
    ?a edu:possedeCompetence|^edu:estPossedeePar ?x .
    OPTIONAL { ?x edu:intitule ?_i } OPTIONAL { ?x rdfs:label ?_l }
    BIND(COALESCE(STR(?_i), STR(?_l)) AS ?label)
} GROUP BY ?x ?label ORDER BY DESC(?nb) ?label LIMIT 10
```

### Création (POST) – équivalence écrite dans les deux sens

```sparql
INSERT DATA {
    edu:Comp_Tests_Unitaires a owl:NamedIndividual , edu:CompetenceJavaScript .
    edu:Comp_Tests_Unitaires rdfs:label "Tests unitaires"@fr .
    edu:Comp_Tests_Unitaires edu:intitule "Tests unitaires"^^xsd:string .
    edu:Comp_Tests_Unitaires edu:scoreMaturite 40 .
    edu:Comp_Tests_Unitaires edu:estSousCompetenceDe edu:Comp_JavaScript .
    edu:Comp_Tests_Unitaires edu:estEquivalenteA edu:Comp_POO_JavaScript .
    edu:Comp_POO_JavaScript edu:estEquivalenteA edu:Comp_Tests_Unitaires .
}
```

### Contrôle des cycles avant modification (PUT)

Si le parent choisi `P` est déjà une sous-compétence (directe ou indirecte) de `C`, on refuse avec un code 400 :

```sparql
SELECT ?x WHERE { edu:P (edu:estSousCompetenceDe|^edu:aPourSousCompetence)+ edu:C . BIND(1 AS ?x) } LIMIT 1
```

### Modification (PUT) : on efface les valeurs gérées, puis on réinsère

```sparql
DELETE { edu:C a ?t } WHERE { edu:C a ?t . ?t rdfs:subClassOf* edu:Competence } ;
DELETE WHERE { edu:C edu:intitule ?o } ;
DELETE WHERE { edu:C edu:scoreMaturite ?o } ;
DELETE WHERE { edu:C edu:estSousCompetenceDe ?o } ;
DELETE WHERE { edu:C edu:estEquivalenteA ?o } ;
DELETE WHERE { ?s edu:estEquivalenteA edu:C } ;
# … (label, technologies, inverses) …
INSERT DATA { … mêmes triplets que la création … }
```

### Suppression (DELETE, 204) : triplets sortants puis entrants

```sparql
DELETE WHERE { edu:C ?p ?o } ;
DELETE WHERE { ?s ?p edu:C }
```

La suppression est refusée (409) si une évaluation ne porterait plus sur aucune compétence (axiome `Evaluation ⊑ ∃porteSurCompetence.Competence`) :

```sparql
SELECT ?e WHERE {
    ?e edu:porteSurCompetence edu:C .
    FILTER NOT EXISTS { ?e edu:porteSurCompetence ?autre . FILTER(?autre != edu:C) }
}
```

---

## 2. Technologie – `/api/technologies`

### Liste, filtre par type, recherche

```sparql
SELECT ?id (SAMPLE(?label) AS ?lib) (COUNT(DISTINCT ?c) AS ?nbComp) (COUNT(DISTINCT ?cours) AS ?nbCours) WHERE {
    ?id a/rdfs:subClassOf* edu:Technologie .
    OPTIONAL { ?id rdfs:label ?l }
    BIND(COALESCE(STR(?l), STRAFTER(STR(?id), "#")) AS ?label)
    ?id a/rdfs:subClassOf* edu:TechnologieOutil .              # filtre type
    FILTER(CONTAINS(LCASE(?label), LCASE("git")))               # recherche
    OPTIONAL { ?c (edu:competenceSurTechnologie|^edu:estMobiliseePar) ?id }
    OPTIONAL { ?cours edu:utiliseTechnologie|^edu:estEnseigneeDans ?id }
} GROUP BY ?id ORDER BY ?lib
```

### Chemin de propriété : compétences et cours d'une technologie (lien porté par l'autre classe)

```sparql
SELECT DISTINCT ?x WHERE { ?x edu:competenceSurTechnologie|^edu:estMobiliseePar edu:Tech_Vue }
SELECT DISTINCT ?x WHERE { ?x edu:utiliseTechnologie|^edu:estEnseigneeDans edu:Tech_Git }
```

### Création, modification, suppression

```sparql
INSERT DATA {
    edu:Tech_Svelte a owl:NamedIndividual , edu:FrameworkFrontend .
    edu:Tech_Svelte rdfs:label "Svelte"@fr .
    edu:Comp_JavaScript edu:competenceSurTechnologie edu:Tech_Svelte .
}
```

- **PUT** : supprime `rdfs:label`, le type et `?c edu:competenceSurTechnologie edu:T`, puis réinsère.
- **DELETE** : refusé (409) si un cours n'aurait plus aucune technologie (axiome `Cours ⊑ ∃utiliseTechnologie.Technologie`).

---

## 3. Evaluation – `/api/evaluations`

### Liste avec filtres type, module, compétence, dates et recherche

```sparql
SELECT ?id (SAMPLE(?label) AS ?lib) (SAMPLE(?date) AS ?d) (SAMPLE(?note) AS ?n) (SAMPLE(?coef) AS ?co)
       (GROUP_CONCAT(DISTINCT ?modLabel; separator=", ") AS ?mods) WHERE {
    ?id a/rdfs:subClassOf* edu:Evaluation .
    OPTIONAL { ?id rdfs:label ?l }
    BIND(COALESCE(STR(?l), STRAFTER(STR(?id), "#")) AS ?label)
    OPTIONAL { ?id edu:dateEvaluation ?date }
    ?id a/rdfs:subClassOf* edu:Quiz .                                               # type
    ?id (edu:evaluationDuModule|^edu:estEvalueParEvaluation) edu:Module_NodeJS .    # module
    ?id (edu:porteSurCompetence|^edu:estMesureePar) edu:Comp_NodeJS .               # compétence
    FILTER(BOUND(?date) && ?date >= "2026-10-27T00:00:00"^^xsd:dateTime)            # à venir
    FILTER(BOUND(?date) && ?date <= "2027-01-31T00:00:00"^^xsd:dateTime)
    OPTIONAL { ?id edu:noteMinimale ?note }
    OPTIONAL { ?id edu:coefficient ?coef }
    OPTIONAL { ?id (edu:evaluationDuModule|^edu:estEvalueParEvaluation) ?m . ?m rdfs:label ?modLabel }
} GROUP BY ?id ORDER BY ?d ?lib
```

### Moyenne des notes minimales par type (GET /api/evaluations/statistiques) – AVG + GROUP BY

```sparql
SELECT ?x ?label (COUNT(DISTINCT ?e) AS ?nb) (AVG(?note) AS ?moyenne) (AVG(?coef) AS ?coefMoyen) WHERE {
    ?e a ?x . ?x rdfs:subClassOf* edu:Evaluation .
    ?e edu:noteMinimale ?note .
    OPTIONAL { ?e edu:coefficient ?coef }
    OPTIONAL { ?x rdfs:label ?label }
} GROUP BY ?x ?label ORDER BY DESC(?moyenne)
```

### Création (refusée sans compétence ni module, note entre 0 et 20, coefficient > 0)

```sparql
INSERT DATA {
    edu:Eval_Quiz_Vue a owl:NamedIndividual , edu:QuizEnLigne .
    edu:Eval_Quiz_Vue rdfs:label "Quiz Vue.js"@fr .
    edu:Eval_Quiz_Vue edu:dateEvaluation "2027-04-01T00:00:00"^^xsd:dateTime .
    edu:Eval_Quiz_Vue edu:noteMinimale 10.00 .
    edu:Eval_Quiz_Vue edu:coefficient 1.50 .
    edu:Eval_Quiz_Vue edu:porteSurCompetence edu:Comp_Vue .
    edu:Eval_Quiz_Vue edu:evaluationDuModule edu:Module_React .
    edu:Eval_Quiz_Vue edu:evalue edu:Cours_React .
}
```

- **PUT** : supprime date, note, coefficient, compétences, modules et cours (dans les deux sens des inverses), puis réinsère.
- **DELETE** : sortants puis entrants (le lien `passeEvaluation` des apprenants disparaît avec).

---

## 4. Sécurité

- **Identifiants** : `valid_id()` (regex `^[A-Z][a-zA-Z0-9_]*$`). Un identifiant invalide renvoie 400 avant toute requête.
- **Chaînes** : `lit()` dans `sparql_outils.py` échappe `\`, `"` et les retours à la ligne avant l'insertion.
- **Types** : vérifiés comme sous-classes de la bonne racine (`rdfs:subClassOf+`). Une compétence ne peut donc pas être typée `Formation`.
