"""
Routeur FastAPI — Cours (tranche Zahra)
Routes : GET/POST /api/cours
         GET/PUT/DELETE /api/cours/{id}
"""

from fastapi import APIRouter, Query
from app import sparql_client as sp
from app.errors import valider_id, echapper, non_trouve, deja_existe, donnee_invalide
from app.models import ListeReponse, CoursCreation, CoursModification

router = APIRouter(prefix="/api/cours", tags=["Cours"])


# ------------------------------------------------------------------ #
#  GET /api/cours                                                     #
# ------------------------------------------------------------------ #
@router.get("", response_model=ListeReponse)
def lister_cours(
    q: str = Query("", description="Recherche dans l'intitulé"),
    niveau: str = Query("", description="Filtrer par niveau"),
    moduleId: str = Query("", description="Filtrer par module"),
    technologieId: str = Query("", description="Filtrer par technologie"),
    page: int = Query(1, ge=1),
    taille: int = Query(20, ge=1, le=100),
):
    filtre_q = f'FILTER(CONTAINS(LCASE(STR(?intitule)), LCASE("{echapper(q)}")))' if q else ""
    filtre_niv = f'FILTER(?niveau = "{echapper(niveau)}")' if niveau else ""
    filtre_mod = f"?c edu:appartientAuModule edu:{valider_id(moduleId)} ." if moduleId else ""
    filtre_tech = f"?c edu:utiliseTechnologie edu:{valider_id(technologieId)} ." if technologieId else ""

    rows = sp.select(f"""
        SELECT ?c ?intitule ?duree ?niveau ?ordre WHERE {{
            ?c a/rdfs:subClassOf* edu:Cours ;
               edu:intitule ?intitule .
            OPTIONAL {{ ?c edu:dureeHeures ?duree }}
            OPTIONAL {{ ?c edu:niveauDifficulte ?niveau }}
            OPTIONAL {{ ?c edu:ordreDansModule ?ordre }}
            {filtre_mod}
            {filtre_tech}
            {filtre_q}
            {filtre_niv}
        }}
        ORDER BY ?ordre ?intitule
        LIMIT {taille} OFFSET {(page - 1) * taille}
    """)

    total_rows = sp.select(f"""
        SELECT (COUNT(?c) AS ?n) WHERE {{
            ?c a/rdfs:subClassOf* edu:Cours ;
               edu:intitule ?intitule .
            OPTIONAL {{ ?c edu:niveauDifficulte ?niveau }}
            {filtre_mod}
            {filtre_tech}
            {filtre_q}
            {filtre_niv}
        }}
    """)

    donnees = [
        {
            "id": sp.uri_locale(sp.valeur(r, "c")),
            "intitule": sp.valeur(r, "intitule"),
            "dureeHeures": sp.valeur(r, "duree"),
            "niveauDifficulte": sp.valeur(r, "niveau"),
            "ordreDansModule": sp.valeur(r, "ordre"),
        }
        for r in rows
    ]
    return {"total": int(sp.valeur(total_rows[0], "n", "0")), "donnees": donnees}


# ------------------------------------------------------------------ #
#  GET /api/cours/{id}                                               #
# ------------------------------------------------------------------ #
@router.get("/{id}")
def detail_cours(id: str):
    valider_id(id)

    rows = sp.select(f"""
        SELECT ?intitule ?duree ?niveau ?ordre WHERE {{
            edu:{id} edu:intitule ?intitule .
            OPTIONAL {{ edu:{id} edu:dureeHeures ?duree }}
            OPTIONAL {{ edu:{id} edu:niveauDifficulte ?niveau }}
            OPTIONAL {{ edu:{id} edu:ordreDansModule ?ordre }}
        }}
    """)
    if not rows:
        non_trouve("Cours", id)

    module_rows = sp.select(f"""
        SELECT ?m ?label WHERE {{
            edu:{id} edu:appartientAuModule ?m .
            OPTIONAL {{ ?m rdfs:label ?label }}
        }}
    """)
    formateur_rows = sp.select(f"""
        SELECT ?f ?label WHERE {{
            edu:{id} edu:enseignePar ?f .
            OPTIONAL {{ ?f rdfs:label ?label }}
        }}
    """)
    comp_rows = sp.select(f"""
        SELECT ?c ?label WHERE {{
            edu:{id} edu:developpeCompetence ?c .
            OPTIONAL {{ ?c rdfs:label ?label }}
        }}
    """)
    tech_rows = sp.select(f"""
        SELECT ?t ?label WHERE {{
            edu:{id} edu:utiliseTechnologie ?t .
            OPTIONAL {{ ?t rdfs:label ?label }}
        }}
    """)
    ressource_rows = sp.select(f"""
        SELECT ?r ?label WHERE {{
            edu:{id} edu:utiliseRessource ?r .
            OPTIONAL {{ ?r rdfs:label ?label }}
        }}
    """)

    def liste(rows_, cle):
        return [{"id": sp.uri_locale(sp.valeur(r, cle)), "label": sp.valeur(r, "label")} for r in rows_]

    return {
        "id": id,
        "intitule": sp.valeur(rows[0], "intitule"),
        "dureeHeures": sp.valeur(rows[0], "duree"),
        "niveauDifficulte": sp.valeur(rows[0], "niveau"),
        "ordreDansModule": sp.valeur(rows[0], "ordre"),
        "module": liste(module_rows, "m"),
        "formateur": liste(formateur_rows, "f"),
        "competences": liste(comp_rows, "c"),
        "technologies": liste(tech_rows, "t"),
        "ressources": liste(ressource_rows, "r"),
    }


# ------------------------------------------------------------------ #
#  POST /api/cours                                                    #
# ------------------------------------------------------------------ #
@router.post("", status_code=201)
def creer_cours(body: CoursCreation):
    valider_id(body.moduleId)
    valider_id(body.formateurId)
    valider_id(body.competenceId)
    valider_id(body.technologieId)

    id_ = "Cours_" + body.intitule.strip().replace(" ", "_")
    valider_id(id_)

    if sp.ask(f"ASK {{ edu:{id_} ?p ?o }}"):
        deja_existe("Cours", id_)

    # Le module et le formateur sont obligatoires
    if not sp.ask(f"ASK {{ edu:{body.moduleId} ?p ?o }}"):
        donnee_invalide(f"Module '{body.moduleId}' introuvable.")

    if not sp.ask(f"ASK {{ edu:{body.formateurId} ?p ?o }}"):
        donnee_invalide(f"Formateur '{body.formateurId}' introuvable.")

    intitule = echapper(body.intitule)
    niveau = echapper(body.niveauDifficulte)

    sp.update(f"""
        INSERT DATA {{
            edu:{id_} a owl:NamedIndividual, edu:Cours ;
                rdfs:label "{intitule}"@fr ;
                edu:intitule "{intitule}"^^xsd:string ;
                edu:dureeHeures {body.dureeHeures} ;
                edu:niveauDifficulte "{niveau}"^^xsd:string ;
                edu:ordreDansModule {body.ordreDansModule} ;
                edu:appartientAuModule edu:{body.moduleId} ;
                edu:enseignePar edu:{body.formateurId} ;
                edu:developpeCompetence edu:{body.competenceId} ;
                edu:utiliseTechnologie edu:{body.technologieId} .
            edu:{body.moduleId} edu:contientCours edu:{id_} .
        }}
    """)
    return {"id": id_, "intitule": body.intitule}


# ------------------------------------------------------------------ #
#  PUT /api/cours/{id}                                               #
# ------------------------------------------------------------------ #
@router.put("/{id}")
def modifier_cours(id: str, body: CoursModification):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Cours", id)

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

    if body.ordreDansModule is not None:
        sp.update(f"""
            DELETE {{ edu:{id} edu:ordreDansModule ?old }}
            INSERT {{ edu:{id} edu:ordreDansModule {body.ordreDansModule} }}
            WHERE  {{ OPTIONAL {{ edu:{id} edu:ordreDansModule ?old }} }}
        """)

    return {"id": id, "modifie": True}


# ------------------------------------------------------------------ #
#  DELETE /api/cours/{id}                                            #
# ------------------------------------------------------------------ #
@router.delete("/{id}", status_code=204)
def supprimer_cours(id: str):
    valider_id(id)
    if not sp.ask(f"ASK {{ edu:{id} ?p ?o }}"):
        non_trouve("Cours", id)

    sp.update(f"DELETE WHERE {{ edu:{id} ?p ?o }}")
    sp.update(f"DELETE WHERE {{ ?s ?p edu:{id} }}")
