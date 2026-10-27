"""
Routeur FastAPI pour la ressource Evaluation (tranche Linda).
Endpoints : liste (filtres type, module, competence, dates), types, statistiques
des notes minimales par type, detail, creation, modification, suppression.
Une evaluation doit porter sur au moins une competence et un module.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from ..sparql_client import select, update
from ..sparql_outils import (
    LABEL_X, compter, exiger_instance, exiger_instances, exiger_sous_classe, existe,
    generer_id, lit, lit_date, local, num, pagination, relations, sous_classes,
    supprimer_individu, type_direct, val, verifier_id,
)

router = APIRouter()

MODULE_DE = "(edu:evaluationDuModule|^edu:estEvalueParEvaluation)"
COMPETENCE_DE = "(edu:porteSurCompetence|^edu:estMesureePar)"
COURS_DE = "(edu:evalue|^edu:estEvaluePar)"


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class EvaluationIn(BaseModel):
    id: Optional[str] = None
    label: str
    type: str
    dateEvaluation: str
    noteMinimale: float
    coefficient: float
    competences: List[str]
    modules: List[str]
    cours: List[str] = []


# ---------------------------------------------------------------------------
# GET /api/evaluations  - Liste avec filtres
# ---------------------------------------------------------------------------

@router.get("", summary="Lister les evaluations")
def liste_evaluations(
    q: Optional[str] = Query(None, description="Recherche dans le libelle"),
    type: Optional[str] = Query(None, description="Sous-classe d'Evaluation, ex. Quiz"),
    module: Optional[str] = Query(None, description="Id du module, ex. Module_JavaScript"),
    competence: Optional[str] = Query(None, description="Id de la competence, ex. Comp_React"),
    date_min: Optional[str] = Query(None, description="ISO, ex. 2026-11-01"),
    date_max: Optional[str] = Query(None, description="ISO, ex. 2027-01-31"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    where = """
        ?id a/rdfs:subClassOf* edu:Evaluation .
        OPTIONAL { ?id rdfs:label ?l }
        BIND(COALESCE(STR(?l), STRAFTER(STR(?id), "#")) AS ?label)
        OPTIONAL { ?id edu:dateEvaluation ?date }
    """
    if type:
        verifier_id(type, "type")
        where += f" ?id a/rdfs:subClassOf* edu:{type} ."
    if module:
        verifier_id(module, "module")
        where += f" ?id {MODULE_DE} edu:{module} ."
    if competence:
        verifier_id(competence, "competence")
        where += f" ?id {COMPETENCE_DE} edu:{competence} ."
    if date_min:
        where += f" FILTER(BOUND(?date) && ?date >= {lit_date(date_min)})"
    if date_max:
        where += f" FILTER(BOUND(?date) && ?date <= {lit_date(date_max)})"
    if q:
        where += f" FILTER(CONTAINS(LCASE(?label), LCASE({lit(q)})))"

    res = select(f"""
    SELECT ?id (SAMPLE(?label) AS ?lib) (SAMPLE(?date) AS ?d) (SAMPLE(?note) AS ?n)
           (SAMPLE(?coef) AS ?co)
           (GROUP_CONCAT(DISTINCT ?modLabel; separator=", ") AS ?mods) WHERE {{
        {where}
        OPTIONAL {{ ?id edu:noteMinimale ?note }}
        OPTIONAL {{ ?id edu:coefficient ?coef }}
        OPTIONAL {{ ?id {MODULE_DE} ?m . ?m rdfs:label ?modLabel }}
    }} GROUP BY ?id ORDER BY ?d ?lib {pagination(page, taille)}
    """)
    return {
        "total": compter(where),
        "page": page,
        "taille": taille,
        "donnees": [
            {
                "id": local(val(r, "id")),
                "label": val(r, "lib"),
                "type": type_direct(local(val(r, "id")), "Evaluation"),
                "dateEvaluation": val(r, "d"),
                "noteMinimale": num(r, "n"),
                "coefficient": num(r, "co"),
                "modules": val(r, "mods") or "",
            }
            for r in res
        ],
    }


# ---------------------------------------------------------------------------
# GET /api/evaluations/types  - Sous-classes d'Evaluation
# ---------------------------------------------------------------------------

@router.get("/types", summary="Types d'evaluations")
def types_evaluations():
    return sous_classes("Evaluation")


# ---------------------------------------------------------------------------
# GET /api/evaluations/options  - Listes deroulantes du formulaire et des filtres
# ---------------------------------------------------------------------------

@router.get("/options", summary="Types, competences, modules et cours selectionnables")
def options_evaluations():
    return {
        "types": sous_classes("Evaluation"),
        "competences": relations("?x a/rdfs:subClassOf* edu:Competence ."),
        "modules": relations("?x a/rdfs:subClassOf* edu:Module ."),
        "cours": relations("?x a/rdfs:subClassOf* edu:Cours ."),
    }


# ---------------------------------------------------------------------------
# GET /api/evaluations/statistiques  - Moyenne des notes minimales par type
# ---------------------------------------------------------------------------

@router.get("/statistiques", summary="Moyenne des notes minimales par type d'evaluation")
def statistiques_evaluations():
    res = select(f"""
    SELECT ?x ?label (COUNT(DISTINCT ?e) AS ?nb) (AVG(?note) AS ?moyenne)
           (AVG(?coef) AS ?coefMoyen) WHERE {{
        ?e a ?x . ?x rdfs:subClassOf* edu:Evaluation .
        ?e edu:noteMinimale ?note .
        OPTIONAL {{ ?e edu:coefficient ?coef }}
        {LABEL_X}
    }} GROUP BY ?x ?label ORDER BY DESC(?moyenne) ?label
    """)
    return [
        {
            "type": local(val(r, "x")),
            "label": val(r, "label"),
            "nbEvaluations": num(r, "nb"),
            "moyenneNoteMinimale": num(r, "moyenne"),
            "coefficientMoyen": num(r, "coefMoyen"),
        }
        for r in res
    ]


# ---------------------------------------------------------------------------
# GET /api/evaluations/{id}  - Detail
# ---------------------------------------------------------------------------

@router.get("/{id}", summary="Detail d'une evaluation")
def detail_evaluation(id: str):
    exiger_instance(id, "Evaluation")
    res = select(f"""
    SELECT ?label ?date ?note ?coef WHERE {{
        OPTIONAL {{ edu:{id} rdfs:label ?label }}
        OPTIONAL {{ edu:{id} edu:dateEvaluation ?date }}
        OPTIONAL {{ edu:{id} edu:noteMinimale ?note }}
        OPTIONAL {{ edu:{id} edu:coefficient ?coef }}
    }} LIMIT 1
    """)
    r = res[0] if res else {}
    return {
        "id": id,
        "label": val(r, "label") or id,
        "type": type_direct(id, "Evaluation"),
        "dateEvaluation": val(r, "date"),
        "noteMinimale": num(r, "note"),
        "coefficient": num(r, "coef"),
        "competences": relations(f"edu:{id} {COMPETENCE_DE} ?x ."),
        "modules": relations(f"edu:{id} {MODULE_DE} ?x ."),
        "cours": relations(f"edu:{id} {COURS_DE} ?x ."),
        "apprenants": relations(f"?x edu:passeEvaluation|^edu:estPasseePar edu:{id} ."),
    }


def _valider(body: EvaluationIn) -> None:
    if not body.label.strip():
        raise HTTPException(status_code=400, detail="Le libelle est obligatoire.")
    exiger_sous_classe(body.type, "Evaluation")
    if not body.competences:
        raise HTTPException(status_code=400, detail="Une evaluation doit porter sur au moins une competence.")
    if not body.modules:
        raise HTTPException(status_code=400, detail="Une evaluation doit etre rattachee a au moins un module.")
    if not 0 <= body.noteMinimale <= 20:
        raise HTTPException(status_code=400, detail="noteMinimale doit etre comprise entre 0 et 20.")
    if body.coefficient <= 0:
        raise HTTPException(status_code=400, detail="Le coefficient doit etre strictement positif.")
    lit_date(body.dateEvaluation)
    exiger_instances(body.competences, "Competence")
    exiger_instances(body.modules, "Module")
    exiger_instances(body.cours, "Cours")


def _triplets(id: str, body: EvaluationIn) -> str:
    t = [
        f"edu:{id} a owl:NamedIndividual , edu:{body.type} .",
        f"edu:{id} rdfs:label {lit(body.label.strip())}@fr .",
        f"edu:{id} edu:dateEvaluation {lit_date(body.dateEvaluation)} .",
        f"edu:{id} edu:noteMinimale {body.noteMinimale:.2f} .",
        f"edu:{id} edu:coefficient {body.coefficient:.2f} .",
    ]
    t += [f"edu:{id} edu:porteSurCompetence edu:{c} ." for c in body.competences]
    t += [f"edu:{id} edu:evaluationDuModule edu:{m} ." for m in body.modules]
    t += [f"edu:{id} edu:evalue edu:{c} ." for c in body.cours]
    return "\n        ".join(t)


# ---------------------------------------------------------------------------
# POST /api/evaluations  - Creer
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Creer une evaluation")
def creer_evaluation(body: EvaluationIn):
    id = body.id or generer_id("Eval", body.label)
    verifier_id(id)
    if existe(id):
        raise HTTPException(status_code=409, detail=f"L'ID '{id}' existe deja.")
    _valider(body)
    update(f"INSERT DATA {{\n        {_triplets(id, body)}\n    }}")
    return detail_evaluation(id)


# ---------------------------------------------------------------------------
# PUT /api/evaluations/{id}  - Modifier
# ---------------------------------------------------------------------------

@router.put("/{id}", summary="Modifier une evaluation")
def modifier_evaluation(id: str, body: EvaluationIn):
    exiger_instance(id, "Evaluation")
    _valider(body)
    update(f"""
    DELETE {{ edu:{id} a ?t }} WHERE {{ edu:{id} a ?t . ?t rdfs:subClassOf* edu:Evaluation }} ;
    DELETE WHERE {{ edu:{id} rdfs:label ?o }} ;
    DELETE WHERE {{ edu:{id} edu:dateEvaluation ?o }} ;
    DELETE WHERE {{ edu:{id} edu:noteMinimale ?o }} ;
    DELETE WHERE {{ edu:{id} edu:coefficient ?o }} ;
    DELETE WHERE {{ edu:{id} edu:porteSurCompetence ?o }} ;
    DELETE WHERE {{ ?s edu:estMesureePar edu:{id} }} ;
    DELETE WHERE {{ edu:{id} edu:evaluationDuModule ?o }} ;
    DELETE WHERE {{ ?s edu:estEvalueParEvaluation edu:{id} }} ;
    DELETE WHERE {{ edu:{id} edu:evalue ?o }} ;
    DELETE WHERE {{ ?s edu:estEvaluePar edu:{id} }} ;
    INSERT DATA {{
        {_triplets(id, body)}
    }}
    """)
    return detail_evaluation(id)


# ---------------------------------------------------------------------------
# DELETE /api/evaluations/{id}  - Supprimer (sortants et entrants)
# ---------------------------------------------------------------------------

@router.delete("/{id}", status_code=204, summary="Supprimer une evaluation")
def supprimer_evaluation(id: str):
    exiger_instance(id, "Evaluation")
    supprimer_individu(id)
    return Response(status_code=204)
