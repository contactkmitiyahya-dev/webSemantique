"""
Routeur FastAPI pour la ressource Technologie (tranche Linda).
Endpoints : liste, types, detail, creation, modification, suppression.
Le lien competence -> technologie (competenceSurTechnologie) est porte par la competence.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from ..sparql_client import select_brut as select, update  # format brut : r["x"]["value"]
from ..sparql_outils import (
    compter, exiger_instance, exiger_instances, exiger_sous_classe, existe, generer_id,
    lit, local, pagination, relations, sous_classes, supprimer_individu, type_direct,
    val, verifier_id,
)

router = APIRouter()

COMPETENCES_DE = "(edu:competenceSurTechnologie|^edu:estMobiliseePar)"


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class TechnologieIn(BaseModel):
    id: Optional[str] = None
    label: str
    type: str = "Technologie"
    competences: List[str] = []


# ---------------------------------------------------------------------------
# GET /api/technologies  - Liste avec filtre de type et recherche
# ---------------------------------------------------------------------------

@router.get("", summary="Lister les technologies")
def liste_technologies(
    q: Optional[str] = Query(None, description="Recherche dans le libelle"),
    type: Optional[str] = Query(None, description="Sous-classe de Technologie, ex. TechnologieFrontend"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    where = """
        ?id a/rdfs:subClassOf* edu:Technologie .
        OPTIONAL { ?id rdfs:label ?l }
        BIND(COALESCE(STR(?l), STRAFTER(STR(?id), "#")) AS ?label)
    """
    if type:
        verifier_id(type, "type")
        where += f" ?id a/rdfs:subClassOf* edu:{type} ."
    if q:
        where += f" FILTER(CONTAINS(LCASE(?label), LCASE({lit(q)})))"

    res = select(f"""
    SELECT ?id (SAMPLE(?label) AS ?lib) (COUNT(DISTINCT ?c) AS ?nbComp)
           (COUNT(DISTINCT ?cours) AS ?nbCours) WHERE {{
        {where}
        OPTIONAL {{ ?c {COMPETENCES_DE} ?id }}
        OPTIONAL {{ ?cours edu:utiliseTechnologie|^edu:estEnseigneeDans ?id }}
    }} GROUP BY ?id ORDER BY ?lib {pagination(page, taille)}
    """)
    return {
        "total": compter(where),
        "page": page,
        "taille": taille,
        "donnees": [
            {
                "id": local(val(r, "id")),
                "label": val(r, "lib"),
                "type": type_direct(local(val(r, "id")), "Technologie"),
                "nbCompetences": int(val(r, "nbComp", 0)),
                "nbCours": int(val(r, "nbCours", 0)),
            }
            for r in res
        ],
    }


# ---------------------------------------------------------------------------
# GET /api/technologies/types  - Sous-classes de Technologie
# ---------------------------------------------------------------------------

@router.get("/types", summary="Types de technologies")
def types_technologies():
    return sous_classes("Technologie")


# ---------------------------------------------------------------------------
# GET /api/technologies/{id}  - Detail
# ---------------------------------------------------------------------------

@router.get("/{id}", summary="Detail d'une technologie")
def detail_technologie(id: str):
    exiger_instance(id, "Technologie")
    res = select(f"SELECT ?label WHERE {{ edu:{id} rdfs:label ?label }} LIMIT 1")
    return {
        "id": id,
        "label": val(res[0], "label") if res else id,
        "type": type_direct(id, "Technologie"),
        "competences": relations(f"?x {COMPETENCES_DE} edu:{id} ."),
        "cours": relations(f"?x edu:utiliseTechnologie|^edu:estEnseigneeDans edu:{id} ."),
        "apprenants": relations(f"?x edu:maitriseTechnologie|^edu:estMaitriseePar edu:{id} ."),
    }


def _valider(body: TechnologieIn) -> None:
    if not body.label.strip():
        raise HTTPException(status_code=400, detail="Le libelle est obligatoire.")
    exiger_sous_classe(body.type, "Technologie")
    exiger_instances(body.competences, "Competence")


def _triplets(id: str, body: TechnologieIn) -> str:
    t = [
        f"edu:{id} a owl:NamedIndividual , edu:{body.type} .",
        f"edu:{id} rdfs:label {lit(body.label.strip())}@fr .",
    ]
    t += [f"edu:{c} edu:competenceSurTechnologie edu:{id} ." for c in body.competences]
    return "\n        ".join(t)


# ---------------------------------------------------------------------------
# POST /api/technologies  - Creer
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Creer une technologie")
def creer_technologie(body: TechnologieIn):
    id = body.id or generer_id("Tech", body.label)
    verifier_id(id)
    if existe(id):
        raise HTTPException(status_code=409, detail=f"L'ID '{id}' existe deja.")
    _valider(body)
    update(f"INSERT DATA {{\n        {_triplets(id, body)}\n    }}")
    return detail_technologie(id)


# ---------------------------------------------------------------------------
# PUT /api/technologies/{id}  - Modifier
# ---------------------------------------------------------------------------

@router.put("/{id}", summary="Modifier une technologie")
def modifier_technologie(id: str, body: TechnologieIn):
    exiger_instance(id, "Technologie")
    _valider(body)
    update(f"""
    DELETE {{ edu:{id} a ?t }} WHERE {{ edu:{id} a ?t . ?t rdfs:subClassOf* edu:Technologie }} ;
    DELETE WHERE {{ edu:{id} rdfs:label ?o }} ;
    DELETE WHERE {{ ?c edu:competenceSurTechnologie edu:{id} }} ;
    DELETE WHERE {{ edu:{id} edu:estMobiliseePar ?c }} ;
    INSERT DATA {{
        {_triplets(id, body)}
    }}
    """)
    return detail_technologie(id)


# ---------------------------------------------------------------------------
# DELETE /api/technologies/{id}  - Supprimer (sortants et entrants)
# ---------------------------------------------------------------------------

@router.delete("/{id}", status_code=204, summary="Supprimer une technologie")
def supprimer_technologie(id: str):
    exiger_instance(id, "Technologie")
    # Axiome Cours : utiliseTechnologie some Technologie -> on ne laisse pas un cours sans technologie
    orphelins = select(f"""
    SELECT ?c WHERE {{
        ?c edu:utiliseTechnologie edu:{id} .
        FILTER NOT EXISTS {{ ?c edu:utiliseTechnologie ?autre . FILTER(?autre != edu:{id}) }}
    }}""")
    if orphelins:
        noms = ", ".join(local(val(r, "c")) for r in orphelins)
        raise HTTPException(status_code=409, detail=f"Suppression refusee : {noms} n'utiliserai(en)t plus aucune technologie.")
    supprimer_individu(id)
    return Response(status_code=204)
