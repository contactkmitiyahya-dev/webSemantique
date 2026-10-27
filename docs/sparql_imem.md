# SPARQL – tranche d'Imem (Formation, Parcours)

Préfixes (ajoutés automatiquement par `sparql_client.py`) :

```sparql
PREFIX edu: <http://www.eduparcours.org/ontologie#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

**Règles sans raisonnement** (Fuseki ne contient que les triplets déclarés) :

| Problème | Solution utilisée |
|---|---|
| `Formation_Master_Web` est typée `FormationMaster`, pas `Formation` | `?f a/rdfs:subClassOf* edu:Formation` |
| Les données déclarent tantôt `?f edu:estProposeePar ?o`, tantôt `?o edu:proposeFormation ?f` | `?f edu:estProposeePar\|^edu:proposeFormation ?o` |
| Les inscriptions sont portées par l'apprenant (`edu:estInscritA`) | `?f ^edu:estInscritA\|edu:accueilleApprenant ?a` |
| Ordre des modules d'un parcours | `edu:aPourPrerequis+` (transitivité) |

Paires inverses utilisées : `composeDe/faitPartieDeFormation`, `appartientAuDomaine/regroupeFormation`,
`estProposeePar/proposeFormation`, `estAdministreePar/administreFormation`, `meneA/estObtenueApres`,
`estInscritA/accueilleApprenant`, `parcoursComprend/estEtapeDuParcours`, `estAnimePar/animeParcours`,
`suitParcours/estSuiviPar`.

---

## 1. Catalogue filtré (coût) avec places restantes – `GET /api/formations?cout_max=1000`

```sparql
SELECT ?f ?intitule ?cout ?places ?inscrits ?places_restantes WHERE {
  { SELECT ?f (SAMPLE(?i) AS ?intitule) (SAMPLE(?c) AS ?cout) (SAMPLE(?pl) AS ?places)
           (COUNT(DISTINCT ?a) AS ?inscrits)
    WHERE {
      ?f a/rdfs:subClassOf* edu:Formation ;
         edu:intitule ?i .
      OPTIONAL { ?f edu:coutFormation ?c }
      OPTIONAL { ?f edu:nombrePlaces ?pl }
      OPTIONAL { ?f ^edu:estInscritA|edu:accueilleApprenant ?a }
      FILTER(BOUND(?c) && ?c <= 1000)                       # filtre coût
      FILTER(CONTAINS(LCASE(STR(?i)), LCASE("web")))        # recherche (paramètre q)
    } GROUP BY ?f }
  BIND(?places - ?inscrits AS ?places_restantes)
} ORDER BY ?cout LIMIT 20 OFFSET 0
```

Les autres filtres de l'API ajoutent une ligne au motif :

| Paramètre | Ligne SPARQL |
|---|---|
| `type=BootCamp` | `?f a/rdfs:subClassOf* edu:BootCamp .` |
| `niveau=Avancé` | `FILTER(STR(?n) = "Avancé")` avec `OPTIONAL { ?f edu:niveauDifficulte ?n }` |
| `duree_max=100` | `FILTER(BOUND(?d) && ?d <= 100)` |
| `domaine=Developpement_Web` | `?f edu:appartientAuDomaine\|^edu:regroupeFormation edu:Developpement_Web .` |
| `module=Module_React` | `?f edu:composeDe\|^edu:faitPartieDeFormation edu:Module_React .` |
| `actif=false` | `FILTER(COALESCE(?act, true) = false)` |
| `a_venir=true` | `FILTER(BOUND(?deb) && ?deb > NOW())` |

Le total pour la pagination : même motif avec `SELECT (COUNT(DISTINCT ?f) AS ?total)`.

## 2. Modules d'une formation – `GET /api/formations/{id}` (champ `modules`)

```sparql
SELECT DISTINCT ?module ?libelle WHERE {
  edu:Formation_FullStack edu:composeDe|^edu:faitPartieDeFormation ?module .
  ?module rdfs:label ?libelle .
} ORDER BY ?libelle
```

Fiche complète (toutes les relations en une requête) :

```sparql
SELECT ?rel ?x ?label WHERE {
     { edu:Formation_FullStack edu:composeDe|^edu:faitPartieDeFormation ?x        BIND("modules" AS ?rel) }
  UNION { edu:Formation_FullStack edu:appartientAuDomaine|^edu:regroupeFormation ?x BIND("domaines" AS ?rel) }
  UNION { edu:Formation_FullStack edu:estProposeePar|^edu:proposeFormation ?x     BIND("organismes" AS ?rel) }
  UNION { edu:Formation_FullStack edu:estAdministreePar|^edu:administreFormation ?x BIND("responsables" AS ?rel) }
  UNION { edu:Formation_FullStack edu:meneA|^edu:estObtenueApres ?x               BIND("certification" AS ?rel) }
  UNION { edu:Formation_FullStack ^edu:estInscritA|edu:accueilleApprenant ?x      BIND("inscrits" AS ?rel) }
  OPTIONAL { ?x rdfs:label ?label }
}
```

## 3. Formations futures et actives – `GET /api/formations?a_venir=true&actif=true`

```sparql
SELECT ?f ?intitule ?debut WHERE {
  ?f a/rdfs:subClassOf* edu:Formation ;
     edu:intitule ?intitule ;
     edu:estActif true ;
     edu:dateDebut ?debut .
  FILTER(?debut > NOW())
} ORDER BY ?debut
```

## 4. Parcours avec leurs modules (ordonnés par prérequis) – `GET /api/parcours/{id}`

```sparql
SELECT ?m ?label (COUNT(DISTINCT ?pre) AS ?nbPrerequis) WHERE {
  edu:Parcours_Frontend_Complet edu:parcoursComprend|^edu:estEtapeDuParcours ?m .
  OPTIONAL { ?m edu:aPourPrerequis+ ?pre }          # chemin transitif : prérequis directs et indirects
  ?m rdfs:label ?label .
} GROUP BY ?m ?label ORDER BY ?nbPrerequis ?label
```

Liste des parcours avec nombre de modules, d'apprenants et animateurs :

```sparql
SELECT ?p (SAMPLE(?l) AS ?label) (COUNT(DISTINCT ?m) AS ?nbModules) (COUNT(DISTINCT ?a) AS ?nbApprenants) WHERE {
  ?p a/rdfs:subClassOf* edu:Parcours ; rdfs:label ?l .
  OPTIONAL { ?p edu:parcoursComprend|^edu:estEtapeDuParcours ?m }
  OPTIONAL { ?p ^edu:suitParcours|edu:estSuiviPar ?a }
} GROUP BY ?p ORDER BY ?label
```

## 5. CRUD Formation

**Créer** (`POST /api/formations`, 201). Avant l'insertion, l'API vérifie : au moins un module, au moins
un domaine, au plus une certification, coût ≥ 0, fin > début, chaque référence existe dans la bonne classe
(`ASK`/`VALUES` + `a/rdfs:subClassOf*`), l'id n'existe pas (sinon 409). Les chaînes passent par `esc()`.

```sparql
INSERT DATA {
  edu:Formation_Atelier_Vue a owl:NamedIndividual , edu:AtelierIntensif ;
    rdfs:label "Atelier Vue"@fr ;
    edu:intitule "Atelier Vue"^^xsd:string ;
    edu:estActif "true"^^xsd:boolean ;
    edu:dureeHeures "30"^^xsd:integer ;
    edu:coutFormation "250.0"^^xsd:decimal ;
    edu:dateDebut "2027-03-01T00:00:00"^^xsd:dateTime ;
    edu:dateFin "2027-03-26T00:00:00"^^xsd:dateTime ;
    edu:composeDe edu:Module_JavaScript ;
    edu:appartientAuDomaine edu:Domaine_Frontend .
}
```

Contrôle d'existence de l'identifiant (409) :

```sparql
ASK { { edu:Formation_Atelier_Vue ?p ?o } UNION { ?s ?p edu:Formation_Atelier_Vue } }
```

**Modifier** (`PUT`, 200) : remplacement complet des propriétés gérées, dans les deux sens, en une
seule requête (transaction Fuseki). Les inscriptions des apprenants ne sont pas touchées.

```sparql
DELETE { edu:Formation_Atelier_Vue ?p ?o } WHERE {
  edu:Formation_Atelier_Vue ?p ?o .
  VALUES ?p { edu:intitule edu:coutFormation edu:composeDe edu:appartientAuDomaine edu:meneA rdfs:label # …
  }
} ;
DELETE { edu:Formation_Atelier_Vue a ?t } WHERE { edu:Formation_Atelier_Vue a ?t . ?t rdfs:subClassOf* edu:Formation } ;
DELETE { ?s ?p edu:Formation_Atelier_Vue } WHERE {
  ?s ?p edu:Formation_Atelier_Vue .
  VALUES ?p { edu:faitPartieDeFormation edu:regroupeFormation edu:proposeFormation edu:administreFormation edu:estObtenueApres }
} ;
INSERT DATA { edu:Formation_Atelier_Vue edu:coutFormation "0.0"^^xsd:decimal ; … }
```

**Supprimer** (`DELETE`, 204) : triplets sortants puis entrants.

```sparql
DELETE WHERE { edu:Formation_Atelier_Vue ?p ?o } ;
DELETE WHERE { ?s ?p edu:Formation_Atelier_Vue }
```

Le CRUD Parcours suit le même modèle (`parcoursComprend` obligatoire, `estAnimePar` vers un `Formateur`).

## 6. Recherche globale – `GET /api/recherche?q=react`

```sparql
SELECT ?x (SAMPLE(?lab) AS ?label) (SAMPLE(?cat) AS ?categorie) WHERE {
  ?x a owl:NamedIndividual .
  { ?x edu:intitule ?lab } UNION { ?x rdfs:label ?lab }
  FILTER(CONTAINS(LCASE(STR(?lab)), LCASE("react")))
  VALUES ?cat { edu:Formation edu:Parcours edu:Module edu:Cours edu:Competence edu:Apprenant # …
  }
  ?x a/rdfs:subClassOf* ?cat .
} GROUP BY ?x ORDER BY ?categorie ?label
```

## 7. Questions NLP (gabarits de `backend/app/nlp/imem.py`)

| Intention | Exemple | Requête produite (résumé) |
|---|---|---|
| LISTER_FORMATIONS | Quelles sont les formations disponibles ? | `?f a/rdfs:subClassOf* edu:Formation ; edu:intitule ?i` |
| FILTRE_COUT | Quelles formations coûtent moins de 1000 dinars ? | + `FILTER(?cout <= 1000)` (« plus de » → `>=`, « gratuit » → `= 0`, « entre a et b ») |
| FILTRE_NIVEAU | Quelles formations sont de niveau avancé ? | + `FILTER(STR(?niveau) = "Avancé")` |
| FORMATIONS_ACTIVES | Quelles formations sont actives ? | + `?f edu:estActif true` (+ `?debut > NOW()` si « à venir ») |
| COMPTER_MODULES | Combien de modules compte la formation Développement Full-Stack ? | `COUNT(DISTINCT ?m)` sur `composeDe\|^faitPartieDeFormation` |
| MODULES_FORMATION | Quels modules composent la formation Front-end ? | `edu:Formation_Frontend edu:composeDe\|^edu:faitPartieDeFormation ?m` |
| CERTIF_FORMATION | Quelle certification obtient-on après la formation back-end ? | `edu:meneA\|^edu:estObtenueApres ?c` + organisme |
| PARCOURS_APPRENANT | Quel parcours suit Ahmed ? | `edu:Ahmed edu:suitParcours\|^edu:estSuiviPar ?p` |
