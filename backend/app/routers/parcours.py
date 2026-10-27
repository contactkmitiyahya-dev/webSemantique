"""Routeur /api/parcours (Imem).

Contraintes : au moins un module (parcoursComprend, restriction someValuesFrom Module) ;
animateurs = individus de la classe Formateur. Les modules de la fiche sont ordonnés par
nombre de prérequis (aPourPrerequis+) : un module sans prérequis vient en premier.
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.imem_commun import (entier, est_sous_classe, exiger, id_utilise, individus_de, libelle, liste,
                             sous_classes, supprimer_individu, uri, verifier_id, verifier_refs)
from app.sparql_client import select, update
from app.utils import esc, lit_str, make_id, pagination

router = APIRouter(prefix="/api/parcours", tags=["Parcours (Imem)"])

RELATIONS = {
    "modules": ("parcoursComprend", "estEtapeDuParcours", "Module"),
    "animateurs": ("estAnimePar", "animeParcours", "Formateur"),
}
SUIVEURS = "^edu:suitParcours|edu:estSuiviPar"


class ParcoursIn(BaseModel):
    id: str | None = Field(None, description="Facultatif : généré depuis le libellé (Parcours_…)")
    label: str = Field(..., min_length=2, max_length=200)
    type: str = Field("Parcours", description="Classe : ParcoursFrontend, ParcoursAccelere…")
    modules: list[str] = []
    animateurs: list[str] = []

    model_config = {"json_schema_extra": {"example": {
        "label": "Parcours React express", "type": "ParcoursAccelere",
        "modules": ["Module_JavaScript", "Module_React"], "animateurs": ["Mme_Jebali"]}}}


@router.get("", summary="Liste des parcours (recherche, type, module, animateur)")
def lister(q: str | None = None,
           type: str | None = Query(None, description="Classe, ex. ParcoursAccelere"),
           module: str | None = None,
           animateur: str | None = None,
           page: int = 1, taille: int = 20):
    limite, decalage = pagination(page, taille)
    m = ["?p a/rdfs:subClassOf* edu:Parcours .", libelle("p")]
    if type:
        m.append(f"?p a/rdfs:subClassOf* {uri(type, 'type')} .")
    if module:
        m.append(f"?p edu:parcoursComprend|^edu:estEtapeDuParcours {uri(module, 'module')} .")
    if animateur:
        m.append(f"?p edu:estAnimePar|^edu:animeParcours {uri(animateur, 'animateur')} .")
    if q:
        m.append(f'FILTER(CONTAINS(LCASE(STR(?p_label)), LCASE("{esc(q)}")))')
    motif = "\n  ".join(m)

    total = select(f"SELECT (COUNT(DISTINCT ?p) AS ?total) WHERE {{\n  {motif}\n}}")[0]["total"]
    requete = f"""SELECT ?p (SAMPLE(?p_label) AS ?label) (SAMPLE(?t) AS ?type)
       (COUNT(DISTINCT ?m) AS ?nbModules) (COUNT(DISTINCT ?a) AS ?nbApprenants)
       (GROUP_CONCAT(DISTINCT ?anim_label; separator=", ") AS ?animateurs) WHERE {{
  {motif}
  OPTIONAL {{ ?p a ?t . ?t rdfs:subClassOf* edu:Parcours }}
  OPTIONAL {{ ?p edu:parcoursComprend|^edu:estEtapeDuParcours ?m }}
  OPTIONAL {{ ?p {SUIVEURS} ?a }}
  OPTIONAL {{ ?p edu:estAnimePar|^edu:animeParcours ?anim . {libelle('anim')} }}
}} GROUP BY ?p ORDER BY LCASE(?label) LIMIT {limite} OFFSET {decalage}"""
    donnees = [{"id": l["p"], "label": l["label"], "type": l.get("type"),
                "nbModules": entier(l["nbModules"]), "nbApprenants": entier(l["nbApprenants"]),
                "animateurs": l.get("animateurs") or ""} for l in select(requete)]
    return liste(total, donnees, sparql=requete)


@router.get("/options", summary="Valeurs possibles pour le formulaire (types, modules, formateurs)")
def options():
    return {"types": sous_classes("Parcours"), "modules": individus_de("Module"),
            "animateurs": individus_de("Formateur")}


def _detail(id_: str) -> dict:
    u = uri(id_)
    lab = select(f"SELECT (SAMPLE(?p_label) AS ?label) WHERE {{ BIND({u} AS ?p) {libelle('p')} }}")
    fiche = {"id": id_, "label": lab[0].get("label") if lab else id_}
    fiche["types"] = [l["t"] for l in select(
        f"SELECT DISTINCT ?t WHERE {{ {u} a ?t . ?t rdfs:subClassOf* edu:Parcours }}")]
    # modules ordonnés : nombre de prérequis (directs et indirects) croissant
    fiche["modules"] = [{"id": l["m"], "label": l["label"], "nbPrerequis": entier(l["prof"])}
                        for l in select(f"""
SELECT ?m (SAMPLE(?m_label) AS ?label) (COUNT(DISTINCT ?pre) AS ?prof) WHERE {{
  {u} edu:parcoursComprend|^edu:estEtapeDuParcours ?m .
  OPTIONAL {{ ?m edu:aPourPrerequis+ ?pre }}
  {libelle('m')}
}} GROUP BY ?m ORDER BY ?prof LCASE(?label)""")]
    for nom, chemin in (("animateurs", "edu:estAnimePar|^edu:animeParcours"), ("apprenants", SUIVEURS)):
        fiche[nom] = [{"id": l["x"], "label": l["label"]} for l in select(f"""
SELECT ?x (SAMPLE(?x_label) AS ?label) WHERE {{ {u} {chemin} ?x . {libelle('x')} }}
GROUP BY ?x ORDER BY LCASE(?label)""")]
    return fiche


@router.get("/{id}", summary="Fiche d'un parcours (modules ordonnés, animateurs, apprenants)")
def detail(id: str):
    exiger(id, "Parcours", "Parcours")
    return _detail(id)


def _valider(p: ParcoursIn) -> None:
    verifier_id(p.type, "type")
    if not est_sous_classe(p.type, "Parcours"):
        raise HTTPException(400, f"type « {p.type} » n'est pas une sous-classe de Parcours")
    if not p.modules:
        raise HTTPException(400, "Un parcours doit comprendre au moins un module")
    for nom, (_, _, classe) in RELATIONS.items():
        verifier_refs(list(dict.fromkeys(getattr(p, nom))), classe, nom)


def _triplets(id_: str, p: ParcoursIn) -> str:
    u = uri(id_)
    t = [f"{u} a owl:NamedIndividual , {uri(p.type)}", f"rdfs:label {lit_str(p.label, 'fr')}"]
    for nom, (prop, _, _) in RELATIONS.items():
        ids = list(dict.fromkeys(getattr(p, nom)))
        if ids:
            t.append(f"edu:{prop} " + " , ".join(uri(i) for i in ids))
    return " ;\n    ".join(t) + " ."


@router.post("", status_code=201, summary="Créer un parcours (au moins un module)")
def creer(p: ParcoursIn):
    id_ = verifier_id(p.id) if p.id else make_id(p.label, "Parcours")
    if not id_:
        raise HTTPException(400, "Impossible de générer un identifiant à partir du libellé")
    _valider(p)
    if id_utilise(id_):
        raise HTTPException(409, f"L'identifiant {id_} existe déjà")
    update(f"INSERT DATA {{\n  {_triplets(id_, p)}\n}}")
    return _detail(id_)


@router.put("/{id}", summary="Modifier un parcours (apprenants qui le suivent conservés)")
def modifier(id: str, p: ParcoursIn):
    exiger(id, "Parcours", "Parcours")
    _valider(p)
    u = uri(id)
    sortantes = " ".join(f"edu:{r[0]}" for r in RELATIONS.values())
    entrantes = " ".join(f"edu:{r[1]}" for r in RELATIONS.values())
    update(f"""DELETE {{ {u} ?p ?o }} WHERE {{ {u} ?p ?o . VALUES ?p {{ {sortantes} rdfs:label edu:intitule }} }} ;
DELETE {{ {u} a ?t }} WHERE {{ {u} a ?t . ?t rdfs:subClassOf* edu:Parcours }} ;
DELETE {{ ?s ?p {u} }} WHERE {{ ?s ?p {u} . VALUES ?p {{ {entrantes} }} }} ;
INSERT DATA {{
  {_triplets(id, p)}
}}""")
    return _detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer un parcours (liens entrants compris)")
def supprimer(id: str):
    exiger(id, "Parcours", "Parcours")
    update(supprimer_individu(id))
    return Response(status_code=204)
