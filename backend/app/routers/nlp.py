# TEMPORAIRE (Ala) – à remplacer par la version de Yahya (route POST /api/nlp/question)
"""Route de test du pipeline NLP pour les intentions d'Ala.

normaliser -> detecter_intention -> reconnaissance d'entité -> gabarit -> select
Réponse : {intention, entites, sparql, resultats} (+ message d'aide si la question n'est pas comprise).

La reconnaissance d'entités ci-dessous est elle aussi TEMPORAIRE (Ala) – à remplacer par le
dictionnaire de Zahra (entities.py) et le matcher de Linda.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from rapidfuzz import fuzz

from app.ala_commun import motif_type
from app.nlp import ala, imem, yahya
from app.nlp.linda import EXEMPLES as EXEMPLES_LINDA
from app.nlp.linda import MOTS_TRANCHE as MOTS_LINDA
from app.nlp.linda import analyser as analyser_linda
from app.nlp.matcher import normaliser as normaliser_linda
from app.nlp.intents import detecter_intention
from app.nlp.normalisation import normaliser
from app.sparql_client import select

router = APIRouter(prefix="/api/nlp", tags=["NLP (TEMPORAIRE)"])

SEUIL_FLOU = 85  # rapidfuzz : tolère une petite faute de frappe (« Mansoury » -> « Mansouri »)
CLASSES = ["Formateur", "Organisme", "Domaine", "Cours", "Formation", "Apprenant", "Certification"]

# Intentions de chaque membre (même contrat : GABARITS, ENTITE_ATTENDUE, EXEMPLES)
MODULES = (ala, imem, yahya)
GABARITS = {i: g for m in MODULES for i, g in m.GABARITS.items()}
ENTITE_ATTENDUE = {i: c for m in MODULES for i, c in m.ENTITE_ATTENDUE.items()}
EXEMPLES = {i: q for m in MODULES for i, q in m.EXEMPLES.items()}
# Les gabarits d'Imem et de Yahya lisent aussi la question (montant, niveau) : gabarit(entite, question)
AVEC_QUESTION = set(imem.GABARITS) | set(yahya.GABARITS)


class Question(BaseModel):
    question: str


# --------------------------------------------------------------------------- dictionnaire d'entités

def dictionnaire() -> list[dict]:
    """Libellés de chaque individu (rdfs:label, edu:intitule, edu:nom, prénom + nom, identifiant),
    normalisés SANS lemmatisation (sinon « EduParcours » deviendrait « eduparcour »).
    Relu à chaque question : un individu créé depuis l'interface est reconnu tout de suite."""
    entrees = []
    for racine in CLASSES:
        lignes = select(f"""SELECT DISTINCT ?x ?t ?lib WHERE {{
  ?x a/rdfs:subClassOf* edu:{racine} .
  {motif_type("x", "t", racine)}
  {{ ?x rdfs:label ?lib }} UNION {{ ?x edu:intitule ?lib }} UNION {{ ?x edu:nom ?lib }}
  UNION {{ ?x edu:nom ?n ; edu:prenom ?p . FILTER(!STRENDS(?p, ".")) BIND(CONCAT(?p, " ", ?n) AS ?lib) }}
}}""")
        vus = set()
        for l in lignes:
            # L'identifiant sert aussi de libellé : Formation_Backend -> « formation backend »
            for texte in (l["lib"], l["x"].replace("_", " ")):
                cle = (l["x"], normaliser(texte, lemmes=False))
                if cle not in vus:
                    vus.add(cle)
                    entrees.append({"uri": l["x"], "type": l["t"], "classe": racine, "libelle": cle[1]})
    # Spécialités : valeurs littérales de edu:specialiteFormateur
    for l in select("SELECT DISTINCT ?s WHERE { ?f edu:specialiteFormateur ?s }"):
        entrees.append({"uri": l["s"], "type": "Specialite", "classe": "Specialite",
                        "libelle": normaliser(l["s"], lemmes=False)})
    return [e for e in entrees if len(e["libelle"]) >= 3]  # trop court = trop ambigu


def fragment_contenu(mots: list[str], libelle: str) -> str | None:
    """Plus long groupe de 1 à 3 mots de la question (au moins 4 lettres) contenu, en mots
    entiers, dans le libellé. Sert aux spécialités, plus longues que ce que l'on tape."""
    for n in (3, 2, 1):
        for i in range(len(mots) - n + 1):
            fragment = " ".join(mots[i:i + n])
            if len(fragment) >= 4 and f" {fragment} " in f" {libelle} ":
                return fragment
    return None


def reconnaitre(question: str, classe: str) -> dict | None:
    """Cherche dans la question le libellé d'un individu de la classe attendue.
    1) correspondance exacte (mots entiers) ; 2) sinon rapidfuzz ratio >= 85 sur une fenêtre
    du même nombre de mots. En cas d'égalité, le libellé le plus long gagne (« cours react » > « react »).
    fuzz.ratio et non WRatio : WRatio fait une comparaison PARTIELLE quand les longueurs diffèrent,
    ce qui donnait 85,5 à « le cours » contre « cours angular » (faux positif)."""
    texte = normaliser(question, lemmes=False)
    mots = texte.split()
    meilleur, meilleur_score = None, 0
    for e in dictionnaire():
        if e["classe"] != classe:
            continue
        lib = e["libelle"]
        n = len(lib.split())
        if f" {lib} " in f" {texte} ":
            score, trouve = 100, lib
        elif len(lib) >= 6 and lib.replace(" ", "") in texte.replace(" ", ""):
            score, trouve = 95, lib                 # « fullstack » trouvé dans « full stack »
        elif classe == "Specialite" and (fragment := fragment_contenu(mots, lib)):
            score, trouve = 90, fragment            # « back end » dans « developpement back end »
        else:
            fenetres = [" ".join(mots[i:i + n]) for i in range(len(mots) - n + 1)]
            score, trouve = max(((fuzz.ratio(lib, f), f) for f in fenetres), default=(0, None))
        if score >= SEUIL_FLOU and (score, len(lib)) > (meilleur_score, len(meilleur["libelle"]) if meilleur else 0):
            meilleur, meilleur_score = {**e, "texte": trouve}, score
    if not meilleur:
        return None
    return {"texte": meilleur["texte"], "uri": meilleur["uri"], "type": meilleur["type"]}


# --------------------------------------------------------------------------- route

def aide(message: str) -> str:
    exemples = " ; ".join(f"« {q} »" for q in EXEMPLES.values())
    return f"{message} Exemples de questions : {exemples}"


@router.get("/exemples", summary="Une question type par intention (page NLP de Yahya)")
def exemples():
    paires = [*EXEMPLES.items(), *(("LINDA", q) for q in EXEMPLES_LINDA)]
    return [{"id": n, "question": q, "intention": i} for n, (i, q) in enumerate(paires, start=1)]


@router.post("/question", summary="Question en langage naturel -> requête SPARQL -> résultats")
def question(q: Question):
    # source : la page NLP de Yahya affiche « Fuseki (En direct) » ; plus aucun résultat simulé
    reponse = {"intention": "INCONNUE", "entites": [], "sparql": None, "resultats": [], "source": "fuseki"}

    if not q.question.strip():
        return {**reponse, "message": aide("La question est vide.")}

    # Tranche Linda (compétences, technologies, évaluations) : son propre analyseur (PhraseMatcher spaCy
    # + rapidfuzz), essayé en premier ; il renvoie None hors de sa tranche. Ses entités restent au format
    # {rôle: "libellé -> uri"} (tests de Linda) ; à unifier avec le format liste quand l'équipe aura choisi.
    # Seulement si la question parle de sa tranche : sinon « après » / « à venir » (Imem) était pris
    # pour EVALUATIONS_APRES.
    texte_linda = normaliser_linda(q.question)
    tranche_linda = any(m in texte_linda for m in (*MOTS_LINDA, "technolog", "note minimal"))
    modele = analyser_linda(q.question) if tranche_linda else None
    if modele:
        reponse.update(intention=modele["intention"], entites=modele["entites"], sparql=modele["sparql"])
        if not modele["sparql"]:
            return {**reponse, "message": modele["message"]}
        reponse["resultats"] = select(modele["sparql"])
        if not reponse["resultats"]:
            reponse["message"] = "La requête est correcte mais ne renvoie aucun résultat."
        return reponse

    intention = detecter_intention(q.question)
    reponse["intention"] = intention
    if intention not in GABARITS:
        return {**reponse, "message": aide("Je n'ai pas compris la question.")}

    classe = ENTITE_ATTENDUE[intention]
    entite = None
    if classe:
        entite = reconnaitre(q.question, classe)
        if not entite:
            return {**reponse, "message": aide(
                f"Intention {intention} reconnue, mais aucun élément de type « {classe} » trouvé dans la question. "
                f"Exemple pour cette intention : « {EXEMPLES[intention]} ».")}
        reponse["entites"] = [entite]

    uri = entite["uri"] if entite else None
    try:
        sparql = GABARITS[intention](uri, q.question) if intention in AVEC_QUESTION else GABARITS[intention](uri)
    except ValueError as e:  # gabarit incomplet (ex. montant absent) : on explique quoi préciser
        return {**reponse, "message": f"{e} Exemple : « {EXEMPLES[intention]} »."}
    reponse["sparql"] = sparql
    reponse["resultats"] = select(sparql)
    if not reponse["resultats"]:
        reponse["message"] = "La requête est correcte mais ne renvoie aucun résultat."
    return reponse
