# Oral – Imem (formations et parcours)

## 1. Ma tranche en 30 secondes
- Classes : **Formation** (11 sous-classes : FormationCourte, BootCamp, FormationLicence, FormationMaster,
  FormationFullStack…) et **Parcours** (ParcoursFrontend, ParcoursAccelere, ParcoursInfereParCompetence…).
- Données : `data/membre_imem.ttl`, 5 formations (dont une gratuite, une inactive, une future) et 3 parcours.
- Contraintes OWL reprises dans l'API : `composeDe some Module`, `appartientAuDomaine some Domaine`,
  `meneA max 1`, `parcoursComprend some Module`.

## 2. Démo (minute 1:45 – 30 s)
1. Catalogue → Coût max **1000** → 9 formations. Clic sur « Coût » pour trier.
2. Ouvrir « Requête SPARQL envoyée à Fuseki » : montrer la ligne `FILTER(BOUND(?c) && ?c <= 1000)`.
3. Niveau **Avancé** → une ligne `FILTER(STR(?n) = "Avancé")` s'ajoute.
4. Ouvrir *Développement Full-Stack* : modules, inscrits, **places restantes 28 / 30**.
5. Question NLP (Swagger `POST /api/nlp/question` tant que la barre de question de Linda n'est pas fusionnée) :
   « Quels modules composent la formation Front-end ? »

## 3. Ce que j'explique sur l'architecture
- **Un filtre = une ligne SPARQL** : chaque paramètre de `GET /api/formations` ajoute une ligne au motif
  (`_motif_liste` dans `routers/formations.py`). Le même motif sert au `COUNT` (total) et à la page (`LIMIT/OFFSET`).
- **Pas de raisonnement dans Fuseki** : `a/rdfs:subClassOf* edu:Formation` (sinon les BootCamp ne sortent pas),
  `edu:estProposeePar|^edu:proposeFormation` car les données déclarent tantôt un sens, tantôt l'autre.
- **Places restantes** : `nombrePlaces - COUNT(?a)` avec `?f ^edu:estInscritA ?a` (inverse).
- **Sécurité** (`utils.py`, mon fichier commun) : `valid_id` (`^[A-Z][A-Za-z0-9_]*$`, sinon 400), `esc()` pour
  les chaînes (test : un intitulé `"} ; DROP ALL ; #` est stocké tel quel, sans injection).
- **Front** : `DataTable` réutilisable (tri et pagination côté serveur ou local), client Axios qui convertit
  `{"detail"}` en message, filtres stockés dans l'URL (lien partageable).
- **NLP** : mon noyau `intents.py`, utilisé par tous les membres. La question est normalisée par spaCy
  (lemmes : « coûtent » → « couter ») et les motifs sont écrits sous cette forme. Score = somme des mots des
  motifs reconnus × poids : « combien de module » (3 mots) l'emporte sur « module ». LISTER_FORMATIONS a un
  poids 0,4 pour ne gagner que si rien de plus précis n'est reconnu. Le montant et le niveau sont lus dans le
  texte non lemmatisé (sinon « entre » devient « entrer ») ; « moins de », « plus de », « entre »,
  « gratuit » deviennent des FILTER, et un niveau présent dans la question s'ajoute au filtre de coût.

## 4. Questions probables
- *Pourquoi PUT efface puis réinsère ?* Remplacement complet en une seule requête de mise à jour
  (transaction Fuseki) ; les inscriptions des apprenants ne sont pas touchées.
- *Que se passe-t-il si on supprime une formation où des apprenants sont inscrits ?* Les triplets entrants
  (`Ahmed estInscritA …`) sont supprimés aussi (`DELETE WHERE { ?s ?p edu:X }`).
- *Peut-on baisser le nombre de places sous le nombre d'inscrits ?* Non : 409.
