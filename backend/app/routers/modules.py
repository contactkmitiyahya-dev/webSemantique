"""
Routeur FastAPI — Modules (tranche Zahra)
Routes : GET /api/modules, GET /api/modules/{id},
         POST /api/modules, PUT /api/modules/{id}, DELETE /api/modules/{id}
         GET /api/modules/{id}/prerequis
         GET /api/modules/{id}/competences-requises
"""

from fastapi import APIRouter, HTTPException, Query
from app import sparql_client as sp
from app.config import EDU_NS
from app.errors import valider_id, echapper, non_trouve, deja_existe, donnee_invalide
from app.models import ListeReponse, ModuleCreation, ModuleModification, PrerequisAjout

router = APIRouter(prefix="/api/modules", tags=["Modules"])


# ------------------------------------------------------------------ #
#  GET /api/modules                                                   #
# ------------------------------------------------------------------ #
@router.get("", response_model=ListeReponse)
def lister_modules(
    q: str = Query("", description="Recherche dans l'intitulé"),
    niveau: str = Query("", description="Filtrer par niveau de difficulté"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    filtre_recherche = f'FILTER(CONTAINS(LCASE(STR(?intitule)), LCASE("{echapper(q)}")))' if q else ""
    filtre_niveau = f'FILTER(?niveau = "{echapper(niveau)}")' if niveau else ""

    rows = sp.select(f"""
        SELECT ?m ?intitule ?duree ?niveau WHERE {{
            ?m a/rdfs:subClassOf* edu:Module ;
               edu:intitule ?intitule .
            OPTIONAL {{ ?m edu:dureeHeures ?duree }}
            OPTIONAL {{ ?m edu:niveauDifficulte ?niveau }}
            {filtre_recherche}
            {filtre_niveau}
        }}
        ORDER BY ?intitule
        LIMIT {taille} OFFSET {(page - 1) * taille}
    """)

    total_rows = sp.select(f"""
        SELECT (COUNT(?m) AS ?n) WHERE {{
            ?m a/rdfs:subClassOf* edu:Module ;
               edu:intitule ?intitule .
            OPTIONAL {{ ?m edu:niveauDifficulte ?niveau }}
            {filtre_recherche}
            {filtre_niveau}
        }}
    """)

    donnees = [
        {
            "id": sp.uri_locale(sp.valeur(r, "m")),
            "intitule": sp.valeur(r, "intitule"),
            "dureeHeures": sp.valeur(r, "duree"),
            "niveauDifficulte": sp.valeur(r, "niveau"),
        }
        for r in rows
    ]
    return {"total": int(sp.valeur(total_rows[0], "n", "0")), "donnees": donnees}


# ------------------------------------------------------------------ #
#  GET /api/modules/{id}                                              #
# ------------------------------------------------------------------ #
@router.get("/{id}")
def detail_module(id: str):
    valider_id(id)
    uri = f"edu:{id}"

    rows = sp.select(f"""
        SELECT ?intitule ?duree ?niveau WHERE {{
            {uri} edu:intitule ?intitule .
            OPTIONAL {{ {uri} edu:dureeHeures ?duree }}
            OPTIONAL {{ {uri} edu:niveauDifficulte ?niveau }}
        }}
    """)
    if not rows:
        non_trouve("Module", id)

    cours_rows = sp.select(f"""
        SELECT ?c ?label ?ordre WHERE {{
            {uri} edu:contientCours ?c .
            OPTIONAL {{ ?c rdfs:label ?label }}
            OPTIONAL {{ ?c edu:ordreDansModule ?ordre }}
        }} ORDER BY ?ordre ?label
    """)

    prereq_rows = sp.select(f"""
        SELECT ?p ?label WHERE {{
            {uri} edu:aPourPrerequis ?p .
            OPTIONAL {{ ?p rdfs:label ?label }}
        }}
    """)

    return {
        "id": id,
        "intitule": sp.valeur(rows[0], "intitule"),
        "dureeHeures": sp.valeur(rows[0], "duree"),
        "niveauDifficulte": sp.valeur(rows[0], "niveau"),
        "cours": [
            {"id": sp.uri_locale(sp.valeur(r, "c")), "label": sp.valeur(r, "label")}
            for r in cours_rows
        ],
        "prerequis": [
            {"id": sp.uri_locale(sp.valeur(r, "p")), "label": sp.valeur(r, "label")}
            for r in prereq_rows
        ],
    }


# ------------------------------------------------------------------ #
#  GET /api/modules/{id}/prerequis  (directs + indirects)            #
# ------------------------------------------------------------------ #
@router.get("/{id}/prerequis")
def prerequis_module(id: str):
    valider_id(id)
    rows = sp.select(f"""
        SELECT DISTINCT ?p ?label WHERE {{
            edu:{id} edu:aPourPrerequis+ ?p .
            OPTIONAL {{ ?p rdfs:label ?label }}
        }}
    """)
    return {
        "moduleId": id,
        "prerequis": [
            {"id": sp.uri_locale(sp.valeur(r, "p")), "label": sp.valeur(r, "label")}
            for r in rows
        ],
    }


# ------------------------------------------------------------------ #
#  GET /api/modules/{id}/competences-requises                        #
# ------------------------------------------------------------------ #
@router.get("/{id}/competences-requises")
def competences_requises(id: str):
    valider_id(id)
    rows = sp.select(f"""
        SELECT DISTINCT ?c ?label WHERE {{
            edu:{id} edu:aPourPrerequis* ?m .
            ?m edu:requiertCompetence ?c .
            OPTIONAL {{ ?c rdfs:label ?label }}
        }}
    """)
    return {
        "moduleId": id,
        "competencesRequises": [
            {"id": sp.uri_locale(sp.valeur(r, "c")), "label": sp.valeur(r, "label")}
            for r in rows
        ],
    }


# ------------------------------------------------------------------ #
#  POST /api/modules                                                  #
# ------------------------------------------------------------------ #
@router.post("", status_code=201)
def creer_module(body: ModuleCreation):
    intitule = echapper(body.intitule)
    niveau = echapper(body.niveauDifficulte)

    # Générer un id depuis l'intitulé
    id_ = body.intitule.strip().replace(" ", "_")
    valider_id(id_)

    # Vérifier que l'id n'existe pas déjà
    if sp.ask(f"ASK {{ edu:{id_} ?p ?o }}"):
        deja_existe("Module", id_)

    if body.prerequisId:
        valider_id(body.prerequisId)
        if not sp.ask(f"ASK {{ edu:{body.prerequisId} ?p ?o }}"):
            donnee_invalide(f"Prérequis '{body.prerequisId}' introuvable.")

    prereq_triple = (
        f"edu:{id_} edu:aPourPrerequis edu:{body.prerequisId} ."
        if body.prerequisId else ""
    )

    sp.update(f"""
        INSERT DATA {{
            edu:{id_} a owl:NamedIndividual, edu:Module ;
                rdfs:label "{intitule}"@fr ;
                edu:intitule "{intitule}"^^xsd:string ;
                edu:dureeHeures {body.dureeHeures} ;
                edu:niveauDifficulte "{niveau}"^^xsd:string .
            {prereq_triple}
        }}
    """)
    return {"id": id_, "intitule": body.intitule}


# ------------------------------------------------------------------ #
#  POST /api/modules/{id}/prerequis                                  #
# ------------------------------------------------------------------ #
@router.post("/{id}/prerequis", status_code=201)
def ajouter_prerequis(id: str, body: PrerequisAjout):
    valider_id(id)
    valider_id(body.prerequisId)

    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Module", id)
    if not sp.ask(f"ASK {{ edu:{body.prerequisId} ?p ?o }}"):
        donnee_invalide(f"Module '{body.prerequisId}' introuvable.")

    if id == body.prerequisId or sp.ask(
        f"ASK {{ edu:{body.prerequisId} edu:aPourPrerequis* edu:{id} }}"
    ):
        donnee_invalide("Ce prérequis crée un cycle.")

    sp.update(f"INSERT DATA {{ edu:{id} edu:aPourPrerequis edu:{body.prerequisId} }}")
    return {"id": id, "prerequisId": body.prerequisId}


# ------------------------------------------------------------------ #
#  PUT /api/modules/{id}                                             #
# ------------------------------------------------------------------ #
@router.put("/{id}")
def modifier_module(id: str, body: ModuleModification):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Module", id)

    if body.intitule is not None:
        v = echapper(body.intitule)
        sp.update(f"""
            DELETE {{ edu:{id} edu:intitule ?old ; rdfs:label ?oldl }}
            INSERT {{ edu:{id} edu:intitule "{v}"^^xsd:string ;
                               rdfs:label "{v}"@fr }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:intitule ?old }}
                      OPTIONAL {{ edu:{id} rdfs:label ?oldl }} }}
        """)

    if body.dureeHeures is not None:
        sp.update(f"""
            DELETE {{ edu:{id} edu:dureeHeures ?old }}
            INSERT {{ edu:{id} edu:dureeHeures {body.dureeHeures} }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:dureeHeures ?old }} }}
        """)

    if body.niveauDifficulte is not None:
        v = echapper(body.niveauDifficulte)
        sp.update(f"""
            DELETE {{ edu:{id} edu:niveauDifficulte ?old }}
            INSERT {{ edu:{id} edu:niveauDifficulte "{v}"^^xsd:string }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:niveauDifficulte ?old }} }}
        """)

    return {"id": id, "modifie": True}


# ------------------------------------------------------------------ #
#  DELETE /api/modules/{id}                                          #
# ------------------------------------------------------------------ #
@router.delete("/{id}", status_code=204)
def supprimer_module(id: str):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Module", id)
    if sp.ask(f"ASK {{ edu:{id} edu:contientCours ?c }}") or sp.ask(
        f"ASK {{ ?m edu:aPourPrerequis edu:{id} }}"
    ):
        raise HTTPException(
            status_code=409,
            detail="Module lié à des cours ou à d'autres modules : suppression refusée.",
        )

    # Supprimer triplets sortants puis entrants
    sp.update(f"DELETE WHERE {{ edu:{id} ?p ?o }}")
    sp.update(f"DELETE WHERE {{ ?s ?p edu:{id} }}")
