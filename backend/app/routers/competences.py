"""
Routeur FastAPI pour la ressource Competence (tranche Linda).
Endpoints : liste, types, arbre, competences repandues, detail, creation,
modification (controle des cycles), suppression.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from ..sparql_client import select, update
from ..sparql_outils import (
    LABEL_X, compter, exiger_instance, exiger_instances, exiger_sous_classe, existe,
    generer_id, lit, local, num, pagination, relations, sous_classes, supprimer_individu,
    type_direct, val, verifier_id,
)

router = APIRouter()

# estSousCompetenceDe peut aussi etre declaree par son inverse aPourSousCompetence
SOUS_DE = "(edu:estSousCompetenceDe|^edu:aPourSousCompetence)"
EQUIV = "(edu:estEquivalenteA|^edu:estEquivalenteA)"


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class CompetenceIn(BaseModel):
    id: Optional[str] = None
    intitule: str
    type: str = "Competence"
    scoreMaturite: Optional[int] = None
    parents: List[str] = []
    equivalentes: List[str] = []
    technologies: List[str] = []


# ---------------------------------------------------------------------------
# GET /api/competences  - Liste avec filtre de type, score minimal et recherche
# ---------------------------------------------------------------------------

@router.get("", summary="Lister les competences")
def liste_competences(
    q: Optional[str] = Query(None, description="Recherche dans l'intitule"),
    type: Optional[str] = Query(None, description="Sous-classe de Competence, ex. CompetenceFrontend"),
    score_min: Optional[int] = Query(None, ge=0, le=100),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    where = """
        ?id a ?t . ?t rdfs:subClassOf* edu:Competence .
        OPTIONAL { ?id edu:intitule ?i } OPTIONAL { ?id rdfs:label ?l }
        BIND(COALESCE(STR(?i), STR(?l), STRAFTER(STR(?id), "#")) AS ?intitule)
        OPTIONAL { ?id edu:scoreMaturite ?score }
    """
    if type:
        verifier_id(type, "type")
        where += f" ?id a/rdfs:subClassOf* edu:{type} ."
    if score_min is not None:
        where += f" FILTER(BOUND(?score) && ?score >= {score_min})"
    if q:
        where += f" FILTER(CONTAINS(LCASE(?intitule), LCASE({lit(q)})))"

    res = select(f"""
    SELECT ?id (SAMPLE(?intitule) AS ?lib) (SAMPLE(?score) AS ?sc)
           (COUNT(DISTINCT ?sous) AS ?nbSous) WHERE {{
        {where}
        OPTIONAL {{ ?sous {SOUS_DE} ?id }}
    }} GROUP BY ?id ORDER BY ?lib {pagination(page, taille)}
    """)
    return {
        "total": compter(where),
        "page": page,
        "taille": taille,
        "donnees": [
            {
                "id": local(val(r, "id")),
                "intitule": val(r, "lib"),
                "type": type_direct(local(val(r, "id")), "Competence"),
                "scoreMaturite": num(r, "sc"),
                "nbSousCompetences": num(r, "nbSous"),
            }
            for r in res
        ],
    }


# ---------------------------------------------------------------------------
# GET /api/competences/types  - Sous-classes de Competence (listes deroulantes)
# ---------------------------------------------------------------------------

@router.get("/types", summary="Types de competences")
def types_competences():
    return sous_classes("Competence")


# ---------------------------------------------------------------------------
# GET /api/competences/arbre  - Arbre des sous-competences (toutes ou une racine)
# ---------------------------------------------------------------------------

@router.get("/arbre", summary="Arbre des sous-competences")
def arbre_competences(racine: Optional[str] = Query(None, description="Id de la competence racine")):
    if racine:
        exiger_instance(racine, "Competence")

    noeuds = {
        local(val(r, "x")): {"id": local(val(r, "x")), "label": val(r, "label"), "scoreMaturite": num(r, "score")}
        for r in select(f"""
        SELECT DISTINCT ?x ?label ?score WHERE {{
            ?x a/rdfs:subClassOf* edu:Competence .
            OPTIONAL {{ ?x edu:scoreMaturite ?score }}
            {LABEL_X}
        }}""")
    }
    enfants = {}
    a_un_parent = set()
    for r in select(f"SELECT DISTINCT ?e ?p WHERE {{ ?e {SOUS_DE} ?p }}"):
        e, p = local(val(r, "e")), local(val(r, "p"))
        if e in noeuds and p in noeuds:
            enfants.setdefault(p, []).append(e)
            a_un_parent.add(e)

    def construire(cid, chemin):
        # chemin : garde-fou si un cycle a ete charge a la main dans Fuseki
        fils = [construire(f, chemin | {f}) for f in sorted(enfants.get(cid, []), key=lambda f: noeuds[f]["label"]) if f not in chemin]
        return {**noeuds[cid], "enfants": fils}

    racines = [racine] if racine else sorted((c for c in noeuds if c not in a_un_parent), key=lambda c: noeuds[c]["label"])
    return [construire(c, {c}) for c in racines]


# ---------------------------------------------------------------------------
# GET /api/competences/repandues  - Competences les plus possedees (GROUP BY)
# ---------------------------------------------------------------------------

@router.get("/repandues", summary="Competences les plus repandues chez les apprenants")
def competences_repandues(limite: int = Query(10, ge=1, le=50)):
    res = select(f"""
    SELECT ?x ?label (COUNT(DISTINCT ?a) AS ?nb) WHERE {{
        ?a edu:possedeCompetence|^edu:estPossedeePar ?x .
        {LABEL_X}
    }} GROUP BY ?x ?label ORDER BY DESC(?nb) ?label LIMIT {limite}
    """)
    return [{"id": local(val(r, "x")), "label": val(r, "label"), "nbApprenants": num(r, "nb")} for r in res]


# ---------------------------------------------------------------------------
# GET /api/competences/{id}  - Detail : proprietes + relations
# ---------------------------------------------------------------------------

@router.get("/{id}", summary="Detail d'une competence")
def detail_competence(id: str):
    exiger_instance(id, "Competence")
    res = select(f"""
    SELECT ?intitule ?label ?score WHERE {{
        OPTIONAL {{ edu:{id} edu:intitule ?intitule }}
        OPTIONAL {{ edu:{id} rdfs:label ?label }}
        OPTIONAL {{ edu:{id} edu:scoreMaturite ?score }}
    }} LIMIT 1
    """)
    r = res[0] if res else {}
    return {
        "id": id,
        "intitule": val(r, "intitule") or val(r, "label") or id,
        "type": type_direct(id, "Competence"),
        "scoreMaturite": num(r, "score"),
        "parents": relations(f"edu:{id} {SOUS_DE} ?x ."),
        "ancetres": relations(f"edu:{id} {SOUS_DE}+ ?x ."),
        "sousCompetences": relations(f"?x {SOUS_DE} edu:{id} ."),
        "toutesSousCompetences": relations(f"?x {SOUS_DE}+ edu:{id} ."),
        "equivalentes": relations(f"edu:{id} {EQUIV} ?x . FILTER(?x != edu:{id})"),
        "technologies": relations(f"edu:{id} edu:competenceSurTechnologie|^edu:estMobiliseePar ?x ."),
        # Modules qui demandent la competence en entree
        "modulesRequierent": relations(f"?x edu:requiertCompetence|^edu:estRequisePar edu:{id} ."),
        # Modules dont un cours developpe la competence ou l'une de ses sous-competences
        "modulesPourAcquerir": relations(f"""
            ?x edu:contientCours|^edu:appartientAuModule ?cours .
            ?cours edu:developpeCompetence|^edu:estDeveloppeePar ?s .
            ?s {SOUS_DE}* edu:{id} ."""),
        "evaluations": relations(f"?x edu:porteSurCompetence|^edu:estMesureePar edu:{id} ."),
        "apprenants": relations(f"?x edu:possedeCompetence|^edu:estPossedeePar edu:{id} ."),
    }


# ---------------------------------------------------------------------------
# Validation commune a la creation et a la modification
# ---------------------------------------------------------------------------

def _valider(body: CompetenceIn, id: str) -> None:
    if not body.intitule.strip():
        raise HTTPException(status_code=400, detail="L'intitule est obligatoire.")
    if body.scoreMaturite is not None and not 0 <= body.scoreMaturite <= 100:
        raise HTTPException(status_code=400, detail="scoreMaturite doit etre compris entre 0 et 100.")
    exiger_sous_classe(body.type, "Competence")
    if id in body.parents:
        raise HTTPException(status_code=400, detail="Une competence ne peut pas etre sa propre sous-competence.")
    if id in body.equivalentes:
        raise HTTPException(status_code=400, detail="Une competence ne peut pas etre equivalente a elle-meme.")
    exiger_instances(body.parents, "Competence")
    exiger_instances(body.equivalentes, "Competence")
    exiger_instances(body.technologies, "Technologie")
    # Cycle : le parent choisi est-il deja une sous-competence (directe ou indirecte) de id ?
    for p in body.parents:
        if select(f"SELECT ?x WHERE {{ edu:{p} {SOUS_DE}+ edu:{id} . BIND(1 AS ?x) }} LIMIT 1"):
            raise HTTPException(status_code=400, detail=f"Cycle refuse : '{p}' est deja une sous-competence de '{id}'.")


def _triplets(id: str, body: CompetenceIn) -> str:
    t = [
        f"edu:{id} a owl:NamedIndividual , edu:{body.type} .",
        f"edu:{id} rdfs:label {lit(body.intitule.strip())}@fr .",
        f"edu:{id} edu:intitule {lit(body.intitule.strip())}^^xsd:string .",
    ]
    if body.scoreMaturite is not None:
        t.append(f"edu:{id} edu:scoreMaturite {body.scoreMaturite} .")
    t += [f"edu:{id} edu:estSousCompetenceDe edu:{p} ." for p in body.parents]
    t += [f"edu:{id} edu:competenceSurTechnologie edu:{te} ." for te in body.technologies]
    # Symetrique : on ecrit les deux sens
    for e in body.equivalentes:
        t += [f"edu:{id} edu:estEquivalenteA edu:{e} .", f"edu:{e} edu:estEquivalenteA edu:{id} ."]
    return "\n        ".join(t)


# ---------------------------------------------------------------------------
# POST /api/competences  - Creer une competence
# ---------------------------------------------------------------------------

@router.post("", status_code=201, summary="Creer une competence")
def creer_competence(body: CompetenceIn):
    id = body.id or generer_id("Comp", body.intitule)
    verifier_id(id)
    if existe(id):
        raise HTTPException(status_code=409, detail=f"L'ID '{id}' existe deja.")
    _valider(body, id)
    update(f"INSERT DATA {{\n        {_triplets(id, body)}\n    }}")
    return detail_competence(id)


# ---------------------------------------------------------------------------
# PUT /api/competences/{id}  - Remplacer les proprietes et relations
# ---------------------------------------------------------------------------

@router.put("/{id}", summary="Modifier une competence")
def modifier_competence(id: str, body: CompetenceIn):
    exiger_instance(id, "Competence")
    _valider(body, id)
    update(f"""
    DELETE {{ edu:{id} a ?t }} WHERE {{ edu:{id} a ?t . ?t rdfs:subClassOf* edu:Competence }} ;
    DELETE WHERE {{ edu:{id} rdfs:label ?o }} ;
    DELETE WHERE {{ edu:{id} edu:intitule ?o }} ;
    DELETE WHERE {{ edu:{id} edu:scoreMaturite ?o }} ;
    DELETE WHERE {{ edu:{id} edu:estSousCompetenceDe ?o }} ;
    DELETE WHERE {{ ?s edu:aPourSousCompetence edu:{id} }} ;
    DELETE WHERE {{ edu:{id} edu:competenceSurTechnologie ?o }} ;
    DELETE WHERE {{ ?s edu:estMobiliseePar edu:{id} }} ;
    DELETE WHERE {{ edu:{id} edu:estEquivalenteA ?o }} ;
    DELETE WHERE {{ ?s edu:estEquivalenteA edu:{id} }} ;
    INSERT DATA {{
        {_triplets(id, body)}
    }}
    """)
    return detail_competence(id)


# ---------------------------------------------------------------------------
# DELETE /api/competences/{id}  - Supprimer (triplets sortants et entrants)
# ---------------------------------------------------------------------------

@router.delete("/{id}", status_code=204, summary="Supprimer une competence")
def supprimer_competence(id: str):
    exiger_instance(id, "Competence")
    # Une evaluation doit porter sur au moins une competence : on refuse de la laisser vide
    orphelines = select(f"""
    SELECT ?e WHERE {{
        ?e edu:porteSurCompetence edu:{id} .
        FILTER NOT EXISTS {{ ?e edu:porteSurCompetence ?autre . FILTER(?autre != edu:{id}) }}
    }}""")
    if orphelines:
        noms = ", ".join(local(val(r, "e")) for r in orphelines)
        raise HTTPException(status_code=409, detail=f"Suppression refusee : {noms} ne porterai(en)t plus sur aucune competence.")
    supprimer_individu(id)
    return Response(status_code=204)
