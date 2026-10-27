"""Routeur /api/domaines (Ala) : domaines de formation."""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app import ala_commun as c
from app.sparql_client import select
from app.utils import make_id, pagination

router = APIRouter(prefix="/api/domaines", tags=["Domaines (Ala)"])

# Sous-classes de Domaine (sauf les deux racines DomaineInformatique / DomaineDesign)
TYPES = ["DeveloppementWeb", "DeveloppementFrontend", "DeveloppementBackend", "DeveloppementFullStack",
         "DonneesEtIA", "AnalyseDeDonnees", "ApprentissageAutomatique",
         "DesignInterface", "UXDesign", "UIDesign"]
TYPES_FILTRE = TYPES + ["DomaineInformatique", "DomaineDesign"]
LIENS = {"formations": ("edu:regroupeFormation", "edu:appartientAuDomaine")}


class DomaineIn(BaseModel):
    id: str | None = None
    type: str
    intitule: str
    formations: list[str] = []


class DomaineMaj(BaseModel):
    type: str | None = None
    intitule: str | None = None
    formations: list[str] | None = None


def detail(id_: str) -> dict:
    fiche = {"id": id_, "type": c.type_de(id_, "Domaine")}
    fiche.update(c.proprietes(id_))
    fiche.update(c.relations(id_, LIENS))
    return fiche


@router.get("", response_model=c.Page, summary="Liste des domaines (filtre type)")
def lister(q: str | None = Query(None, description="recherche dans l'intitulé"),
           type: str | None = Query(None, description=", ".join(TYPES_FILTRE)),
           page: int = 1, taille: int = 20):
    limite, decalage = pagination(page, taille)
    racine = c.verifier_type(type, TYPES_FILTRE) if type else "Domaine"
    where = f"?d a/rdfs:subClassOf* edu:{racine} ; edu:intitule ?intitule ."
    if q:
        where += "\n  " + c.filtre_contient("?intitule", q)

    total = c.compter(where, "d")
    lignes = select(f"""SELECT ?d (SAMPLE(?intitule) AS ?intituleD) (SAMPLE(?t) AS ?type)
       (COUNT(DISTINCT ?f) AS ?nbFormations) WHERE {{
  {where}
  {c.motif_type("d", "t", "Domaine")}
  OPTIONAL {{ ?f (edu:appartientAuDomaine|^edu:regroupeFormation) ?d }}
}} GROUP BY ?d ORDER BY ?intituleD LIMIT {limite} OFFSET {decalage}""")

    donnees = [{
        "id": l["d"],
        "intitule": l.get("intituleD"),
        "type": l.get("type"),
        "nb_formations": int(l["nbFormations"]),
    } for l in lignes]
    return {"total": total, "donnees": donnees}


@router.get("/{id}", summary="Fiche : intitulé + formations du domaine")
def lire(id: str):
    c.exiger(id, "Domaine", "Domaine")
    return detail(id)


@router.post("", status_code=201, summary="Créer un domaine")
def creer(d: DomaineIn):
    c.verifier_type(d.type, TYPES)
    c.verifier_texte(d.intitule, "intitule")
    id_ = d.id or make_id(f"Domaine {d.intitule}")
    c.verifier_id(id_)
    if c.existe(id_):
        raise HTTPException(409, f"L'identifiant « {id_} » existe déjà.")
    c.verifier_cibles(d.formations, "Formation", "Formation")
    # L'intitulé sert aussi de rdfs:label
    c.creer(id_, d.type, {"intitule": d.intitule, "label": d.intitule},
            [("edu:regroupeFormation", d.formations)])
    return detail(id_)


@router.put("/{id}", summary="Modifier (champs envoyés uniquement)")
def modifier(id: str, d: DomaineMaj):
    c.exiger(id, "Domaine", "Domaine")
    envoye = d.model_dump(exclude_unset=True)
    if "type" in envoye:
        c.verifier_type(envoye["type"], TYPES)
    if "intitule" in envoye:
        c.verifier_texte(envoye["intitule"], "intitule")
    if envoye.get("formations") is not None:
        c.verifier_cibles(envoye["formations"], "Formation", "Formation")

    if envoye.get("type"):
        c.changer_type(id, envoye["type"])
    if "intitule" in envoye:
        c.modifier(id, {"intitule": envoye["intitule"], "label": envoye["intitule"]})
    if envoye.get("formations") is not None:
        c.remplacer_relation(id, "edu:regroupeFormation", envoye["formations"])
    return detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer (triplets sortants et entrants)")
def supprimer(id: str):
    c.exiger(id, "Domaine", "Domaine")
    c.supprimer(id)
    return Response(status_code=204)
