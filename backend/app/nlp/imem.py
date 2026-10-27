"""NLP – intentions de la tranche d'Imem (formations et parcours) : motifs et gabarits SPARQL.

Même contrat que nlp/ala.py : MOTIFS, ENTITE_ATTENDUE, EXEMPLES, GABARITS.
Différence : les gabarits d'Imem reçoivent aussi la question (gabarit(entite, question)),
car le montant (« moins de 1000 dinars ») et le niveau (« avancé ») sont lus dans le texte.

Motifs : écrits sous la forme produite par normaliser() (minuscules, lemmatisés, sans accents).
Exemples observés : « coûtent » -> « couter », « actives » -> « actif », « entre » -> « entrer ».
LISTER_FORMATIONS a un poids 0,4 : elle ne gagne que si aucune intention plus précise n'est reconnue.
"""
import re

from app.nlp.intents import enregistrer
from app.nlp.normalisation import normaliser
from app.utils import valid_id

# --------------------------------------------------------------------------- motifs
MOTIFS = {
    "FILTRE_COUT": ["moins de", "plus de", "moins cher", "pas cher", "cout", "couter", "prix", "tarif",
                    "gratuit", "dinar", "euro", "budget", "inferieur a", "superieur a", "au maximum",
                    "au plus", "au moins", "entre", "entrer"],
    "FILTRE_NIVEAU": ["niveau", "debutant", "intermediaire", "avance", "difficulte"],
    "COMPTER_MODULES": ["combien de module", "nombre de module"],
    "MODULES_FORMATION": ["quel module", "module de le formation", "module composer", "composer de",
                          "contenu de le formation", "programme de le formation", "module contenir",
                          "module dans le formation"],
    "CERTIF_FORMATION": ["certification", "certificat", "diplome", "mener a", "obtenir on",
                         "permettre d obtenir", "delivrer apres", "attestation", "apres le formation"],
    "PARCOURS_APPRENANT": ["quel parcours", "parcours de", "parcours suivre", "suivre quel parcours",
                           "suivre le parcours", "parcours suivi", "suivre il", "suivre elle"],
    "FORMATIONS_ACTIVES": ["formation actif", "etre actif", "actif", "en cours", "ouvert", "inscription ouvert",
                           "actuellement", "a venir", "prochain formation", "formation futur"],
}
for _intention, _motifs in MOTIFS.items():
    enregistrer(_intention, *_motifs)
enregistrer("LISTER_FORMATIONS", "quel formation", "quel etre le formation", "quelle etre le formation",
            "liste de formation", "lister le formation", "tout le formation", "formation disponible",
            "formation existant", poids=0.4)

# --------------------------------------------------------------------------- entité attendue
ENTITE_ATTENDUE = {
    "LISTER_FORMATIONS": None,
    "FILTRE_COUT": None,
    "FILTRE_NIVEAU": None,
    "FORMATIONS_ACTIVES": None,
    "COMPTER_MODULES": "Formation",
    "MODULES_FORMATION": "Formation",
    "CERTIF_FORMATION": "Formation",
    "PARCOURS_APPRENANT": "Apprenant",
}

# Une question d'exemple par intention (message d'aide + docs/questions_types.csv)
EXEMPLES = {
    "LISTER_FORMATIONS": "Quelles sont les formations disponibles ?",
    "FILTRE_COUT": "Quelles formations coûtent moins de 1000 dinars ?",
    "FILTRE_NIVEAU": "Quelles formations sont de niveau avancé ?",
    "FORMATIONS_ACTIVES": "Quelles formations sont actives ?",
    "COMPTER_MODULES": "Combien de modules compte la formation Développement Full-Stack ?",
    "MODULES_FORMATION": "Quels modules composent la formation Front-end ?",
    "CERTIF_FORMATION": "Quelle certification obtient-on après la formation back-end ?",
    "PARCOURS_APPRENANT": "Quel parcours suit Ahmed ?",
}


# --------------------------------------------------------------------------- valeurs lues dans la question
def _id(entite: str) -> str:
    """Sécurité : l'identifiant injecté dans la requête est validé."""
    if not valid_id(entite):
        raise ValueError(f"identifiant invalide : {entite}")
    return entite


def _texte(question: str) -> str:
    """Sans lemmatisation : « entre » reste « entre » (lemmatisé, il devient « entrer »)."""
    return normaliser(question, lemmes=False)


def nombres(question: str) -> list[float]:
    """Montants écrits en chiffres : « 1000 », « 1 500 », « 99,5 »."""
    return [float(n.replace(" ", "").replace(",", "."))
            for n in re.findall(r"\d{1,3}(?: \d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?", question)]


def filtres_cout(question: str) -> list[str]:
    """FILTER SPARQL sur ?cout déduits de la question (liste vide si aucune contrainte)."""
    t, n = _texte(question), nombres(question)
    if re.search(r"\b(gratuit|sans frais|cout nul)", t):
        return ["FILTER(?cout = 0)"]
    if not n:
        return ["FILTER(?cout < 500)"] if re.search(r"\b(moins cher|pas cher)", t) else []
    if re.search(r"\bentre\b", t) and len(n) >= 2:
        a, b = sorted(n[:2])
        return [f"FILTER(?cout >= {a:g} && ?cout <= {b:g})"]
    if re.search(r"\b(plus de|superieur|au moins|minimum|plus que|depasse)", t):
        return [f"FILTER(?cout >= {n[0]:g})"]
    return [f"FILTER(?cout <= {n[0]:g})"]  # « moins de », « au plus », « inférieur à » ou nombre seul


NIVEAUX = {"debutant": "Débutant", "intermediaire": "Intermédiaire", "avance": "Avancé"}


def niveau(question: str) -> str | None:
    t = _texte(question)
    return next((v for cle, v in NIVEAUX.items() if re.search(r"\b" + cle, t)), None)


def liste_formations(question: str, *, exiger_cout=False, exiger_niveau=False, actives=False) -> str:
    """Gabarit de liste commun : les filtres présents dans la question sont tous appliqués
    (« formations actives de niveau débutant » -> estActif + niveau)."""
    lignes = ["?formation a/rdfs:subClassOf* edu:Formation ;", "           edu:intitule ?intitule .",
              "OPTIONAL { ?formation edu:coutFormation ?cout }",
              "OPTIONAL { ?formation edu:niveauDifficulte ?niveau }"]
    fc = filtres_cout(question)
    if exiger_cout and not fc:
        raise ValueError("Précisez un montant, par exemple « moins de 1000 dinars » ou « gratuites ».")
    lignes += fc
    nv = niveau(question)
    if exiger_niveau and not nv:
        raise ValueError("Précisez le niveau : débutant, intermédiaire ou avancé.")
    if nv:
        lignes.append(f'FILTER(STR(?niveau) = "{nv}")')
    if actives:
        lignes.append("?formation edu:estActif true .")
        lignes.append("OPTIONAL { ?formation edu:dateDebut ?debut }")
        if re.search(r"\b(a venir|futur|prochain)", _texte(question)):
            lignes.append("FILTER(?debut > NOW())")
        champs, ordre = "?formation ?intitule ?debut ?cout", "?debut"
    else:
        champs, ordre = "?formation ?intitule ?cout ?niveau", "?cout" if fc else "?intitule"
    corps = "\n  ".join(lignes)
    return f"SELECT DISTINCT {champs} WHERE {{\n  {corps}\n}} ORDER BY {ordre}"


# --------------------------------------------------------------------------- gabarits
def lister_formations(_, question):
    return liste_formations(question)


def filtre_cout(_, question):
    return liste_formations(question, exiger_cout=True)


def filtre_niveau(_, question):
    return liste_formations(question, exiger_niveau=True)


def formations_actives(_, question):
    return liste_formations(question, actives=True)


def compter_modules(formation, _=None):
    return f"""SELECT (COUNT(DISTINCT ?module) AS ?nombreModules) WHERE {{
  edu:{_id(formation)} edu:composeDe|^edu:faitPartieDeFormation ?module .
}}"""


def modules_formation(formation, _=None):
    return f"""SELECT DISTINCT ?module ?libelle WHERE {{
  edu:{_id(formation)} edu:composeDe|^edu:faitPartieDeFormation ?module .
  ?module rdfs:label ?libelle .
}} ORDER BY ?libelle"""


def certif_formation(formation, _=None):
    return f"""SELECT DISTINCT ?certification ?libelle ?organisme WHERE {{
  edu:{_id(formation)} edu:meneA|^edu:estObtenueApres ?certification .
  ?certification rdfs:label ?libelle .
  OPTIONAL {{ ?certification edu:delivreeParOrganisme|^edu:delivreCertification ?o .
             ?o rdfs:label ?organisme }}
}}"""


def parcours_apprenant(apprenant, _=None):
    return f"""SELECT DISTINCT ?parcours ?libelle ?module WHERE {{
  edu:{_id(apprenant)} edu:suitParcours|^edu:estSuiviPar ?parcours .
  ?parcours rdfs:label ?libelle .
  OPTIONAL {{ ?parcours edu:parcoursComprend|^edu:estEtapeDuParcours ?module }}
}} ORDER BY ?libelle ?module"""


GABARITS = {
    "LISTER_FORMATIONS": lister_formations,
    "FILTRE_COUT": filtre_cout,
    "FILTRE_NIVEAU": filtre_niveau,
    "FORMATIONS_ACTIVES": formations_actives,
    "COMPTER_MODULES": compter_modules,
    "MODULES_FORMATION": modules_formation,
    "CERTIF_FORMATION": certif_formation,
    "PARCOURS_APPRENANT": parcours_apprenant,
}
