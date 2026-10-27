"""
Routeur FastAPI — Ressources pédagogiques (tranche Zahra)
Routes : GET/POST /api/ressources
         GET/PUT/DELETE /api/ressources/{id}
"""

from fastapi import APIRouter, Query
from app import sparql_client as sp
from app.errors import valider_id, echapper, non_trouve, deja_existe, donnee_invalide
from app.models import ListeReponse, RessourceCreation, RessourceModification

router = APIRouter(prefix="/api/ressources", tags=["Ressources"])

TYPES_AUTORISES = {
    "TutorielComplet", "SupportPDF", "GuideRapide",
    "Diapositives", "DocumentationOfficielle", "EditeurEnLigne",
    "DocumentReference", "Video", "Webinaire",
}


# ------------------------------------------------------------------ #
#  GET /api/ressources                                                #
# ------------------------------------------------------------------ #
@router.get("", response_model=ListeReponse)
def lister_ressources(
    q: str = Query("", description="Recherche dans le label"),
    type_: str = Query("", alias="type", description="Filtrer par type"),
    langue: str = Query("", description="Filtrer par langue"),
    competenceId: str = Query("", description="Filtrer par compétence cible"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    filtre_q = f'FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{echapper(q)}")))' if q else ""
    filtre_lang = f'FILTER(?langue = "{echapper(langue)}")' if langue else ""
    filtre_comp = f"?r edu:ressourceCibleCompetence edu:{valider_id(competenceId)} ." if competenceId else ""
    filtre_type = f"?r a edu:{valider_id(type_)} ." if type_ else ""

    rows = sp.select(f"""
        SELECT ?r ?label ?url ?langue WHERE {{
            ?r a/rdfs:subClassOf* edu:RessourcePedagogique .
            OPTIONAL {{ ?r rdfs:label ?label }}
            OPTIONAL {{ ?r edu:urlRessource ?url }}
            OPTIONAL {{ ?r edu:langue ?langue }}
            {filtre_type}
            {filtre_comp}
            {filtre_q}
            {filtre_lang}
        }}
        ORDER BY ?label
        LIMIT {taille} OFFSET {(page - 1) * taille}
    """)

    total_rows = sp.select(f"""
        SELECT (COUNT(?r) AS ?n) WHERE {{
            ?r a/rdfs:subClassOf* edu:RessourcePedagogique .
            OPTIONAL {{ ?r rdfs:label ?label }}
            OPTIONAL {{ ?r edu:langue ?langue }}
            {filtre_type}
            {filtre_comp}
            {filtre_q}
            {filtre_lang}
        }}
    """)

    donnees = [
        {
            "id": sp.uri_locale(sp.valeur(r, "r")),
            "label": sp.valeur(r, "label"),
            "urlRessource": sp.valeur(r, "url"),
            "langue": sp.valeur(r, "langue"),
        }
        for r in rows
    ]
    return {"total": int(sp.valeur(total_rows[0], "n", "0")), "donnees": donnees}


# ------------------------------------------------------------------ #
#  GET /api/ressources/{id}                                          #
# ------------------------------------------------------------------ #
@router.get("/{id}")
def detail_ressource(id: str):
    valider_id(id)

    rows = sp.select(f"""
        SELECT ?label ?url ?langue ?pages ?dureeMin WHERE {{
            edu:{id} a/rdfs:subClassOf* edu:RessourcePedagogique .
            OPTIONAL {{ edu:{id} rdfs:label ?label }}
            OPTIONAL {{ edu:{id} edu:urlRessource ?url }}
            OPTIONAL {{ edu:{id} edu:langue ?langue }}
            OPTIONAL {{ edu:{id} edu:nombrePages ?pages }}
            OPTIONAL {{ edu:{id} edu:dureeMinutes ?dureeMin }}
        }}
    """)
    if not rows:
        non_trouve("Ressource", id)

    comp_rows = sp.select(f"""
        SELECT ?c ?label WHERE {{
            edu:{id} edu:ressourceCibleCompetence ?c .
            OPTIONAL {{ ?c rdfs:label ?label }}
        }}
    """)
    cours_rows = sp.select(f"""
        SELECT ?c ?label WHERE {{
            ?c edu:utiliseRessource edu:{id} .
            OPTIONAL {{ ?c rdfs:label ?label }}
        }}
    """)

    return {
        "id": id,
        "label": sp.valeur(rows[0], "label"),
        "urlRessource": sp.valeur(rows[0], "url"),
        "langue": sp.valeur(rows[0], "langue"),
        "nombrePages": sp.valeur(rows[0], "pages"),
        "dureeMinutes": sp.valeur(rows[0], "dureeMin"),
        "competencesCiblees": [
            {"id": sp.uri_locale(sp.valeur(r, "c")), "label": sp.valeur(r, "label")}
            for r in comp_rows
        ],
        "utiliseeParCours": [
            {"id": sp.uri_locale(sp.valeur(r, "c")), "label": sp.valeur(r, "label")}
            for r in cours_rows
        ],
    }


# ------------------------------------------------------------------ #
#  POST /api/ressources                                              #
# ------------------------------------------------------------------ #
@router.post("", status_code=201)
def creer_ressource(body: RessourceCreation):
    if body.type not in TYPES_AUTORISES:
        donnee_invalide(f"Type inconnu '{body.type}'. Types autorisés : {sorted(TYPES_AUTORISES)}")

    valider_id(body.competenceId)

    id_ = body.type + "_" + body.intitule.strip().replace(" ", "_")
    valider_id(id_)

    if sp.ask(f"ASK {{ edu:{id_} ?p ?o }}"):
        deja_existe("Ressource", id_)

    label = echapper(body.intitule)
    url = echapper(body.urlRessource)
    langue = echapper(body.langue)

    extra = ""
    if body.nombrePages is not None:
        extra += f"edu:{id_} edu:nombrePages {body.nombrePages} .\n"
    if body.dureeMinutes is not None:
        extra += f"edu:{id_} edu:dureeMinutes {body.dureeMinutes} .\n"

    sp.update(f"""
        INSERT DATA {{
            edu:{id_} a owl:NamedIndividual, edu:{body.type} ;
                rdfs:label "{label}"@fr ;
                edu:urlRessource "{url}"^^xsd:string ;
                edu:langue "{langue}"^^xsd:string ;
                edu:ressourceCibleCompetence edu:{body.competenceId} .
            {extra}
        }}
    """)
    return {"id": id_, "label": body.intitule}


# ------------------------------------------------------------------ #
#  PUT /api/ressources/{id}                                         #
# ------------------------------------------------------------------ #
@router.put("/{id}")
def modifier_ressource(id: str, body: RessourceModification):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Ressource", id)

    if body.intitule is not None:
        v = echapper(body.intitule)
        sp.update(f"""
            DELETE {{ edu:{id} rdfs:label ?old }}
            INSERT {{ edu:{id} rdfs:label "{v}"@fr }}
            WHERE  {{ OPTIONAL {{ edu:{id} rdfs:label ?old }} }}
        """)

    if body.urlRessource is not None:
        v = echapper(body.urlRessource)
        sp.update(f"""
            DELETE {{ edu:{id} edu:urlRessource ?old }}
            INSERT {{ edu:{id} edu:urlRessource "{v}"^^xsd:string }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:urlRessource ?old }} }}
        """)

    if body.langue is not None:
        v = echapper(body.langue)
        sp.update(f"""
            DELETE {{ edu:{id} edu:langue ?old }}
            INSERT {{ edu:{id} edu:langue "{v}"^^xsd:string }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:langue ?old }} }}
        """)

    return {"id": id, "modifie": True}


# ------------------------------------------------------------------ #
#  DELETE /api/ressources/{id}                                      #
# ------------------------------------------------------------------ #
@router.delete("/{id}", status_code=204)
def supprimer_ressource(id: str):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Ressource", id)

    sp.update(f"DELETE WHERE {{ edu:{id} ?p ?o }}")
    sp.update(f"DELETE WHERE {{ ?s ?p edu:{id} }}")
