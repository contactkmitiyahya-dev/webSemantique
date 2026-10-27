"""
Routeur FastAPI pour le module NLP (Questions en langage naturel -> SPARQL).
Version finale complète et robuste.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from ..sparql_client import select

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

# ==========================================
# 1. Dictionnaires d'entités
# ==========================================
NOMS_APPRENANTS = {
    "lina": "Lina_Master", "omar": "Omar", "ahmed": "Ahmed",
    "nour": "Nour", "sarra": "Sarra", "mariem": "Mariem",
    "karim": "Karim", "yassine": "Yassine", "rim": "Rim",
}

CERTIFICATIONS = {
    "front": "Certificat_Frontend", "frontend": "Certificat_Frontend", "front-end": "Certificat_Frontend",
    "back": "Certificat_Backend", "backend": "Certificat_Backend", "back-end": "Certificat_Backend",
    "web": "Certificat_DeveloppeurWeb", "full": "Certificat_DeveloppeurWeb", "fullstack": "Certificat_DeveloppeurWeb",
    "react": "Attestation_Module_React"
}

# ==========================================
# 2. Fonction principale de détection
# ==========================================
def analyser_question(texte: str) -> Dict[str, Any]:
    txt = texte.lower().strip()
    
    # ----------------------------------------
    # A. FORMATEURS (Nouveau !)
    # ----------------------------------------
    if any(k in txt for k in ["formateur", "formateurs", "enseignant", "enseignants", "prof", "profs", "enseigne"]):
        if "react" in txt:
            return {
                "intention": "FORMATEUR_MATIERE", "entites": {"matiere": "React"},
                "sparql": "SELECT ?f ?nom ?prenom WHERE { ?c edu:utiliseTechnologie edu:Tech_React ; edu:enseignePar ?f . ?f edu:nom ?nom ; edu:prenom ?prenom . }",
                "simules": [{"f": "edu:Dr_Benali", "nom": "Benali", "prenom": "Dr."}]
            }
        return {
            "intention": "LISTER_FORMATEURS", "entites": {},
            "sparql": "SELECT ?f ?nom ?prenom ?specialite WHERE { ?f a/rdfs:subClassOf* edu:Formateur ; edu:nom ?nom ; edu:prenom ?prenom ; edu:specialiteFormateur ?specialite . }",
            "simules": [
                {"f": "edu:Dr_Benali", "nom": "Benali", "prenom": "Dr.", "specialite": "Développement web"},
                {"f": "edu:Mme_Jebali", "nom": "Jebali", "prenom": "Hela", "specialite": "Front-end"}
            ]
        }

    # ----------------------------------------
    # B. MODULES REQUIS POUR CERTIFICATION(S)
    # ----------------------------------------
    if any(k in txt for k in ["module", "requis", "comprend", "contient"]):
        certifs = []
        for mot_cle, uri in CERTIFICATIONS.items():
            if mot_cle in txt and uri not in certifs:
                certifs.append(uri)
        if not certifs: certifs = ["Certificat_Frontend", "Certificat_Backend"]
        
        union_parts = [f"{{ edu:{c} edu:certificationRequiertModule ?m . BIND(\"{c}\" AS ?certification) }}" for c in certifs]
        sparql = f"""
        SELECT DISTINCT ?certification ?m ?label WHERE {{
            {' UNION '.join(union_parts)}
            ?m rdfs:label ?label .
        }}
        """
        return {
            "intention": "MODULES_CERTIF_MULTIPLE", 
            "entites": {"certifications": ", ".join(certifs)},
            "sparql": sparql, "simules": []
        }

    # ----------------------------------------
    # C. COMPTER
    # ----------------------------------------
    if any(k in txt for k in ["combien", "nombre", "total", "compter"]):
        if any(c in txt for c in ["certification", "certif"]):
            return {
                "intention": "COMPTER_CERTIFICATIONS", "entites": {},
                "sparql": "SELECT (COUNT(?c) AS ?n) WHERE { ?c a/rdfs:subClassOf* edu:Certification . }",
                "simules": []
            }
        return {
            "intention": "COMPTER_APPRENANTS", "entites": {},
            "sparql": "SELECT (COUNT(?a) AS ?n) WHERE { ?a a/rdfs:subClassOf* edu:Apprenant . }",
            "simules": []
        }

    # ----------------------------------------
    # D. CERTIFICATIONS D'UN APPRENANT
    # ----------------------------------------
    if any(k in txt for k in ["certification", "certif", "diplome", "diplôme"]):
        app_uri = next((uri for nom, uri in NOMS_APPRENANTS.items() if nom in txt), None)
        if app_uri:
            return {
                "intention": "CERTIFS_APPRENANT", "entites": {"personne": app_uri},
                "sparql": f"SELECT ?c ?label WHERE {{ edu:{app_uri} edu:obtientCertification ?c . ?c rdfs:label ?label . }}",
                "simules": []
            }
        return {
            "intention": "LISTER_CERTIFICATIONS", "entites": {},
            "sparql": "SELECT ?c ?label WHERE { ?c a/rdfs:subClassOf* edu:Certification ; rdfs:label ?label . }",
            "simules": []
        }

    # ----------------------------------------
    # E. COMPÉTENCES D'UN APPRENANT
    # ----------------------------------------
    if any(k in txt for k in ["compétence", "competence", "sait faire"]):
        app_uri = next((uri for nom, uri in NOMS_APPRENANTS.items() if nom in txt), None)
        if app_uri:
            return {
                "intention": "COMPETENCES_APPRENANT", "entites": {"personne": app_uri},
                "sparql": f"SELECT ?c ?intitule WHERE {{ edu:{app_uri} edu:possedeCompetence ?c . ?c edu:intitule ?intitule . }}",
                "simules": []
            }

    # ----------------------------------------
    # F. COÉQUIPIERS
    # ----------------------------------------
    if any(k in txt for k in ["coéquipier", "coequipier", "coequipiers", "coéquipiers", "binôme", "binome"]):
        app_uri = next((uri for nom, uri in NOMS_APPRENANTS.items() if nom in txt), None)
        if app_uri:
            return {
                "intention": "COEQUIPIERS", "entites": {"personne": app_uri},
                "sparql": f"SELECT ?c ?nom ?prenom WHERE {{ edu:{app_uri} edu:estCoequipierDe ?c . ?c edu:nom ?nom ; edu:prenom ?prenom . }}",
                "simules": []
            }

    # ----------------------------------------
    # G. FORMATIONS
    # ----------------------------------------
    if "formation" in txt:
        app_uri = next((uri for nom, uri in NOMS_APPRENANTS.items() if nom in txt), None)
        if app_uri:
            return {
                "intention": "FORMATIONS_APPRENANT", "entites": {"personne": app_uri},
                "sparql": f"SELECT ?f ?label WHERE {{ edu:{app_uri} edu:estInscritA ?f . ?f rdfs:label ?label . }}",
                "simules": []
            }
        return {
            "intention": "APPRENANTS_FORMATION", "entites": {"formation": "Formation_FullStack"},
            "sparql": "SELECT ?a ?nom ?prenom WHERE { ?a edu:estInscritA edu:Formation_FullStack ; edu:nom ?nom ; edu:prenom ?prenom . }",
            "simules": []
        }

    # ----------------------------------------
    # H. NIVEAU D'ÉTUDES
    # ----------------------------------------
    if any(k in txt for k in ["niveau", "master", "licence", "doctorat", "baccalauréat", "bac"]):
        niveau = "Master"
        if "licence" in txt: niveau = "Licence"
        if "doctorat" in txt: niveau = "Doctorat"
        if "bac" in txt: niveau = "Baccalauréat"
        return {
            "intention": "APPRENANTS_NIVEAU", "entites": {"niveau": niveau},
            "sparql": f'SELECT ?a ?nom ?prenom WHERE {{ ?a a/rdfs:subClassOf* edu:Apprenant ; edu:nom ?nom ; edu:prenom ?prenom ; edu:niveauEtudes ?n . FILTER(?n = "{niveau}") }}',
            "simules": []
        }

    # ----------------------------------------
    # I. FALLBACK
    # ----------------------------------------
    return {
        "intention": "INCONNUE", "entites": {}, "sparql": "", "simules": [],
        "message": "Je n'ai pas compris. Essayez : 'Quels sont les formateurs ?', 'Modules pour le back-end' ou 'Apprenants de niveau Master'."
    }

# ==========================================
# 3. Routes FastAPI
# ==========================================

@router.get("/exemples", summary="Obtenir les questions types")
def get_exemples():
    return [
        {"id": 1, "question": "Quels sont les apprenants de niveau Master ?", "intention": "APPRENANTS_NIVEAU"},
        {"id": 2, "question": "Quels modules sont requis pour le back-end et le front-end ?", "intention": "MODULES_CERTIF_MULTIPLE"},
        {"id": 3, "question": "Quels sont les formateurs ?", "intention": "LISTER_FORMATEURS"},
        {"id": 4, "question": "Quelles certifications a obtenu Lina ?", "intention": "CERTIFS_APPRENANT"},
        {"id": 5, "question": "Combien y a-t-il d'apprenants ?", "intention": "COMPTER_APPRENANTS"},
        {"id": 6, "question": "Qui sont les coéquipiers de Nour ?", "intention": "COEQUIPIERS"},
        {"id": 7, "question": "Quelles sont les compétences de Omar ?", "intention": "COMPETENCES_APPRENANT"},
        {"id": 8, "question": "À quelles formations est inscrit Ahmed ?", "intention": "FORMATIONS_APPRENANT"}
    ]

@router.post("/question", summary="Interroger le module NLP")
def traiter_question(req: QuestionRequest):
    modele = analyser_question(req.question)
    
    resultats = modele.get("simules", [])
    source = "simulation"

    if modele["sparql"]:
        try:
            bindings = select(modele["sparql"])
            if bindings:
                parsed = [{k: v.get("value", "").split("#")[-1] for k, v in b.items()} for b in bindings]
                resultats = parsed
                source = "fuseki"
        except Exception:
            pass

    sparql_complet = ""
    if modele["sparql"]:
        sparql_complet = f"""PREFIX edu:  <http://www.eduparcours.org/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
{modele["sparql"]}"""

    return {
        "question": req.question,
        "intention": modele["intention"],
        "entites": modele["entites"],
        "sparql": sparql_complet,
        "resultats": resultats,
        "source": source,
        "message": modele.get("message", "Succès")
    }