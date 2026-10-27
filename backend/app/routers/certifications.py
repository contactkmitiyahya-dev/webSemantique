"""
Routeur FastAPI pour la ressource Certification.
Endpoints : liste, detail, creation, attribution a un apprenant.
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

class CertificationCreate(BaseModel):
    id: str
    label: str
    organisme_id: str
    dureeValiditeAns: Optional[int] = None


class AttributionRequest(BaseModel):
    apprenant_id: str
    certification_id: str


# ---------------------------------------------------------------------------
# GET /api/certifications  - Liste de toutes les certifications
# ---------------------------------------------------------------------------

@router.get("", summary="Lister les certifications")
def liste_certifications(
    q: Optional[str] = Query(None, description="Recherche par label"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * taille
    filtre = ""
    if q:
        filtre = f'FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{esc(q)}"))) '

    query = f"""
    SELECT ?id ?label ?validite ?organisme WHERE {{
        ?id a/rdfs:subClassOf* edu:Certification ;
            rdfs:label ?label .
        OPTIONAL {{ ?id edu:dureeValiditeAns ?validite }}
        OPTIONAL {{ ?id edu:delivreeParOrganisme ?org . ?org rdfs:label ?organisme }}
        {filtre}
    }} ORDER BY ?label LIMIT {taille} OFFSET {offset}
    """
    res = select(query)
    return {
        "total": len(res),
        "page": page,
        "taille": taille,
        "donnees": [
            {
                "id": r["id"]["value"].split("#")[-1],
                "label": r["label"]["value"],
                "dureeValiditeAns": r.get("validite", {}).get("value"),
                "organisme": r.get("organisme", {}).get("value"),
            }
            for r in res
        ],
    }


# ---------------------------------------------------------------------------
# GET /api/certifications/{id}  - Detail d'une certification
# ---------------------------------------------------------------------------

@router.get("/{id}", summary="Detail d'une certification")
def detail_certification(id: str):
    if not valid_id(id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    query = f"""
    SELECT ?label ?validite ?organisme WHERE {{
        edu:{id} rdfs:label ?label .
        OPTIONAL {{ edu:{id} edu:dureeValiditeAns ?validite }}
        OPTIONAL {{ edu:{id} edu:delivreeParOrganisme ?org . ?org rdfs:label ?organisme }}
    }}
    """
    res = select(query)
    if not res:
        raise HTTPException(status_code=404, detail=f"Certification '{id}' introuvable.")
    r = res[0]

    # Apprenants ayant obtenu cette certification
    q_apprenants = f"""
    SELECT ?appId ?nom ?prenom WHERE {{
        ?appId edu:obtientCertification edu:{id} ;
               edu:nom ?nom ;
               edu:prenom ?prenom .
    }}
    """
    apprenants = select(q_apprenants)

    return {
        "id": id,
        "label": r["label"]["value"],
        "dureeValiditeAns": r.get("validite", {}).get("value"),
        "organisme": r.get("organisme", {}).get("value"),
        "apprenants": [
            {
                "id": a["appId"]["value"].split("#")[-1],
                "nom": a["nom"]["value"],
                "prenom": a["prenom"]["value"],
            }
            for a in apprenants
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/certifications  - Creer une certification
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Creer une certification")
def creer_certification(cert: CertificationCreate):
    if not valid_id(cert.id):
        raise HTTPException(status_code=400, detail="ID invalide.")
    if not valid_id(cert.organisme_id):
        raise HTTPException(status_code=400, detail="organisme_id invalide.")

    check = select(f"SELECT ?p WHERE {{ edu:{cert.id} ?p ?o }} LIMIT 1")
    if check:
        raise HTTPException(status_code=409, detail=f"L'ID '{cert.id}' existe deja.")

    validite_triple = ""
    if cert.dureeValiditeAns is not None:
        validite_triple = f'edu:dureeValiditeAns {cert.dureeValiditeAns} ;'

    query = f"""
    INSERT DATA {{
        edu:{cert.id} a owl:NamedIndividual, edu:Certification ;
            rdfs:label "{esc(cert.label)}" ;
            {validite_triple}
            edu:delivreeParOrganisme edu:{cert.organisme_id} .
    }}
    """
    update(query)
    return {"message": "Certification creee avec succes", "id": cert.id}


# ---------------------------------------------------------------------------
# POST /api/certifications/attribution  - Attribuer une certification a un apprenant
# ---------------------------------------------------------------------------

@router.post("/attribution", summary="Attribuer une certification a un apprenant")
def attribuer_certification(body: AttributionRequest):
    if not valid_id(body.apprenant_id) or not valid_id(body.certification_id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    # Verifier existence des deux ressources
    check_app = select(f"SELECT ?p WHERE {{ edu:{body.apprenant_id} ?p ?o }} LIMIT 1")
    if not check_app:
        raise HTTPException(status_code=404, detail=f"Apprenant '{body.apprenant_id}' introuvable.")

    check_cert = select(f"SELECT ?p WHERE {{ edu:{body.certification_id} ?p ?o }} LIMIT 1")
    if not check_cert:
        raise HTTPException(status_code=404, detail=f"Certification '{body.certification_id}' introuvable.")

    update(f"INSERT DATA {{ edu:{body.apprenant_id} edu:obtientCertification edu:{body.certification_id} }}")
    return {
        "message": "Certification attribuee avec succes",
        "apprenant": body.apprenant_id,
        "certification": body.certification_id,
    }


# ---------------------------------------------------------------------------
# DELETE /api/certifications/{id}  - Supprimer une certification
# ---------------------------------------------------------------------------

@router.delete("/{id}", summary="Supprimer une certification")
def supprimer_certification(id: str):
    if not valid_id(id):
        raise HTTPException(status_code=400, detail="ID invalide.")

    check = select(f"SELECT ?p WHERE {{ edu:{id} ?p ?o }} LIMIT 1")
    if not check:
        raise HTTPException(status_code=404, detail=f"Certification '{id}' introuvable.")

    update(f"DELETE WHERE {{ edu:{id} ?p ?o }}")
    update(f"DELETE WHERE {{ ?s ?p edu:{id} }}")
    return {"message": f"Certification '{id}' supprimee avec succes."}
