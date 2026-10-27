# Requêtes SPARQL – tranche d'Ala

**Classes :** Formateur, ResponsableFormation + ServiceScolarite, Organisme, Domaine.

Toutes les requêtes ont été **exécutées contre Fuseki** (dataset `eduparcours`, ontologie + `data/membre_ala.ttl`).
Sous chaque requête : un extrait du résultat réel (identifiants `edu:` affichés en nom local, comme le renvoie `sparql_client.py`).
Les requêtes de création / modification / suppression ont été jouées sur des individus d'exemple, vérifiées, puis supprimées :
le nombre de triplets est revenu à sa valeur de départ (voir la fin du document).

## Préfixes

Ajoutés automatiquement par `sparql_client.py` ; à recopier pour tester dans l'interface de Fuseki (http://localhost:3030).

```sparql
PREFIX edu: <http://www.eduparcours.org/ontologie#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

## Chemins de propriété utilisés (pas de raisonnement dans Fuseki)

Fuseki ne contient que les triplets écrits, pas ceux que HermiT déduirait. Les chemins SPARQL compensent :

| Chemin | Exemple | Rôle |
|---|---|---|
| `/` (séquence) | `?f a/rdfs:subClassOf* edu:Formateur` | enchaîne deux propriétés : « le type de ?f, puis ses super-classes ». |
| `*` (zéro ou plus) | `rdfs:subClassOf*` | remonte toute la hiérarchie (0, 1, 2… niveaux) : un `FormateurSenior` est trouvé comme `Formateur` sans raisonneur. |
| `+` (un ou plus) | `rdfs:subClassOf+` | comme `*` mais au moins un niveau : sert à trouver les sous-classes strictes (type le plus spécifique). |
| `^` (inverse) | `^edu:enseigne` | parcourt la propriété à l'envers : `?c ^edu:enseigne ?f` équivaut à `?f edu:enseigne ?c`. |
| `\|` (alternative) | `edu:enseignePar\|^edu:enseigne` | accepte l'un OU l'autre chemin : le lien est trouvé quel que soit le sens dans lequel il a été écrit dans les données. |

**Pourquoi `|` est indispensable ici :** dans les données, une même relation est écrite tantôt dans un sens, tantôt dans l'autre
(ex. `EduParcours_Academie edu:proposeFormation Formation_FullStack` mais `Formation_Backend edu:estProposeePar EduParcours_Academie`).
Avec un seul sens, on perdrait la moitié des résultats ; `owl:inverseOf` n'est pas appliqué par Fuseki.

**Type le plus spécifique :** un individu a souvent `owl:NamedIndividual` + sa classe. Le motif suivant garde la classe la plus précise :

```sparql
?x a ?type . ?type rdfs:subClassOf* edu:Formateur .
FILTER NOT EXISTS { ?x a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
```

## 1. Formateur

#### 1.1 Liste (avec type le plus spécifique)

Tous les formateurs, sous-classes comprises (`a/rdfs:subClassOf*`), triés par nom, paginés.

```sparql
SELECT ?f ?nom ?prenom ?type ?specialite ?experience WHERE {
  ?f a/rdfs:subClassOf* edu:Formateur ; edu:nom ?nom .
  ?f a ?type . ?type rdfs:subClassOf* edu:Formateur .
  FILTER NOT EXISTS { ?f a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
  OPTIONAL { ?f edu:prenom ?prenom }
  OPTIONAL { ?f edu:specialiteFormateur ?specialite }
  OPTIONAL { ?f edu:anneesExperience ?experience }
} ORDER BY ?nom LIMIT 20 OFFSET 0
```

**Résultat réel :**

| f | nom | prenom | type | specialite | experience |
|---|---|---|---|---|---|
| Mme_Ayari | Ayari | Ines | FormateurPermanent | Génie logiciel et agilité | 8 |
| Dr_Benali | Benali | Dr. | FormateurSenior | Développement web | 12 |
| Mme_Bouazizi | Bouazizi | Rania | FormateurInvite | Méthodes agiles | 6 |
| Mr_Cherif | Cherif | Walid | FormateurInvite | DevOps | 5 |
| Mr_Ferchichi | Ferchichi | Bilel | FormateurJunior | Intégration front-end | 2 |
| Mr_Gharbi | Gharbi | Hatem | FormateurExpertIndustrie | DevOps | 10 |
| Mr_Hamdi | Hamdi | Youssef | FormateurJunior | Front-end | 2 |
| Mr_Jaziri | Jaziri | Anis | FormateurExpertIndustrie | DevOps et cloud | 10 |

_… 3 autres lignes (11 au total)_

#### 1.2 Détail : propriétés

Toutes les propriétés littérales d'un formateur (ici `Dr_Mansouri`).

```sparql
SELECT ?propriete ?valeur WHERE {
  edu:Dr_Mansouri ?propriete ?valeur .
  FILTER(isLiteral(?valeur))
} ORDER BY ?propriete
```

**Résultat réel :**

| propriete | valeur |
|---|---|
| anneesExperience | 15 |
| email | hichem.mansouri@eduparcours.org |
| nom | Mansouri |
| prenom | Hichem |
| specialiteFormateur | Développement back-end |
| telephone | +216 71 100 201 |
| http://www.w3.org/2000/01/rdf-schema#label | Dr. Mansouri |

_7 ligne(s)_

#### 1.3 Détail : relations (cours, apprenants, parcours) – chemins à deux sens

Une seule requête avec `UNION` ; chaque relation est lue dans les deux sens avec `|` et `^`.

```sparql
SELECT DISTINCT ?relation ?id ?label WHERE {
  { ?id (edu:enseignePar|^edu:enseigne) edu:Dr_Mansouri . BIND("cours" AS ?relation) }
  UNION
  { ?id (edu:estEncadrePar|^edu:encadre) edu:Dr_Mansouri . BIND("apprenant" AS ?relation) }
  UNION
  { ?id (edu:estAnimePar|^edu:animeParcours) edu:Dr_Mansouri . BIND("parcours" AS ?relation) }
  OPTIONAL { ?id edu:intitule ?intitule }
  OPTIONAL { ?id rdfs:label ?libelle }
  BIND(COALESCE(?intitule, ?libelle) AS ?label)   # un seul libellé : intitulé en priorité
} ORDER BY ?relation ?id
```

**Résultat réel :**

| relation | id | label |
|---|---|---|
| apprenant | Lina_Master | Lina |
| cours | Cours_Express | Express et API REST |
| cours | Cours_NodeJS | Node.js |
| cours | Cours_SQL | Bases de données SQL |

_4 ligne(s)_

#### 1.4 Filtre : par type (sous-classes comprises) et spécialité

Formateurs vacataires (`FormateurVacataire` et ses sous-classes `FormateurExpertIndustrie`, `FormateurInvite`).

```sparql
SELECT ?f ?nom ?specialite WHERE {
  ?f a/rdfs:subClassOf* edu:FormateurVacataire ; edu:nom ?nom .
  OPTIONAL { ?f edu:specialiteFormateur ?specialite }
} ORDER BY ?nom
```

**Résultat réel :**

| f | nom | specialite |
|---|---|---|
| Mme_Bouazizi | Bouazizi | Méthodes agiles |
| Mr_Cherif | Cherif | DevOps |
| Mr_Gharbi | Gharbi | DevOps |
| Mr_Jaziri | Jaziri | DevOps et cloud |
| Mme_Trabelsi | Trabelsi | Bases de données |

_5 ligne(s)_

#### 1.5 Recherche par nom ou prénom (insensible à la casse)

`LCASE` des deux côtés ; `COALESCE` car le prénom peut manquer. Recherche de « MANS » → trouve Mansouri.

```sparql
SELECT ?f ?prenom ?nom WHERE {
  ?f a/rdfs:subClassOf* edu:Formateur ; edu:nom ?nom .
  OPTIONAL { ?f edu:prenom ?prenom }
  FILTER( CONTAINS(LCASE(CONCAT(COALESCE(?prenom, ""), " ", ?nom)), LCASE("MANS")) )
}
```

**Résultat réel :**

| f | prenom | nom |
|---|---|---|
| Dr_Mansouri | Hichem | Mansouri |

_1 ligne(s)_

#### 1.6 Chemin de propriété : apprenants encadrés par un formateur

`edu:estEncadrePar|^edu:encadre` : Dr_Benali est référencé par les apprenants (`estEncadrePar`), Dr_Mansouri écrit lui-même `encadre`.

```sparql
SELECT ?formateur ?apprenant WHERE {
  VALUES ?formateur { edu:Dr_Benali edu:Dr_Mansouri edu:Mr_Ferchichi }
  ?apprenant (edu:estEncadrePar|^edu:encadre) ?formateur .
} ORDER BY ?formateur ?apprenant
```

**Résultat réel :**

| formateur | apprenant |
|---|---|
| Dr_Benali | Ahmed |
| Dr_Benali | Nour |
| Dr_Benali | Omar |
| Dr_Benali | Sarra |
| Dr_Mansouri | Lina_Master |
| Mr_Ferchichi | Yassine |

_6 ligne(s)_

#### 1.7 Formateurs expérimentés (expérience ≥ N) avec nombre de cours

`COUNT` + `GROUP BY`, chemin à deux sens. `OPTIONAL` pour garder un formateur sans cours (compte 0). Ici N = 10.

```sparql
SELECT ?f ?nom ?experience (COUNT(DISTINCT ?c) AS ?nbCours) WHERE {
  ?f a/rdfs:subClassOf* edu:Formateur ; edu:nom ?nom ; edu:anneesExperience ?experience .
  FILTER(?experience >= 10)
  OPTIONAL { ?c (edu:enseignePar|^edu:enseigne) ?f }
} GROUP BY ?f ?nom ?experience
ORDER BY DESC(?experience)
```

**Résultat réel :**

| f | nom | experience | nbCours |
|---|---|---|---|
| Dr_Mansouri | Mansouri | 15 | 3 |
| Dr_Benali | Benali | 12 | 6 |
| Mme_Jebali | Jebali | 11 | 1 |
| Mr_Gharbi | Gharbi | 10 | 1 |
| Mr_Jaziri | Jaziri | 10 | 2 |

_5 ligne(s)_

#### 1.8 Classe définie FormateurPolyvalent (≥ 3 cours) reproduite par une requête

Dans l'ontologie : `FormateurPolyvalent ≡ Formateur ⊓ (enseigne min 3 Cours)`. HermiT la déduit dans Protégé,
mais Fuseki ne raisonne pas : on la reproduit avec `COUNT` + `HAVING` (le filtre `HAVING` porte sur le résultat de l'agrégat,
alors que `FILTER` porte sur les lignes avant regroupement).

```sparql
SELECT ?f ?nom (COUNT(DISTINCT ?c) AS ?nbCours) WHERE {
  ?f a/rdfs:subClassOf* edu:Formateur ; edu:nom ?nom .
  ?c a/rdfs:subClassOf* edu:Cours ;
     (edu:enseignePar|^edu:enseigne) ?f .
} GROUP BY ?f ?nom
HAVING (COUNT(DISTINCT ?c) >= 3)
ORDER BY DESC(?nbCours)
```

**Résultat réel :**

| f | nom | nbCours |
|---|---|---|
| Dr_Benali | Benali | 6 |
| Dr_Mansouri | Mansouri | 3 |

_2 ligne(s)_

#### 1.9 Existence d'un identifiant (avant création → 409)

Utilisé par l'API avant un POST : si vrai, l'id est déjà pris.

```sparql
ASK { edu:Dr_Mansouri ?p ?o }
```

**Résultat réel :** `True`

#### 1.10 Création

Un seul type feuille + `owl:NamedIndividual`, un seul `edu:nom`. Chaînes typées `xsd:string`, entier sans guillemets.

```sparql
INSERT DATA {
  edu:Mme_Nasri a owl:NamedIndividual, edu:FormateurJunior ;
    rdfs:label "Mme Nasri"@fr ;
    edu:nom "Nasri"^^xsd:string ;
    edu:prenom "Sonia"^^xsd:string ;
    edu:email "sonia.nasri@eduparcours.org"^^xsd:string ;
    edu:specialiteFormateur "Front-end"^^xsd:string ;
    edu:anneesExperience 1 ;
    edu:enseigne edu:Cours_React .
}
```

Vérification :

```sparql
SELECT ?nom ?prenom ?experience WHERE { edu:Mme_Nasri edu:nom ?nom ; edu:prenom ?prenom ; edu:anneesExperience ?experience }
```

| nom | prenom | experience |
|---|---|---|
| Nasri | Sonia | 1 |

_1 ligne(s)_

#### 1.11 Modification (remplace, n'ajoute jamais une deuxième valeur)

`DELETE` l'ancienne valeur puis `INSERT` la nouvelle dans la même requête. `OPTIONAL` dans le `WHERE` : la modification
fonctionne même si la propriété n'existait pas encore. C'est ce qui garantit **un seul `edu:nom`**.

```sparql
DELETE { edu:Mme_Nasri edu:nom ?ancienNom . edu:Mme_Nasri edu:anneesExperience ?ancienneExp }
INSERT { edu:Mme_Nasri edu:nom "Nasri-Ben Salah"^^xsd:string . edu:Mme_Nasri edu:anneesExperience 3 }
WHERE {
  OPTIONAL { edu:Mme_Nasri edu:nom ?ancienNom }
  OPTIONAL { edu:Mme_Nasri edu:anneesExperience ?ancienneExp }
}
```

Vérification :

```sparql
SELECT (COUNT(?n) AS ?nbNoms) (SAMPLE(?n) AS ?valeurNom) (SAMPLE(?e) AS ?experience) WHERE { edu:Mme_Nasri edu:nom ?n ; edu:anneesExperience ?e }
```

| nbNoms | valeurNom | experience |
|---|---|---|
| 1 | Nasri-Ben Salah | 3 |

_1 ligne(s)_

#### 1.12 Suppression (triplets sortants puis entrants)

Deux opérations séparées par `;`. La seconde supprime les liens qui pointent vers le formateur (ex. `Cours_React edu:enseignePar edu:Mme_Nasri`) : aucun lien orphelin.

```sparql
DELETE WHERE { edu:Mme_Nasri ?p ?o } ;
DELETE WHERE { ?s ?p edu:Mme_Nasri }
```

Vérification :

```sparql
ASK { { edu:Mme_Nasri ?p ?o } UNION { ?s ?p edu:Mme_Nasri } }
```

**Résultat réel :** `False`

## 2. Personnel : ResponsableFormation et ServiceScolarite
Les deux classes sont sous `edu:PersonnelAdministratif` et sont **disjointes** : un agent de scolarité ne peut pas administrer une formation (domaine de `administreFormation` = `ResponsableFormation`).

#### 2.1 Liste (responsables et scolarité)

Avec la catégorie (`ResponsableFormation` ou `ServiceScolarite`) et le type le plus spécifique.

```sparql
SELECT ?p ?nom ?prenom ?categorie ?type WHERE {
  VALUES ?categorie { edu:ResponsableFormation edu:ServiceScolarite }
  ?p a/rdfs:subClassOf* ?categorie ; edu:nom ?nom .
  ?p a ?type . ?type rdfs:subClassOf* edu:PersonnelAdministratif .
  FILTER NOT EXISTS { ?p a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
  OPTIONAL { ?p edu:prenom ?prenom }
} ORDER BY ?categorie ?nom
```

**Résultat réel :**

| p | nom | prenom | categorie | type |
|---|---|---|---|---|
| Mr_Dridi | Dridi | Sami | ResponsableFormation | ResponsablePedagogique |
| Mme_Karoui | Karoui | Nadia | ResponsableFormation | ResponsableDeFormation |
| Mme_Salhi | Salhi | Leila | ResponsableFormation | ResponsableDeFormation |
| Mr_Zouari | Zouari | Mehdi | ResponsableFormation | ResponsablePedagogique |
| Mr_BenAmor | Ben Amor | Fares | ServiceScolarite | GestionnaireInscription |
| Mme_Gharsalli | Gharsalli | Amel | ServiceScolarite | AgentScolarite |
| Mme_Hamrouni | Hamrouni | Salma | ServiceScolarite | GestionnaireInscription |

_7 ligne(s)_

#### 2.2 Filtre : par type

Paramètre `type` de l'API (ici `ResponsablePedagogique`).

```sparql
SELECT ?p ?nom ?email WHERE {
  ?p a/rdfs:subClassOf* edu:ResponsablePedagogique ; edu:nom ?nom .
  OPTIONAL { ?p edu:email ?email }
}
```

**Résultat réel :**

| p | nom | email |
|---|---|---|
| Mr_Dridi | Dridi | sami.dridi@eduparcours.org |
| Mr_Zouari | Zouari | mehdi.zouari@eduparcours.org |

_2 ligne(s)_

#### 2.3 Détail : propriétés

Propriétés littérales de `Mme_Salhi` (prénom ajouté dans `membre_ala.ttl`).

```sparql
SELECT ?propriete ?valeur WHERE {
  edu:Mme_Salhi ?propriete ?valeur . FILTER(isLiteral(?valeur))
} ORDER BY ?propriete
```

**Résultat réel :**

| propriete | valeur |
|---|---|
| nom | Salhi |
| prenom | Leila |
| http://www.w3.org/2000/01/rdf-schema#label | Mme Salhi |

_3 ligne(s)_

#### 2.4 Chemin de propriété : formations administrées (deux sens)

`Mme_Salhi` écrit `administreFormation` ; `Mr_Dridi` n'apparaît que via `Formation_X edu:estAdministreePar edu:Mr_Dridi`. Le chemin `|` trouve les deux.

```sparql
SELECT ?responsable ?formation ?intitule WHERE {
  ?responsable a/rdfs:subClassOf* edu:ResponsableFormation .
  ?formation (edu:estAdministreePar|^edu:administreFormation) ?responsable .
  OPTIONAL { ?formation edu:intitule ?intitule }
} ORDER BY ?responsable ?formation
```

**Résultat réel :**

| responsable | formation | intitule |
|---|---|---|
| Mme_Karoui | BootCamp_Web | Bootcamp Web |
| Mme_Salhi | Formation_Angular | Spécialisation Angular |
| Mme_Salhi | Formation_Frontend | Formation Front-end |
| Mme_Salhi | Formation_FullStack | Développement Full-Stack |
| Mme_Salhi | Formation_Git_Collab | Bootcamp Git et agilité |
| Mr_Dridi | Formation_Backend | Développement back-end |
| Mr_Dridi | Formation_Debutant_Web | Initiation au web |
| Mr_Dridi | Formation_Master_Web | Master spécialisé web |

_… 1 autres lignes (9 au total)_

#### 2.5 Recherche par nom ou prénom (insensible à la casse)

Recherche de « sa » → Salhi, Sami Dridi, Salma Hamrouni…

```sparql
SELECT ?p ?prenom ?nom WHERE {
  ?p a/rdfs:subClassOf* edu:PersonnelAdministratif ; edu:nom ?nom .
  OPTIONAL { ?p edu:prenom ?prenom }
  FILTER( CONTAINS(LCASE(CONCAT(COALESCE(?prenom, ""), " ", ?nom)), LCASE("sa")) )
} ORDER BY ?nom
```

**Résultat réel :**

| p | prenom | nom |
|---|---|---|
| Mr_Dridi | Sami | Dridi |
| Mme_Gharsalli | Amel | Gharsalli |
| Mme_Hamrouni | Salma | Hamrouni |
| Mme_Salhi | Leila | Salhi |

_4 ligne(s)_

#### 2.6 Création

Agent de scolarité (aucune relation : il n'administre pas de formation).

```sparql
INSERT DATA {
  edu:Mr_Saidi a owl:NamedIndividual, edu:AgentScolarite ;
    rdfs:label "M. Saidi"@fr ;
    edu:nom "Saidi"^^xsd:string ;
    edu:prenom "Karim"^^xsd:string ;
    edu:email "karim.saidi@eduparcours.org"^^xsd:string .
}
```

Vérification :

```sparql
SELECT ?type ?nom WHERE { edu:Mr_Saidi a ?type ; edu:nom ?nom FILTER(?type != owl:NamedIndividual) }
```

| type | nom |
|---|---|
| AgentScolarite | Saidi |

_1 ligne(s)_

#### 2.7 Modification (email)

Même principe : supprimer l'ancienne valeur, insérer la nouvelle.

```sparql
DELETE { edu:Mr_Saidi edu:email ?ancien }
INSERT { edu:Mr_Saidi edu:email "k.saidi@eduparcours.org"^^xsd:string }
WHERE { OPTIONAL { edu:Mr_Saidi edu:email ?ancien } }
```

Vérification :

```sparql
SELECT ?email WHERE { edu:Mr_Saidi edu:email ?email }
```

| email |
|---|
| k.saidi@eduparcours.org |

_1 ligne(s)_

#### 2.8 Suppression

Sortants puis entrants.

```sparql
DELETE WHERE { edu:Mr_Saidi ?p ?o } ;
DELETE WHERE { ?s ?p edu:Mr_Saidi }
```

Vérification :

```sparql
ASK { { edu:Mr_Saidi ?p ?o } UNION { ?s ?p edu:Mr_Saidi } }
```

**Résultat réel :** `False`

## 3. Organisme

#### 3.1 Liste

Libellé (`rdfs:label`) et type le plus spécifique.

```sparql
SELECT ?o ?label ?type WHERE {
  ?o a/rdfs:subClassOf* edu:Organisme ; rdfs:label ?label .
  ?o a ?type . ?type rdfs:subClassOf* edu:Organisme .
  FILTER NOT EXISTS { ?o a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
} ORDER BY ?label
```

**Résultat réel :**

| o | label | type |
|---|---|---|
| EduParcours_Academie | EduParcours Académie | AcademieEnLigne |
| MOOC_FrontendPro | MOOC Front-end Pro | MOOC |
| MOOC_WebDev | MOOC Web Dev | MOOC |
| Ministere_Enseignement | Ministère de l'Enseignement | MinistereFormation |
| Ministere_FormationPro | Ministère de la Formation professionnelle | MinistereFormation |
| Universite_Sfax | Université de Sfax | Universite |
| Universite_Tunis | Université de Tunis | Universite |
| Ecole_Esprit | École supérieure d'ingénieurs | EcoleSuperieure |

_… 2 autres lignes (10 au total)_

#### 3.2 Organismes par type (GROUP BY)

Nombre d'organismes par type le plus spécifique.

```sparql
SELECT ?type (COUNT(?o) AS ?nombre) WHERE {
  ?o a/rdfs:subClassOf* edu:Organisme .
  ?o a ?type . ?type rdfs:subClassOf* edu:Organisme .
  FILTER NOT EXISTS { ?o a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
} GROUP BY ?type ORDER BY DESC(?nombre) ?type
```

**Résultat réel :**

| type | nombre |
|---|---|
| EditeurTechnologique | 2 |
| MOOC | 2 |
| MinistereFormation | 2 |
| Universite | 2 |
| AcademieEnLigne | 1 |
| EcoleSuperieure | 1 |

_6 ligne(s)_

#### 3.3 Filtre : organismes certificateurs (sous-classes comprises)

`OrganismeCertificateur` regroupe `CertificateurPublic` (→ `MinistereFormation`) et `CertificateurPrive` (→ `EditeurTechnologique`).

```sparql
SELECT ?o ?label WHERE {
  ?o a/rdfs:subClassOf* edu:OrganismeCertificateur ; rdfs:label ?label .
} ORDER BY ?label
```

**Résultat réel :**

| o | label |
|---|---|
| Ministere_Enseignement | Ministère de l'Enseignement |
| Ministere_FormationPro | Ministère de la Formation professionnelle |
| Editeur_DevTools | Éditeur DevTools |
| Editeur_Cloud | Éditeur technologique cloud |

_4 ligne(s)_

#### 3.4 Détail : formations proposées et certifications délivrées (deux sens)

Pour `EduParcours_Academie` : certaines formations sont reliées par `proposeFormation`, d'autres par `estProposeePar`.

```sparql
SELECT DISTINCT ?relation ?id ?label WHERE {
  { ?id (edu:estProposeePar|^edu:proposeFormation) edu:EduParcours_Academie . BIND("formation" AS ?relation) }
  UNION
  { ?id (edu:delivreeParOrganisme|^edu:delivreCertification) edu:EduParcours_Academie . BIND("certification" AS ?relation) }
  OPTIONAL { ?id edu:intitule ?intitule }
  OPTIONAL { ?id rdfs:label ?libelle }
  BIND(COALESCE(?intitule, ?libelle) AS ?label)   # un seul libellé : intitulé en priorité
} ORDER BY ?relation ?id
```

**Résultat réel :**

| relation | id | label |
|---|---|---|
| certification | Attestation_Module_React | Attestation module React |
| certification | Certificat_DeveloppeurWeb | Certificat Développeur Web |
| certification | Certificat_Frontend | Certificat Développeur Front-end |
| formation | BootCamp_Web | Bootcamp Web |
| formation | Formation_Backend | Développement back-end |
| formation | Formation_Frontend | Formation Front-end |
| formation | Formation_FullStack | Développement Full-Stack |
| formation | Formation_Git_Collab | Bootcamp Git et agilité |

_8 ligne(s)_

#### 3.5 Formations proposées par un organisme : pourquoi le chemin à deux sens

Comparaison du nombre de formations trouvées selon le chemin utilisé, pour `EduParcours_Academie`.

```sparql
SELECT ?chemin (COUNT(DISTINCT ?f) AS ?nbFormations) WHERE {
  { ?f edu:estProposeePar edu:EduParcours_Academie . BIND("estProposeePar seul" AS ?chemin) }
  UNION
  { edu:EduParcours_Academie edu:proposeFormation ?f . BIND("proposeFormation seul" AS ?chemin) }
  UNION
  { ?f (edu:estProposeePar|^edu:proposeFormation) edu:EduParcours_Academie . BIND("deux sens (|, ^)" AS ?chemin) }
} GROUP BY ?chemin ORDER BY ?chemin
```

**Résultat réel :**

| chemin | nbFormations |
|---|---|
| deux sens (\|, ^) | 5 |
| estProposeePar seul | 2 |
| proposeFormation seul | 3 |

_3 ligne(s)_

#### 3.6 Recherche par libellé (insensible à la casse)

Recherche de « univ ».

```sparql
SELECT ?o ?label WHERE {
  ?o a/rdfs:subClassOf* edu:Organisme ; rdfs:label ?label .
  FILTER( CONTAINS(LCASE(STR(?label)), LCASE("univ")) )
}
```

**Résultat réel :**

| o | label |
|---|---|
| Universite_Tunis | Université de Tunis |
| Universite_Sfax | Université de Sfax |

_2 ligne(s)_

#### 3.7 Création

Organisme de formation (MOOC) qui propose une formation existante.

```sparql
INSERT DATA {
  edu:MOOC_Exemple a owl:NamedIndividual, edu:MOOC ;
    rdfs:label "MOOC Exemple"@fr ;
    edu:proposeFormation edu:Formation_Angular .
}
```

Vérification :

```sparql
SELECT ?label ?formation WHERE { edu:MOOC_Exemple rdfs:label ?label ; edu:proposeFormation ?formation }
```

| label | formation |
|---|---|
| MOOC Exemple | Formation_Angular |

_1 ligne(s)_

#### 3.8 Modification (libellé)

Le libellé garde sa langue `@fr`.

```sparql
DELETE { edu:MOOC_Exemple rdfs:label ?ancien }
INSERT { edu:MOOC_Exemple rdfs:label "MOOC Exemple (édition 2026)"@fr }
WHERE { OPTIONAL { edu:MOOC_Exemple rdfs:label ?ancien } }
```

Vérification :

```sparql
SELECT ?label WHERE { edu:MOOC_Exemple rdfs:label ?label }
```

| label |
|---|
| MOOC Exemple (édition 2026) |

_1 ligne(s)_

#### 3.9 Suppression

Sortants puis entrants.

```sparql
DELETE WHERE { edu:MOOC_Exemple ?p ?o } ;
DELETE WHERE { ?s ?p edu:MOOC_Exemple }
```

Vérification :

```sparql
ASK { { edu:MOOC_Exemple ?p ?o } UNION { ?s ?p edu:MOOC_Exemple } }
```

**Résultat réel :** `False`

## 4. Domaine

#### 4.1 Liste

Intitulé et type le plus spécifique.

```sparql
SELECT ?d ?intitule ?type WHERE {
  ?d a/rdfs:subClassOf* edu:Domaine ; edu:intitule ?intitule .
  ?d a ?type . ?type rdfs:subClassOf* edu:Domaine .
  FILTER NOT EXISTS { ?d a ?autre . ?autre rdfs:subClassOf+ ?type . FILTER(?autre != ?type) }
} ORDER BY ?intitule
```

**Résultat réel :**

| d | intitule | type |
|---|---|---|
| Analyse_Donnees | Analyse de données | AnalyseDeDonnees |
| Domaine_IA | Apprentissage automatique | ApprentissageAutomatique |
| Design_UX | Design UX | UXDesign |
| Domaine_UI | Design d'interface (UI) | UIDesign |
| Domaine_Backend | Développement back-end | DeveloppementBackend |
| Domaine_Frontend | Développement front-end | DeveloppementFrontend |
| Domaine_FullStack | Développement full-stack | DeveloppementFullStack |
| Developpement_Web | Développement web | DeveloppementWeb |

_8 ligne(s)_

#### 4.2 Formations regroupées par domaine (deux sens, GROUP BY)

`GROUP_CONCAT` liste les formations de chaque domaine sur une ligne ; `STRAFTER` garde le nom local.

```sparql
SELECT ?d (COUNT(DISTINCT ?f) AS ?nbFormations)
       (GROUP_CONCAT(DISTINCT STRAFTER(STR(?f), "#"); separator=", ") AS ?formations) WHERE {
  ?d a/rdfs:subClassOf* edu:Domaine .
  OPTIONAL { ?f (edu:appartientAuDomaine|^edu:regroupeFormation) ?d }
} GROUP BY ?d ORDER BY DESC(?nbFormations)
```

**Résultat réel :**

| d | nbFormations | formations |
|---|---|---|
| Developpement_Web | 6 | Formation_Master_Web, Formation_FullStack, Formation_Debutant_Web, BootCamp_Web, Formation_Frontend, Atelier_HTML_CSS |
| Domaine_FullStack | 2 | Formation_FullStack, BootCamp_Web |
| Domaine_Backend | 2 | Formation_Git_Collab, Formation_Backend |
| Domaine_Frontend | 1 | Formation_Angular |
| Domaine_UI | 1 | Formation_Frontend |
| Domaine_IA | 1 | Formation_Master_Web |
| Analyse_Donnees | 0 |  |
| Design_UX | 0 |  |

_8 ligne(s)_

#### 4.3 Filtre : domaines informatiques (sous-classes comprises)

`DomaineInformatique` → `DeveloppementWeb`, `DonneesEtIA` et leurs sous-classes ; exclut le design.

```sparql
SELECT ?d ?intitule WHERE {
  ?d a/rdfs:subClassOf* edu:DomaineInformatique ; edu:intitule ?intitule .
} ORDER BY ?intitule
```

**Résultat réel :**

| d | intitule |
|---|---|
| Analyse_Donnees | Analyse de données |
| Domaine_IA | Apprentissage automatique |
| Domaine_Backend | Développement back-end |
| Domaine_Frontend | Développement front-end |
| Domaine_FullStack | Développement full-stack |
| Developpement_Web | Développement web |

_6 ligne(s)_

#### 4.4 Détail

Propriétés de `Domaine_FullStack` et ses formations (chemin à deux sens).

```sparql
SELECT ?propriete ?valeur WHERE {
  { edu:Domaine_FullStack ?propriete ?valeur . FILTER(isLiteral(?valeur)) }
  UNION
  { ?valeur (edu:appartientAuDomaine|^edu:regroupeFormation) edu:Domaine_FullStack . BIND("formation" AS ?propriete) }
} ORDER BY ?propriete
```

**Résultat réel :**

| propriete | valeur |
|---|---|
| intitule | Développement full-stack |
| http://www.w3.org/2000/01/rdf-schema#label | Développement full-stack |
| formation | BootCamp_Web |
| formation | Formation_FullStack |

_4 ligne(s)_

#### 4.5 Recherche par intitulé (insensible à la casse)

Recherche de « DÉVELOPPEMENT » (avec majuscules) : `LCASE` gère aussi les lettres accentuées.

```sparql
SELECT ?d ?intitule WHERE {
  ?d a/rdfs:subClassOf* edu:Domaine ; edu:intitule ?intitule .
  FILTER( CONTAINS(LCASE(STR(?intitule)), LCASE("DÉVELOPPEMENT")) )
} ORDER BY ?intitule
```

**Résultat réel :**

| d | intitule |
|---|---|
| Domaine_Backend | Développement back-end |
| Domaine_Frontend | Développement front-end |
| Domaine_FullStack | Développement full-stack |
| Developpement_Web | Développement web |

_4 ligne(s)_

#### 4.6 Chemin de propriété : domaine → formations → organismes

Séquence `/` de deux chemins à deux sens : quels organismes proposent des formations du domaine full-stack ?

```sparql
SELECT DISTINCT ?organisme WHERE {
  edu:Domaine_FullStack (^edu:appartientAuDomaine|edu:regroupeFormation)/(edu:estProposeePar|^edu:proposeFormation) ?organisme .
}
```

**Résultat réel :**

| organisme |
|---|
| EduParcours_Academie |

_1 ligne(s)_

#### 4.7 Création

Domaine avec `edu:intitule` et `rdfs:label`.

```sparql
INSERT DATA {
  edu:Domaine_Exemple a owl:NamedIndividual, edu:UXDesign ;
    rdfs:label "Domaine exemple"@fr ;
    edu:intitule "Domaine exemple"^^xsd:string ;
    edu:regroupeFormation edu:Formation_Frontend .
}
```

Vérification :

```sparql
SELECT ?intitule ?formation WHERE { edu:Domaine_Exemple edu:intitule ?intitule ; edu:regroupeFormation ?formation }
```

| intitule | formation |
|---|---|
| Domaine exemple | Formation_Frontend |

_1 ligne(s)_

#### 4.8 Modification (intitulé et libellé)

Les deux valeurs sont remplacées ensemble pour rester cohérentes.

```sparql
DELETE { edu:Domaine_Exemple edu:intitule ?i . edu:Domaine_Exemple rdfs:label ?l }
INSERT { edu:Domaine_Exemple edu:intitule "Expérience utilisateur"^^xsd:string .
         edu:Domaine_Exemple rdfs:label "Expérience utilisateur"@fr }
WHERE { OPTIONAL { edu:Domaine_Exemple edu:intitule ?i } OPTIONAL { edu:Domaine_Exemple rdfs:label ?l } }
```

Vérification :

```sparql
SELECT ?intitule ?label WHERE { edu:Domaine_Exemple edu:intitule ?intitule ; rdfs:label ?label }
```

| intitule | label |
|---|---|
| Expérience utilisateur | Expérience utilisateur |

_1 ligne(s)_

#### 4.9 Suppression

Sortants puis entrants.

```sparql
DELETE WHERE { edu:Domaine_Exemple ?p ?o } ;
DELETE WHERE { ?s ?p edu:Domaine_Exemple }
```

Vérification :

```sparql
ASK { { edu:Domaine_Exemple ?p ?o } UNION { ?s ?p edu:Domaine_Exemple } }
```

**Résultat réel :** `False`

## Contrôle final
Nombre de triplets avant les requêtes de mise à jour : **3206** ; après création, modification et suppression
des individus d'exemple : **3206** → identique, aucune trace laissée ✅.
