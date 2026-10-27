"""
Routeur FastAPI pour la ressource Apprenant.
Endpoints CRUD + inscription aux formations + statistiques.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from ..sparql_client import select, update
from ..utils import valid_id, esc

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class ApprenantCreate(BaseModel):
    id: str
    nom: str
    prenom: str
    email: str
    niveauEtudes: str
    dateNaissance: str


# ---------------------------------------------------------------------------
# GET /api/apprenants  - Liste paginee avec filtres optionnels
# ---------------------------------------------------------------------------

@router.get("", summary="Lister les apprenants")
def liste_apprenants(
    q: Optional[str] = Query(None, description="Recherche par nom"),
    niveau: Optional[str] = Query(None, description="Filtrer par niveau d'etudes"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * taille
    filtre = ""
    if q:
        filtre += f'FILTER(CONTAINS(LCASE(STR(?nom)), LCASE("{esc(q)}"))) '
    if niveau:
        filtre += f'FILTER(?niveau = "{esc(niveau)}") '

    query = f"""
    SELECT ?id ?nom ?prenom ?niveau WHERE {{
        ?id a/rdfs:subClassOf* edu:Apprenant ;
            edu:nom ?nom ;
            edu:prenom ?prenom ;
            edu:niveauEtudes ?niveau .
        {filtre}
    }} ORDER BY ?nom LIMIT {taille} OFFSET {offset}
    """
    resultats = select(query)
    donnees = [
        {
            "id": r["id"]["value"].split("#")[-1],
            "nom": r["nom"]["value"],
            "prenom": r["prenom"]["value"],
            "niveau": r["niveau"]["value"],
        }
        for r in resultats
    ]
    return {"total": len(donnees), "page": page, "taille": taille, "donnees": donnees}


# ---------------------------------------------------------------------------
# GET /api/apprenants/stats  - Statistiques par niveau
# ---------------------------------------------------------------------------

@router.get("/stats", summary="Statistiques des apprenants par niveau")
def statistiques():
    query = """
    SELECT ?niveau (COUNT(?id) AS ?nombre) WHERE {
        ?id a/rdfs:subClassOf* edu:Apprenant ;
            edu:niveauEtudes ?niveau .
    } GROUP BY ?niveau ORDER BY DESC(?nombre)
    """
    resultats = select(query)
    return [
        {"niveau": r["niveau"]["value"], "nombre": int(r["nombre"]["value"])}
        for r in resultats
    ]


# ---------------------------------------------------------------------------
# GET /api/apprenants/{id}  - Detail d'un apprenant + ses relations
# ---------------------------------------------------------------------------

@router.get("/{id}", summary="Detail d'un apprenant")
def detail_apprenant(id: str):
    if not valid_id(id):
        raise HTTPException(status_code=400, detail="ID invalide : doit commencer par une majuscule et ne contenir que des lettres, chiffres ou underscores.")

    # Informations de base (avec OPTIONAL pour les champs qui peuvent manquer)
    query = f"""
    SELECT ?nom ?prenom ?email ?niveau ?dateN WHERE {{
        edu:{id} edu:nom ?nom ;
                 edu:prenom ?prenom .
        OPTIONAL {{ edu:{id} edu:email ?email }}
        OPTIONAL {{ edu:{id} edu:niveauEtudes ?niveau }}
        OPTIONAL {{ edu:{id} edu:dateNaissance ?dateN }}
    }}
    """
    res = select(query)
    if not res:
        raise HTTPException(status_code=404, detail=f"Apprenant '{id}' introuvable.")
    r = res[0]

    # Relations : formations, competences, certifications
    q_rel = f"""
    SELECT ?type ?objId ?label WHERE {{
        {{
            edu:{id} edu:estInscritA ?obj .
            ?obj rdfs:label ?label .
            BIND("formation" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
        UNION
        {{
            edu:{id} edu:possedeCompetence ?obj .
            ?obj edu:intitule ?label .
            BIND("competence" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
        UNION
        {{
            edu:{id} edu:obtientCertification ?obj .
            ?obj rdfs:label ?label .
            BIND("certification" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
    }}
    """
    rels = select(q_rel)
    relations = {"formations": [], "competences": [], "certifications": []}
    for rel in rels:
        cle = rel["type"]["value"] + "s"
        if cle in relations:
            relations[cle].append({
                "id": rel["objId"]["value"].split("#")[-1],
                "label": rel["label"]["value"],
            })

    # Gestion des champs potentiellement vides avec .get()
    return {
        "id": id,
        "nom": r["nom"]["value"] if "nom" in r else "Inconnu",
        "prenom": r["prenom"]["value"] if "prenom" in r else "Inconnu",
        "email": r["email"]["value"] if "email" in r else "Non renseigné",
        "niveau": r["niveau"]["value"] if "niveau" in r else "Non renseigné",
        "dateNaissance": r["dateN"]["value"] if "dateN" in r else None,
        "relations": relations,
    }
    if not valid_id(id):
        raise HTTPException(status_code=400, detail="ID invalide : doit commencer par une majuscule et ne contenir que des lettres, chiffres ou underscores.")

    # Informations de base
    query = f"""
    SELECT ?nom ?prenom ?email ?niveau ?dateN WHERE {{
        edu:{id} edu:nom ?nom ;
                 edu:prenom ?prenom ;
                 edu:email ?email ;
                 edu:niveauEtudes ?niveau ;
                 edu:dateNaissance ?dateN .
    }}
    """
    res = select(query)
    if not res:
        raise HTTPException(status_code=404, detail=f"Apprenant '{id}' introuvable.")
    r = res[0]

    # Relations : formations, competences, certifications
    q_rel = f"""
    SELECT ?type ?objId ?label WHERE {{
        {{
            edu:{id} edu:estInscritA ?obj .
            ?obj rdfs:label ?label .
            BIND("formation" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
        UNION
        {{
            edu:{id} edu:possedeCompetence ?obj .
            ?obj edu:intitule ?label .
            BIND("competence" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
        UNION
        {{
            edu:{id} edu:obtientCertification ?obj .
            ?obj rdfs:label ?label .
            BIND("certification" AS ?type)
            BIND(STR(?obj) AS ?objId)
        }}
    }}
    """
    rels = select(q_rel)
    relations = {"formations": [], "competences": [], "certifications": []}
    for rel in rels:
        cle = rel["type"]["value"] + "s"
        if cle in relations:
            relations[cle].append({
                "id": rel["objId"]["value"].split("#")[-1],
                "label": rel["label"]["value"],
            })

    return {
        "id": id,
        "nom": r["nom"]["value"],
        "prenom": r["prenom"]["value"],
        "email": r["email"]["value"],
        "niveau": r["niveau"]["value"],
        "dateNaissance": r["dateN"]["value"],
        "relations": relations,
    }


# ---------------------------------------------------------------------------
# POST /api/apprenants  - Creer un apprenant
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Creer un apprenant")
def creer_apprenant(apprenant: ApprenantCreate):
    if not valid_id(apprenant.id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    # Verifier unicite
    check = select(f"SELECT ?p WHERE {{ edu:{apprenant.id} ?p ?o }} LIMIT 1")
    if check:
        raise HTTPException(status_code=409, detail=f"L'ID '{apprenant.id}' existe deja.")

    query = f"""
    INSERT DATA {{
        edu:{apprenant.id} a owl:NamedIndividual, edu:Apprenant ;
            edu:nom "{esc(apprenant.nom)}" ;
            edu:prenom "{esc(apprenant.prenom)}" ;
            edu:email "{esc(apprenant.email)}" ;
            edu:niveauEtudes "{esc(apprenant.niveauEtudes)}" ;
            edu:dateNaissance "{esc(apprenant.dateNaissance)}"^^xsd:dateTime .
    }}
    """
    update(query)
    return {"message": "Apprenant cree avec succes", "id": apprenant.id}


# ---------------------------------------------------------------------------
# POST /api/apprenants/{id}/inscription  - Inscrire a une formation
# ---------------------------------------------------------------------------

@router.post("/{id}/inscription", summary="Inscrire un apprenant a une formation")
def inscrire_apprenant(
    id: str, 
    formation_id: str = Query(..., description="ID de la formation a laquelle inscrire l'apprenant")
):
    if not valid_id(id) or not valid_id(formation_id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    # Contrainte OWL : max 3 inscriptions simultanees
    q_count = f"SELECT (COUNT(?f) AS ?n) WHERE {{ edu:{id} edu:estInscritA ?f }}"
    res = select(q_count)
    nb_inscriptions = int(res[0]["n"]["value"]) if res else 0
    if nb_inscriptions >= 3:
        raise HTTPException(
            status_code=409,
            detail="Limite de 3 inscriptions simultanees atteinte pour cet apprenant.",
        )

    # Verifier que la formation existe
    check_f = select(f"SELECT ?p WHERE {{ edu:{formation_id} ?p ?o }} LIMIT 1")
    if not check_f:
        raise HTTPException(status_code=404, detail=f"Formation '{formation_id}' introuvable.")

    update(f"INSERT DATA {{ edu:{id} edu:estInscritA edu:{formation_id} }}")
    return {"message": "Inscription reussie", "apprenant": id, "formation": formation_id}


# ---------------------------------------------------------------------------
# DELETE /api/apprenants/{id}  - Supprimer un apprenant
# ---------------------------------------------------------------------------

@router.delete("/{id}", summary="Supprimer un apprenant")
def supprimer_apprenant(id: str):
    if not valid_id(id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    # Verifier existence
    check = select(f"SELECT ?p WHERE {{ edu:{id} ?p ?o }} LIMIT 1")
    if not check:
        raise HTTPException(status_code=404, detail=f"Apprenant '{id}' introuvable.")

    # Supprimer toutes les triplets sortants et entrants
    update(f"DELETE WHERE {{ edu:{id} ?p ?o }}")
    update(f"DELETE WHERE {{ ?s ?p edu:{id} }}")
    return {"message": f"Apprenant '{id}' supprime avec succes."}