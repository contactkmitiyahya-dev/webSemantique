"""
Routeur FastAPI pour le module NLP (Questions en langage naturel -> SPARQL).
Gère l'extraction d'entités multiples et les requêtes complexes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from ..sparql_client import select

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

# ==========================================
# 1. Dictionnaires d'entités
# ==========================================
NOMS_APPRENANTS = {
    "lina": "Lina_Master",
    "omar": "Omar",
    "ahmed": "Ahmed",
    "nour": "Nour",
    "sarra": "Sarra",
    "mariem": "Mariem",
    "karim": "Karim",
    "yassine": "Yassine",
    "rim": "Rim",
}

CERTIFICATIONS = {
    "front": "Certificat_Frontend",
    "frontend": "Certificat_Frontend",
    "front-end": "Certificat_Frontend",
    "back": "Certificat_Backend",
    "backend": "Certificat_Backend",
    "back-end": "Certificat_Backend",
    "web": "Certificat_DeveloppeurWeb",
    "full": "Certificat_DeveloppeurWeb",
    "fullstack": "Certificat_DeveloppeurWeb",
    "react": "Attestation_Module_React"
}

# ==========================================
# 2. Fonction principale de détection
# ==========================================
def analyser_question(texte: str) -> Dict[str, Any]:
    txt = texte.lower().strip()
    
    # ----------------------------------------
    # A. MODULES REQUIS POUR CERTIFICATION(S)
    # ----------------------------------------
    if any(k in txt for k in ["module", "requis", "comprend", "contient"]):
        # On cherche TOUTES les certifications mentionnées dans la phrase
        certifs_trouvees = []
        for mot_cle, uri in CERTIFICATIONS.items():
            if mot_cle in txt and uri not in certifs_trouvees:
                certifs_trouvees.append(uri)
        
        # Si aucune certification n'est précisée, on les prend toutes
        if not certifs_trouvees:
            certifs_trouvees = ["Certificat_Frontend", "Certificat_Backend"]
            
        # Génération de la requête SPARQL avec UNION pour gérer plusieurs certifs
        union_parts = []
        for c in certifs_trouvees:
            union_parts.append(f"{{ edu:{c} edu:certificationRequiertModule ?m . BIND(\"{c}\" AS ?certification) }}")
        
        sparql = f"""
        SELECT DISTINCT ?certification ?m ?label WHERE {{
            {' UNION '.join(union_parts)}
            ?m rdfs:label ?label .
        }}
        """
        
        return {
            "intention": "MODULES_CERTIF_MULTIPLE",
            "entites": {"certifications": certifs_trouvees},
            "sparql": sparql,
            "simules": [{"certification": c, "m": "edu:Module_X", "label": "Module X"} for c in certifs_trouvees]
        }

    # ----------------------------------------
    # B. COMPTER (Apprenants, Certifications...)
    # ----------------------------------------
    if any(k in txt for k in ["combien", "nombre", "total", "compter"]):
        if any(c in txt for c in ["certification", "certif"]):
            return {
                "intention": "COMPTER_CERTIFICATIONS",
                "entites": {},
                "sparql": "SELECT (COUNT(?c) AS ?n) WHERE { ?c a/rdfs:subClassOf* edu:Certification . }",
                "simules": [{"n": "6"}]
            }
        return {
            "intention": "COMPTER_APPRENANTS",
            "entites": {},
            "sparql": "SELECT (COUNT(?a) AS ?n) WHERE { ?a a/rdfs:subClassOf* edu:Apprenant . }",
            "simules": [{"n": "10"}]
        }

    # ----------------------------------------
    # C. CERTIFICATIONS D'UN APPRENANT
    # ----------------------------------------
    if any(k in txt for k in ["certification", "certif", "diplome", "diplôme"]):
        apprenant_uri = None
        for nom, uri in NOMS_APPRENANTS.items():
            if nom in txt:
                apprenant_uri = uri
                break
                
        if apprenant_uri:
            return {
                "intention": "CERTIFS_APPRENANT",
                "entites": {"personne": apprenant_uri},
                "sparql": f"""
                SELECT ?c ?label WHERE {{
                    edu:{apprenant_uri} edu:obtientCertification ?c .
                    ?c rdfs:label ?label .
                }}""",
                "simules": [{"c": "edu:Certificat_DeveloppeurWeb", "label": "Certificat Web"}]
            }

    # ----------------------------------------
    # D. COMPÉTENCES D'UN APPRENANT
    # ----------------------------------------
    if any(k in txt for k in ["compétence", "competence", "sait faire"]):
        apprenant_uri = None
        for nom, uri in NOMS_APPRENANTS.items():
            if nom in txt:
                apprenant_uri = uri
                break
                
        if apprenant_uri:
            return {
                "intention": "COMPETENCES_APPRENANT",
                "entites": {"personne": apprenant_uri},
                "sparql": f"""
                SELECT ?c ?intitule WHERE {{
                    edu:{apprenant_uri} edu:possedeCompetence ?c .
                    ?c edu:intitule ?intitule .
                }}""",
                "simules": [{"c": "edu:Comp_React", "intitule": "React"}]
            }

    # ----------------------------------------
    # E. COÉQUIPIERS
    # ----------------------------------------
    if any(k in txt for k in ["coéquipier", "coequipier", "binôme", "binome"]):
        apprenant_uri = None
        for nom, uri in NOMS_APPRENANTS.items():
            if nom in txt:
                apprenant_uri = uri
                break
                
        if apprenant_uri:
            return {
                "intention": "COEQUIPIERS",
                "entites": {"personne": apprenant_uri},
                "sparql": f"""
                SELECT ?c ?nom ?prenom WHERE {{
                    edu:{apprenant_uri} edu:estCoequipierDe ?c .
                    ?c edu:nom ?nom ; edu:prenom ?prenom .
                }}""",
                "simules": [{"c": "edu:Omar", "nom": "Gharbi", "prenom": "Omar"}]
            }

    # ----------------------------------------
    # F. FORMATIONS D'UN APPRENANT
    # ----------------------------------------
    if "formation" in txt:
        apprenant_uri = None
        for nom, uri in NOMS_APPRENANTS.items():
            if nom in txt:
                apprenant_uri = uri
                break
                
        if apprenant_uri:
            return {
                "intention": "FORMATIONS_APPRENANT",
                "entites": {"personne": apprenant_uri},
                "sparql": f"""
                SELECT ?f ?label WHERE {{
                    edu:{apprenant_uri} edu:estInscritA ?f .
                    ?f rdfs:label ?label .
                }}""",
                "simules": [{"f": "edu:Formation_FullStack", "label": "Full-Stack"}]
            }
        # Qui est inscrit à une formation (Full-Stack par défaut)
        elif any(k in txt for k in ["qui", "inscrit"]):
             return {
                "intention": "APPRENANTS_FORMATION",
                "entites": {"formation": "Formation_FullStack"},
                "sparql": """
                SELECT ?a ?nom ?prenom WHERE {
                    ?a edu:estInscritA edu:Formation_FullStack ;
                       edu:nom ?nom ; edu:prenom ?prenom .
                }""",
                "simules": [{"a": "edu:Ahmed", "nom": "Ahmed", "prenom": "Ahmed"}]
            }

    # ----------------------------------------
    # G. NIVEAU D'ÉTUDES (Master, Licence, etc.)
    # ----------------------------------------
    if any(k in txt for k in ["niveau", "master", "licence", "doctorat", "baccalauréat"]):
        niveau = "Master"
        if "licence" in txt: niveau = "Licence"
        if "doctorat" in txt: niveau = "Doctorat"
        if "bac" in txt: niveau = "Baccalauréat"
        
        return {
            "intention": "APPRENANTS_NIVEAU",
            "entites": {"niveau": niveau},
            "sparql": f"""
            SELECT ?a ?nom ?prenom WHERE {{
                ?a a/rdfs:subClassOf* edu:Apprenant ;
                   edu:nom ?nom ; edu:prenom ?prenom ; edu:niveauEtudes ?n .
                FILTER(?n = "{niveau}")
            }}""",
            "simules": [{"a": "edu:Lina_Master", "nom": "Lina", "prenom": "Lina"}]
        }

    # ----------------------------------------
    # H. FALLBACK (Question non comprise)
    # ----------------------------------------
    return {
        "intention": "INCONNUE",
        "entites": {},
        "sparql": "",
        "simules": [],
        "message": "Je n'ai pas compris. Essayez : 'Quels sont les apprenants de niveau Master ?' ou 'Modules pour le back-end et le front-end'."
    }

# ==========================================
# 3. Routes FastAPI
# ==========================================

@router.get("/exemples", summary="Obtenir les questions types pour l'interface")
def get_exemples():
    # On renvoie une liste d'objets pour que le Front-end puisse afficher les boutons
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

    # Exécution réelle sur Fuseki
    if modele["sparql"]:
        try:
            bindings = select(modele["sparql"])
            if bindings:
                parsed = []
                for b in bindings:
                    item = {k: v.get("value", "").split("#")[-1] for k, v in b.items()}
                    parsed.append(item)
                resultats = parsed
                source = "fuseki"
        except Exception as e:
            pass # On garde les simulations si Fuseki plante

    # Ajout des préfixes pour l'affichage
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