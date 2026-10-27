"""NLP – intentions de la tranche d'Ala : motifs (détection) et gabarits SPARQL (une intention = un gabarit).

Motifs : écrits sous la forme produite par normaliser() (minuscules, sans accents, lemmatisés),
car detecter_intention() compare des sous-chaînes du texte normalisé. Exemples observés :
« enseignés par » -> « enseigner par », « du cours » -> « de cours », « proposées » -> « proposer ».
« specialis » est un radical : il couvre « specialise », « specialiser » et « specialiste ».

Gabarits : fonction (entité -> requête SPARQL). Les relations sont lues dans les deux sens
(chemin « p|^inverse ») car les données les écrivent tantôt dans un sens, tantôt dans l'autre.
"""
from app.nlp.intents import enregistrer
from app.utils import esc, valid_id

# --------------------------------------------------------------------------- motifs
MOTIFS = {
    "ENSEIGNANT": ["qui enseigne", "qui enseigner", "enseignant", "formateur de cours", "formateur de le cours",
                   "prof", "professeur", "qui donne", "donne le cours", "par qui", "qui assure"],
    "COURS_FORMATEUR": ["quel cours", "cours enseigner", "enseigner par", "cours donne", "que enseigne",
                        "qu enseigne", "cours de le formateur"],
    "FORMATEURS_SPECIALITE": ["specialis", "specialite", "expert en", "formateur en"],
    "ORGANISME_FORMATION": ["quel organisme", "par quel organisme", "organisme proposer", "qui proposer",
                            "qui offre", "qui offrir", "organisme de le formation"],
    "FORMATIONS_ORGANISME": ["proposer par", "que proposer", "formation proposer", "formation offrir",
                             "formation de l organisme", "catalogue"],
    "FORMATIONS_DOMAINE": ["domaine", "appartenir", "regroupe"],
    "RESPONSABLE_FORMATION": ["responsable", "administrer", "qui gerer", "qui diriger", "qui dirige"],
    "COMPTER_FORMATEURS": ["combien de formateur", "nombre de formateur", "compter le formateur"],
}
for _intention, _motifs in MOTIFS.items():
    enregistrer(_intention, *_motifs)

# --------------------------------------------------------------------------- entité attendue
# Classe de l'entité à reconnaître dans la question (None = pas d'entité).
# « Specialite » n'est pas une classe : ce sont les valeurs de edu:specialiteFormateur.
ENTITE_ATTENDUE = {
    "ENSEIGNANT": "Cours",
    "COURS_FORMATEUR": "Formateur",
    "FORMATEURS_SPECIALITE": "Specialite",
    "ORGANISME_FORMATION": "Formation",
    "FORMATIONS_ORGANISME": "Organisme",
    "FORMATIONS_DOMAINE": "Domaine",
    "RESPONSABLE_FORMATION": "Formation",
    "COMPTER_FORMATEURS": None,
}

# Une question d'exemple par intention (message d'aide + docs/questions_types.csv)
EXEMPLES = {
    "ENSEIGNANT": "Qui enseigne le cours React ?",
    "COURS_FORMATEUR": "Quels cours sont enseignés par Dr Mansouri ?",
    "FORMATEURS_SPECIALITE": "Quels formateurs sont spécialisés en DevOps ?",
    "ORGANISME_FORMATION": "Quel organisme propose la formation Full-Stack ?",
    "FORMATIONS_ORGANISME": "Quelles formations sont proposées par EduParcours Académie ?",
    "FORMATIONS_DOMAINE": "Quelles formations appartiennent au domaine développement web ?",
    "RESPONSABLE_FORMATION": "Qui est responsable de la formation Backend ?",
    "COMPTER_FORMATEURS": "Combien de formateurs y a-t-il ?",
}


# --------------------------------------------------------------------------- gabarits
def _id(entite: str) -> str:
    """Sécurité : l'identifiant injecté dans la requête est validé."""
    if not valid_id(entite):
        raise ValueError(f"identifiant invalide : {entite}")
    return entite


def enseignant(cours):
    return f"""SELECT DISTINCT ?formateur ?label WHERE {{
  edu:{_id(cours)} (edu:enseignePar|^edu:enseigne) ?formateur .
  OPTIONAL {{ ?formateur rdfs:label ?label }}
}} ORDER BY ?label"""


def cours_formateur(formateur):
    return f"""SELECT DISTINCT ?cours ?intitule WHERE {{
  ?cours (edu:enseignePar|^edu:enseigne) edu:{_id(formateur)} .
  OPTIONAL {{ ?cours edu:intitule ?intitule }}
}} ORDER BY ?intitule"""


def formateurs_specialite(specialite):
    # Ici l'entité est un texte (valeur de edu:specialiteFormateur) : il est échappé, pas validé comme id
    return f"""SELECT DISTINCT ?formateur ?label ?specialite WHERE {{
  ?formateur a/rdfs:subClassOf* edu:Formateur ; edu:specialiteFormateur ?specialite .
  OPTIONAL {{ ?formateur rdfs:label ?label }}
  FILTER( CONTAINS(LCASE(STR(?specialite)), LCASE("{esc(specialite)}")) )
}} ORDER BY ?label"""


def organisme_formation(formation):
    return f"""SELECT DISTINCT ?organisme ?label WHERE {{
  edu:{_id(formation)} (edu:estProposeePar|^edu:proposeFormation) ?organisme .
  OPTIONAL {{ ?organisme rdfs:label ?label }}
}} ORDER BY ?label"""


def formations_organisme(organisme):
    return f"""SELECT DISTINCT ?formation ?intitule WHERE {{
  ?formation (edu:estProposeePar|^edu:proposeFormation) edu:{_id(organisme)} .
  OPTIONAL {{ ?formation edu:intitule ?intitule }}
}} ORDER BY ?intitule"""


def formations_domaine(domaine):
    return f"""SELECT DISTINCT ?formation ?intitule WHERE {{
  ?formation (edu:appartientAuDomaine|^edu:regroupeFormation) edu:{_id(domaine)} .
  OPTIONAL {{ ?formation edu:intitule ?intitule }}
}} ORDER BY ?intitule"""


def responsable_formation(formation):
    return f"""SELECT DISTINCT ?responsable ?label WHERE {{
  edu:{_id(formation)} (edu:estAdministreePar|^edu:administreFormation) ?responsable .
  OPTIONAL {{ ?responsable rdfs:label ?label }}
}} ORDER BY ?label"""


def compter_formateurs(_=None):
    # Sous-classes comprises (pas de raisonnement dans Fuseki)
    return """SELECT (COUNT(DISTINCT ?formateur) AS ?nombre) WHERE {
  ?formateur a/rdfs:subClassOf* edu:Formateur .
}"""


GABARITS = {
    "ENSEIGNANT": enseignant,
    "COURS_FORMATEUR": cours_formateur,
    "FORMATEURS_SPECIALITE": formateurs_specialite,
    "ORGANISME_FORMATION": organisme_formation,
    "FORMATIONS_ORGANISME": formations_organisme,
    "FORMATIONS_DOMAINE": formations_domaine,
    "RESPONSABLE_FORMATION": responsable_formation,
    "COMPTER_FORMATEURS": compter_formateurs,
}
