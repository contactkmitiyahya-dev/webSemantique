"""
NLP de la tranche Linda : 8 intentions sur Competence, Technologie et Evaluation.
Approche « intention + entites + gabarit » (aucune API de LLM) :
  1. normalisation du texte ;
  2. intention : registre de motifs (score = motifs presents) ;
  3. entites : dictionnaire charge depuis Fuseki + PhraseMatcher spaCy + rapidfuzz ;
  4. gabarit SPARQL de l'intention, dans lequel on injecte l'URI reconnue.
analyser() renvoie None si la question ne releve pas de cette tranche.
"""

import re
from datetime import date

from ..sparql_client import select_brut as select  # format brut : r["x"]["value"]
from ..utils import valid_id
from .matcher import EntityMatcher, normaliser

# ---------------------------------------------------------------------------
# 1. Registre des intentions (meme forme que le registre prevu dans nlp/intents.py)
# ---------------------------------------------------------------------------

REGISTRE = {}  # intention -> motifs forts (une intention n'est retenue que si l'un d'eux est present)
BONUS = {}     # intention -> motifs faibles (departagent deux intentions, comptent pour 0.5)


def enregistrer(intention, *motifs, bonus=()):
    REGISTRE.setdefault(intention, []).extend(motifs)
    BONUS.setdefault(intention, []).extend(bonus)


# L'ordre compte : en cas d'egalite, la premiere intention enregistree l'emporte.
enregistrer("SOUS_COMPETENCES", "sous competence", "decompos", "se compose", "composantes")
enregistrer("EQUIVALENTES", "equivalen", "equivaut", "remplac", "alternative")
enregistrer("TECHNO_COMPETENCE", "technologie", "techno ", "outil", "framework", "mobilis")
enregistrer("MODULES_COMPETENCE", "acquerir", "apprendre", "apprend ", "developp", "requier", "necessit",
            bonus=("module",))
enregistrer("NOTE_MINIMALE", "note minimale", "note min", "notes minimales", "note requise", "seuil",
            "valider", "note a obtenir")
enregistrer("EVALUATIONS_APRES", "apres", "a venir", "prochain", "futur", "a partir", "depuis",
            bonus=("evaluation", "examen", "quiz"))
enregistrer("EVALUATIONS_MODULE", "evaluation", "examen", "quiz", "epreuve", "soutenance", "controle",
            bonus=("module",))
enregistrer("COMPETENCES_REPANDUES", "repandu", "plus courant", "frequent", "populaire", "plus possed",
            "plus partag")


def detecter_intention(question: str) -> str:
    txt = normaliser(question) + " "
    scores = {}
    for intention, motifs in REGISTRE.items():
        forts = sum(m in txt for m in motifs)
        if forts:
            scores[intention] = forts + 0.5 * sum(b in txt for b in BONUS[intention])
    if not scores:
        return "INCONNUE"
    return max(scores, key=scores.get)  # max garde la premiere en cas d'egalite


# ---------------------------------------------------------------------------
# 2. Dictionnaire d'entites (recharge a chaque question : toujours a jour apres un POST)
# ---------------------------------------------------------------------------

SYNONYMES = [
    ["javascript", "js"],
    ["node js", "nodejs", "node"],
    ["bases de donnees", "base de donnees", "bdd"],
    ["postgresql", "postgres"],
    ["vue js", "vuejs", "vue"],
    ["html", "html5"],
    ["css", "css3"],
]

PREFIXES_LIBELLES = ("module ", "competence ")


def charger_matcher() -> EntityMatcher:
    m = EntityMatcher(SYNONYMES)
    res = select("""
    SELECT DISTINCT ?x ?racine ?label WHERE {
        VALUES ?racine { edu:Competence edu:Technologie edu:Module edu:Evaluation }
        ?x a/rdfs:subClassOf* ?racine .
        { ?x edu:intitule ?label } UNION { ?x rdfs:label ?label }
    }""")
    for r in res:
        uri = r["x"]["value"].split("#")[-1]
        type_ = r["racine"]["value"].split("#")[-1]
        label = r["label"]["value"]
        m.ajouter(label, uri, type_)
        # « Module React » doit aussi etre reconnu par « React »
        norm = normaliser(label)
        for p in PREFIXES_LIBELLES:
            if norm.startswith(p) and len(norm) > len(p) + 2:
                m.ajouter(norm[len(p):], uri, type_)
    return m


# ---------------------------------------------------------------------------
# 3. Dates (« apres le 1er decembre 2026 », « 15/01/2027 », « 2027-02-01 »)
# ---------------------------------------------------------------------------

MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout",
        "septembre", "octobre", "novembre", "decembre"]


def extraire_date(question: str):
    txt = normaliser(question)
    brut = question.lower()
    if m := re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", brut):
        a, mo, j = map(int, m.groups())
    elif m := re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", brut):
        j, mo, a = map(int, m.groups())
    elif m := re.search(r"(?:(\d{1,2}) (?:er )?)?(" + "|".join(MOIS) + r") (\d{4})", txt):
        j = int(m.group(1) or 1)
        mo, a = MOIS.index(m.group(2)) + 1, int(m.group(3))
    else:
        return None
    try:
        return date(a, mo, j)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 4. Gabarits SPARQL (une intention = un gabarit)
# ---------------------------------------------------------------------------

SOUS_DE = "(edu:estSousCompetenceDe|^edu:aPourSousCompetence)"

GABARITS = {
    "SOUS_COMPETENCES": ("Competence", True, """SELECT DISTINCT ?sousCompetence ?intitule WHERE {{
    ?sousCompetence """ + SOUS_DE + """+ edu:{uri} ;
                    edu:intitule ?intitule .
}} ORDER BY ?intitule"""),
    "EQUIVALENTES": ("Competence", True, """SELECT DISTINCT ?equivalente ?intitule WHERE {{
    edu:{uri} edu:estEquivalenteA|^edu:estEquivalenteA ?equivalente .
    ?equivalente edu:intitule ?intitule .
    FILTER(?equivalente != edu:{uri})
}} ORDER BY ?intitule"""),
    "TECHNO_COMPETENCE": ("Competence", True, """SELECT DISTINCT ?technologie ?label WHERE {{
    edu:{uri} edu:competenceSurTechnologie|^edu:estMobiliseePar ?technologie .
    ?technologie rdfs:label ?label .
}} ORDER BY ?label"""),
    "MODULES_COMPETENCE": ("Competence", True, """SELECT DISTINCT ?module ?label WHERE {{
    ?module edu:contientCours|^edu:appartientAuModule ?cours ;
            rdfs:label ?label .
    ?cours edu:developpeCompetence|^edu:estDeveloppeePar ?c .
    ?c """ + SOUS_DE + """* edu:{uri} .
}} ORDER BY ?label"""),
    "EVALUATIONS_MODULE": ("Module", True, """SELECT DISTINCT ?evaluation ?label ?date WHERE {{
    ?evaluation edu:evaluationDuModule|^edu:estEvalueParEvaluation edu:{uri} ;
                rdfs:label ?label .
    OPTIONAL {{ ?evaluation edu:dateEvaluation ?date }}
}} ORDER BY ?date"""),
    "EVALUATIONS_APRES": (None, False, """SELECT DISTINCT ?evaluation ?label ?date WHERE {{
    ?evaluation a/rdfs:subClassOf* edu:Evaluation ;
                rdfs:label ?label ;
                edu:dateEvaluation ?date .
    FILTER(?date >= "{date}T00:00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime>)
}} ORDER BY ?date"""),
    "NOTE_MINIMALE": ("Evaluation", False, """SELECT DISTINCT ?evaluation ?label ?noteMinimale ?coefficient WHERE {{
    {valeurs}?evaluation a/rdfs:subClassOf* edu:Evaluation ;
                rdfs:label ?label ;
                edu:noteMinimale ?noteMinimale .
    OPTIONAL {{ ?evaluation edu:coefficient ?coefficient }}
}} ORDER BY ?label"""),
    "COMPETENCES_REPANDUES": (None, False, """SELECT ?competence ?intitule (COUNT(DISTINCT ?apprenant) AS ?nbApprenants) WHERE {{
    ?apprenant edu:possedeCompetence|^edu:estPossedeePar ?competence .
    ?competence edu:intitule ?intitule .
}} GROUP BY ?competence ?intitule ORDER BY DESC(?nbApprenants) ?intitule LIMIT 5"""),
}

ROLES = {"Competence": "competence", "Module": "module", "Evaluation": "evaluation"}

EXEMPLES = [
    "Quelles sont les sous-compétences de Programmation Web ?",
    "Quels modules permettent d'acquérir la compétence JavaScript ?",
    "Quelles évaluations ont lieu après le 1er janvier 2027 ?",
]

MOTS_TRANCHE = ("competenc", "evaluation", "examen", "quiz", "soutenance")


def analyser(question: str):
    """Modele {intention, entites, sparql, simules, message} ou None si hors tranche."""
    intention = detecter_intention(question)
    if intention not in GABARITS:
        return None
    type_attendu, obligatoire, gabarit = GABARITS[intention]
    entites, valeurs = {}, {}

    if type_attendu:
        try:
            trouvees = charger_matcher().trouver(question, {type_attendu})
        except Exception:
            return None  # Fuseki indisponible : on laisse la main aux autres analyseurs
        trouvees = [e for e in trouvees if valid_id(e["uri"])]
        if trouvees:
            e = trouvees[0]
            entites[ROLES[type_attendu]] = f"{e['label']} -> {e['uri']}" + (
                f" (« {e['texte']} », {e['score']} %)" if e["methode"] == "approchee" else "")
            valeurs["uri"] = e["uri"]
        elif obligatoire:
            if not any(m in normaliser(question) for m in MOTS_TRANCHE):
                return None
            return {
                "intention": intention, "entites": {}, "sparql": "", "simules": [],
                "message": f"Intention {intention} reconnue, mais aucune {ROLES[type_attendu]} "
                           f"n'a ete trouvee dans la question. Exemples : " + " | ".join(EXEMPLES),
            }

    if intention == "EVALUATIONS_APRES":
        d = extraire_date(question) or date.today()
        entites["date"] = d.isoformat()
        valeurs["date"] = d.isoformat()
    if intention == "NOTE_MINIMALE":
        valeurs["valeurs"] = f"VALUES ?evaluation {{ edu:{valeurs['uri']} }}\n    " if "uri" in valeurs else ""

    return {
        "intention": intention,
        "entites": entites,
        "sparql": gabarit.format(**valeurs),
        "simules": [],
        "message": "Succès",
    }
