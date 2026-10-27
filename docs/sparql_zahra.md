# Requêtes SPARQL — tranche Zahra (Module, Cours, RessourcePedagogique)

Les requêtes sont envoyées à Apache Jena Fuseki (dataset `eduparcours`) via SPARQLWrapper.
Le préfixe `edu:` désigne `http://www.eduparcours.org/ontologie#`.

## Conventions

- Les lectures passent par `sp.select()` (SELECT) ou `sp.ask()` (ASK). Les écritures passent par `sp.update()`.
- Les ids sont validés par l'expression `^[A-Za-z0-9_]+$` avant d'entrer dans une requête.
- Les valeurs texte fournies par l'utilisateur sont échappées (`echapper`) pour éviter l'injection SPARQL.
- Les sous-classes sont prises en compte avec `a/rdfs:subClassOf*`, car Fuseki ne fait pas de raisonnement OWL.
- Les prérequis sont transitifs avec `+`. Les compétences requises combinent `*` (zéro ou plusieurs pas) et `/`.

## Modules

### Lister les modules (filtres q, niveau, pagination)

```sparql
SELECT ?m ?intitule ?duree ?niveau WHERE {
    ?m a/rdfs:subClassOf* edu:Module ;
       edu:intitule ?intitule .
    OPTIONAL { ?m edu:dureeHeures ?duree }
    OPTIONAL { ?m edu:niveauDifficulte ?niveau }
    FILTER(CONTAINS(LCASE(STR(?intitule)), LCASE("...")))   # si q est renseigné
    FILTER(?niveau = "...")                                # si niveau est renseigné
}
ORDER BY ?intitule
LIMIT 20 OFFSET 0
```

Un second `SELECT (COUNT(?m) AS ?n)` avec les mêmes filtres donne le champ `total`.

### Détail d'un module

Trois requêtes : les propriétés du module, ses cours (`edu:contientCours`) et ses prérequis directs (`edu:aPourPrerequis`).

### Prérequis directs et indirects

```sparql
SELECT DISTINCT ?p ?label WHERE {
    edu:Module_Interactivite edu:aPourPrerequis+ ?p .
    OPTIONAL { ?p rdfs:label ?label }
}
```

Le `+` remonte toute la chaîne. Un cycle est donc impossible par construction (voir la création ci-dessous).

### Compétences requises

```sparql
SELECT DISTINCT ?c ?label WHERE {
    edu:Module_Production edu:aPourPrerequis* ?m .
    ?m edu:requiertCompetence ?c .
    OPTIONAL { ?c rdfs:label ?label }
}
```

Le `*` inclut le module lui-même, puis tous ses prérequis, et renvoie les compétences de chacun.

### Créer un module

1. Vérifier que l'id n'existe pas : `ASK { edu:<id> ?p ?o }`.
2. Si un prérequis est donné, vérifier qu'il n'introduit pas de cycle : `ASK { edu:<prerequis> edu:aPourPrerequis+ edu:<prerequis> }`.
3. Insérer le module :

```sparql
INSERT DATA {
    edu:<id> a owl:NamedIndividual, edu:Module ;
        rdfs:label "<intitule>"@fr ;
        edu:intitule "<intitule>"^^xsd:string ;
        edu:dureeHeures <duree> ;
        edu:niveauDifficulte "<niveau>"^^xsd:string .
    edu:<id> edu:aPourPrerequis edu:<prerequis> .   # si prérequis
}
```

### Modifier et supprimer

- Modification : `DELETE { ... } INSERT { ... } WHERE { OPTIONAL { ... } }`, champ par champ.
- Suppression : `DELETE WHERE { edu:<id> ?p ?o }` puis `DELETE WHERE { ?s ?p edu:<id> }`, pour retirer les triplets sortants puis entrants.

## Cours

### Créer un cours

Le cours est relié à son module, son formateur, sa compétence et sa technologie. Le module reçoit aussi le lien inverse `edu:contientCours`.

```sparql
INSERT DATA {
    edu:<id> a owl:NamedIndividual, edu:Cours ;
        rdfs:label "<intitule>"@fr ;
        edu:intitule "<intitule>"^^xsd:string ;
        edu:dureeHeures <duree> ;
        edu:niveauDifficulte "<niveau>"^^xsd:string ;
        edu:ordreDansModule <ordre> ;
        edu:appartientAuModule edu:<moduleId> ;
        edu:enseignePar edu:<formateurId> ;
        edu:developpeCompetence edu:<competenceId> ;
        edu:utiliseTechnologie edu:<technologieId> .
    edu:<moduleId> edu:contientCours edu:<id> .
}
```

Avant l'insertion, le module et le formateur sont vérifiés par `ASK { edu:<id> ?p ?o }`.

### Détail d'un cours

Le détail renvoie le module, le formateur, les compétences, les technologies et les ressources liées au cours.

## Ressources pédagogiques

### Lister les ressources

Les sous-classes de `edu:RessourcePedagogique` sont prises en compte. Les filtres sont optionnels :

- type : `?r a edu:<type>`
- langue : `FILTER(?langue = "...")`
- compétence : `?r edu:ressourceCibleCompetence edu:<competenceId>`
- texte : `CONTAINS(LCASE(STR(?label)), ...)`

### Détail d'une ressource

Le détail renvoie les compétences ciblées (`edu:ressourceCibleCompetence`) et les cours qui utilisent la ressource (`?c edu:utiliseRessource edu:<id>`).

### Créer une ressource

Le type est contrôlé dans l'application (`TYPES_AUTORISES`) avant la requête. L'id est formé de `<type>_<intitule>`.

```sparql
INSERT DATA {
    edu:<id> a owl:NamedIndividual, edu:<type> ;
        rdfs:label "<intitule>"@fr ;
        edu:urlRessource "<url>"^^xsd:string ;
        edu:langue "<langue>"^^xsd:string ;
        edu:ressourceCibleCompetence edu:<competenceId> .
    edu:<id> edu:nombrePages <pages> .        # si renseigné
    edu:<id> edu:dureeMinutes <duree> .       # si renseigné
}
```

## Note sur ASK

Une requête ASK renvoie `{"head": {}, "boolean": true}`, sans clé `results`. Elle ne doit donc pas passer par `sp.select()`, qui lit `results.bindings`. Le client expose une fonction dédiée `sp.ask()` qui renvoie directement le booléen. Cette correction a été nécessaire pour les routes de création, de modification et de suppression.
