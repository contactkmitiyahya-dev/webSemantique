"""NLP – intentions de la tranche de Yahya (apprenants et certifications) : motifs et gabarits SPARQL.

Portage de l'ancienne chaîne de « if » de routers/nlp.py (branche yahya) vers le contrat commun
(MOTIFS, ENTITE_ATTENDUE, EXEMPLES, GABARITS), comme nlp/ala.py et nlp/imem.py.
Mêmes intentions et mêmes requêtes ; plus de résultats simulés : tout est lu dans Fuseki.

Les gabarits reçoivent (entite, question) : APPRENANTS_NIVEAU lit le niveau dans le texte.
Motifs : écrits sous la forme produite par normaliser() (« requis » -> « requerir »,
« inscrit » -> « inscrire », « y a-t-il » -> « y avoir t il »). Ils sont plus longs que ceux
d'Imem qui partagent des mots (« certification », « niveau », « quel formation ») pour l'emporter.
"""
from app.nlp.intents import enregistrer
from app.nlp.normalisation import normaliser
from app.utils import esc, valid_id

# --------------------------------------------------------------------------- motifs
MOTIFS = {
    "APPRENANTS_NIVEAU": ["apprenant de niveau", "etudiant de niveau", "niveau master", "niveau licence",
                          "niveau doctorat", "niveau baccalaureat", "niveau bac", "niveau d etude"],
    "COMPTER_APPRENANTS": ["combien de apprenant", "nombre de apprenant", "combien y avoir t il de apprenant",
                           "combien d apprenant"],
    "COMPTER_CERTIFICATIONS": ["combien de certification", "nombre de certification",
                               "combien y avoir t il de certification"],
    "LISTER_CERTIFICATIONS": ["quel etre le certification", "quelle etre le certification",
                              "liste de certification", "tout le certification", "certification disponible"],
    "CERTIFS_APPRENANT": ["certification avoir obtenir", "avoir obtenir", "certificat de", "diplome de",
                          "certification de"],
    "MODULES_CERTIF": ["module etre requerir", "module requerir", "requerir pour", "module necessaire pour",
                       "requis pour"],
    "COMPETENCES_APPRENANT": ["competence", "savoir faire", "sait faire"],
    "COEQUIPIERS": ["coequipier", "binome", "equipe avec"],
    "FORMATIONS_APPRENANT": ["quel formation etre inscrire", "formation etre inscrire", "formation suivre"],
    "APPRENANTS_FORMATION": ["qui etre inscrire", "apprenant etre inscrire", "inscrire a le formation",
                             "apprenant de le formation"],
}
for _intention, _motifs in MOTIFS.items():
    enregistrer(_intention, *_motifs)

# --------------------------------------------------------------------------- entité attendue
ENTITE_ATTENDUE = {
    "APPRENANTS_NIVEAU": None,
    "COMPTER_APPRENANTS": None,
    "COMPTER_CERTIFICATIONS": None,
    "LISTER_CERTIFICATIONS": None,
    "CERTIFS_APPRENANT": "Apprenant",
    "MODULES_CERTIF": "Certification",
    "COMPETENCES_APPRENANT": "Apprenant",
    "COEQUIPIERS": "Apprenant",
    "FORMATIONS_APPRENANT": "Apprenant",
    "APPRENANTS_FORMATION": "Formation",
}

# Une question d'exemple par intention (message d'aide + docs/questions_types.csv)
EXEMPLES = {
    "APPRENANTS_NIVEAU": "Quels sont les apprenants de niveau Master ?",
    "COMPTER_APPRENANTS": "Combien y a-t-il d'apprenants en tout ?",
    "COMPTER_CERTIFICATIONS": "Combien y a-t-il de certifications en tout ?",
    "LISTER_CERTIFICATIONS": "Quelles sont les certifications disponibles ?",
    "CERTIFS_APPRENANT": "Quelles certifications a obtenu Lina ?",
    "MODULES_CERTIF": "Quels modules sont requis pour le Certificat Développeur Front-end ?",
    "COMPETENCES_APPRENANT": "Quelles sont les compétences de Omar ?",
    "COEQUIPIERS": "Qui sont les coéquipiers de Nour ?",
    "FORMATIONS_APPRENANT": "À quelles formations est inscrit Ahmed ?",
    "APPRENANTS_FORMATION": "Qui est inscrit à la Formation Full-Stack ?",
}


# --------------------------------------------------------------------------- valeurs lues dans la question
def _id(entite: str) -> str:
    """Sécurité : l'identifiant injecté dans la requête est validé."""
    if not valid_id(entite):
        raise ValueError(f"identifiant invalide : {entite}")
    return entite


# Valeurs de edu:niveauEtudes dans les données ; « bac » en dernier (préfixe de « baccalaureat »)
NIVEAUX = {"master": "Master", "licence": "Licence", "doctorat": "Doctorat",
           "baccalaureat": "Baccalauréat", "bac": "Baccalauréat"}


def niveau_etudes(question: str) -> str | None:
    mots = normaliser(question, lemmes=False).split()
    return next((v for k, v in NIVEAUX.items() if k in mots), None)


# --------------------------------------------------------------------------- gabarits
def apprenants_niveau(_, question):
    niveau = niveau_etudes(question)
    if not niveau:
        raise ValueError("Préciser le niveau d'études (Baccalauréat, Licence, Master ou Doctorat).")
    return f"""SELECT DISTINCT ?apprenant ?nom ?prenom WHERE {{
  ?apprenant a/rdfs:subClassOf* edu:Apprenant ; edu:niveauEtudes "{esc(niveau)}" .
  OPTIONAL {{ ?apprenant edu:nom ?nom }} OPTIONAL {{ ?apprenant edu:prenom ?prenom }}
}} ORDER BY ?nom"""


def compter_apprenants(_=None, __=None):
    return """SELECT (COUNT(DISTINCT ?a) AS ?nombreApprenants) WHERE {
  ?a a/rdfs:subClassOf* edu:Apprenant .
}"""


def compter_certifications(_=None, __=None):
    return """SELECT (COUNT(DISTINCT ?c) AS ?nombreCertifications) WHERE {
  ?c a/rdfs:subClassOf* edu:Certification .
}"""


def lister_certifications(_=None, __=None):
    return """SELECT DISTINCT ?certification ?libelle WHERE {
  ?certification a/rdfs:subClassOf* edu:Certification ; rdfs:label ?libelle .
} ORDER BY ?libelle"""


def certifs_apprenant(apprenant, _=None):
    return f"""SELECT DISTINCT ?certification ?libelle WHERE {{
  edu:{_id(apprenant)} edu:obtientCertification ?certification .
  ?certification rdfs:label ?libelle .
}} ORDER BY ?libelle"""


def modules_certif(certification, _=None):
    return f"""SELECT DISTINCT ?module ?libelle WHERE {{
  edu:{_id(certification)} edu:certificationRequiertModule ?module .
  ?module rdfs:label ?libelle .
}} ORDER BY ?libelle"""


def competences_apprenant(apprenant, _=None):
    return f"""SELECT DISTINCT ?competence ?intitule WHERE {{
  edu:{_id(apprenant)} edu:possedeCompetence ?competence .
  OPTIONAL {{ ?competence edu:intitule ?intitule }}
}} ORDER BY ?intitule"""


def coequipiers(apprenant, _=None):
    return f"""SELECT DISTINCT ?coequipier ?nom ?prenom WHERE {{
  edu:{_id(apprenant)} edu:estCoequipierDe|^edu:estCoequipierDe ?coequipier .
  OPTIONAL {{ ?coequipier edu:nom ?nom }} OPTIONAL {{ ?coequipier edu:prenom ?prenom }}
}} ORDER BY ?nom"""


def formations_apprenant(apprenant, _=None):
    return f"""SELECT DISTINCT ?formation ?libelle WHERE {{
  edu:{_id(apprenant)} edu:estInscritA ?formation .
  OPTIONAL {{ ?formation rdfs:label|edu:intitule ?libelle }}
}} ORDER BY ?libelle"""


def apprenants_formation(formation, _=None):
    return f"""SELECT DISTINCT ?apprenant ?nom ?prenom WHERE {{
  ?apprenant edu:estInscritA edu:{_id(formation)} .
  OPTIONAL {{ ?apprenant edu:nom ?nom }} OPTIONAL {{ ?apprenant edu:prenom ?prenom }}
}} ORDER BY ?nom"""


GABARITS = {
    "APPRENANTS_NIVEAU": apprenants_niveau,
    "COMPTER_APPRENANTS": compter_apprenants,
    "COMPTER_CERTIFICATIONS": compter_certifications,
    "LISTER_CERTIFICATIONS": lister_certifications,
    "CERTIFS_APPRENANT": certifs_apprenant,
    "MODULES_CERTIF": modules_certif,
    "COMPETENCES_APPRENANT": competences_apprenant,
    "COEQUIPIERS": coequipiers,
    "FORMATIONS_APPRENANT": formations_apprenant,
    "APPRENANTS_FORMATION": apprenants_formation,
}
