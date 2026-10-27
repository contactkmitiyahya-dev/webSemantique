"""Routeur /api/organismes (Ala) : organismes de formation et certificateurs."""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app import ala_commun as c
from app.sparql_client import select
from app.utils import make_id, pagination

router = APIRouter(prefix="/api/organismes", tags=["Organismes (Ala)"])

# Création : classes feuilles uniquement
TYPES = ["Universite", "EcoleSuperieure", "MOOC", "AcademieEnLigne",
         "MinistereFormation", "EditeurTechnologique"]
# Filtre : on accepte aussi les classes intermédiaires (sous-classes comprises)
TYPES_FILTRE = TYPES + ["OrganismeDeFormation", "EtablissementAcademique", "PlateformeEnLigne",
                        "OrganismeCertificateur", "CertificateurPublic", "CertificateurPrive"]
# Relation -> (propriété portée par l'organisme, propriété inverse, classe cible)
RELATIONS = {
    "formations": ("edu:proposeFormation", "edu:estProposeePar", "Formation"),
    "certifications": ("edu:delivreCertification", "edu:delivreeParOrganisme", "Certification"),
}
LIENS = {rel: (prop, inverse) for rel, (prop, inverse, _) in RELATIONS.items()}


class OrganismeIn(BaseModel):
    id: str | None = None
    type: str
    label: str
    formations: list[str] = []
    certifications: list[str] = []


class OrganismeMaj(BaseModel):
    type: str | None = None
    label: str | None = None
    formations: list[str] | None = None
    certifications: list[str] | None = None


def detail(id_: str) -> dict:
    fiche = {"id": id_, "type": c.type_de(id_, "Organisme")}
    fiche.update(c.proprietes(id_))
    fiche.update(c.relations(id_, LIENS))
    return fiche


@router.get("", response_model=c.Page, summary="Liste des organismes (filtre type)")
def lister(q: str | None = Query(None, description="recherche dans le libellé"),
           type: str | None = Query(None, description=", ".join(TYPES_FILTRE)),
           page: int = 1, taille: int = 20):
    limite, decalage = pagination(page, taille)
    racine = c.verifier_type(type, TYPES_FILTRE) if type else "Organisme"
    where = f"?o a/rdfs:subClassOf* edu:{racine} ; rdfs:label ?label ."
    if q:
        where += "\n  " + c.filtre_contient("?label", q)

    total = c.compter(where, "o")
    lignes = select(f"""SELECT ?o (SAMPLE(?label) AS ?labelO) (SAMPLE(?t) AS ?type)
       (COUNT(DISTINCT ?f) AS ?nbFormations) (COUNT(DISTINCT ?cert) AS ?nbCertifications) WHERE {{
  {where}
  {c.motif_type("o", "t", "Organisme")}
  OPTIONAL {{ ?f (edu:estProposeePar|^edu:proposeFormation) ?o }}
  OPTIONAL {{ ?cert (edu:delivreeParOrganisme|^edu:delivreCertification) ?o }}
}} GROUP BY ?o ORDER BY ?labelO LIMIT {limite} OFFSET {decalage}""")

    donnees = [{
        "id": l["o"],
        "label": l.get("labelO"),
        "type": l.get("type"),
        "nb_formations": int(l["nbFormations"]),
        "nb_certifications": int(l["nbCertifications"]),
    } for l in lignes]
    return {"total": total, "donnees": donnees}


@router.get("/{id}", summary="Fiche : formations proposées + certifications délivrées")
def lire(id: str):
    c.exiger(id, "Organisme", "Organisme")
    return detail(id)


@router.post("", status_code=201, summary="Créer un organisme")
def creer(o: OrganismeIn):
    c.verifier_type(o.type, TYPES)
    c.verifier_texte(o.label, "label")
    id_ = o.id or make_id(o.label)
    c.verifier_id(id_)
    if c.existe(id_):
        raise HTTPException(409, f"L'identifiant « {id_} » existe déjà.")
    for rel, (_, _, classe) in RELATIONS.items():
        c.verifier_cibles(getattr(o, rel), classe, classe)
    liens = [(prop, getattr(o, rel)) for rel, (prop, _, _) in RELATIONS.items()]
    c.creer(id_, o.type, {"label": o.label}, liens)
    return detail(id_)


@router.put("/{id}", summary="Modifier (champs envoyés uniquement)")
def modifier(id: str, o: OrganismeMaj):
    c.exiger(id, "Organisme", "Organisme")
    envoye = o.model_dump(exclude_unset=True)
    if "type" in envoye:
        c.verifier_type(envoye["type"], TYPES)
    if "label" in envoye:
        c.verifier_texte(envoye["label"], "label")
    for rel, (_, _, classe) in RELATIONS.items():
        if envoye.get(rel) is not None:
            c.verifier_cibles(envoye[rel], classe, classe)

    if envoye.get("type"):
        c.changer_type(id, envoye["type"])
    if "label" in envoye:
        c.modifier(id, {"label": envoye["label"]})
    for rel, (prop, _, _) in RELATIONS.items():
        if envoye.get(rel) is not None:
            c.remplacer_relation(id, prop, envoye[rel])
    return detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer (triplets sortants et entrants)")
def supprimer(id: str):
    c.exiger(id, "Organisme", "Organisme")
    c.supprimer(id)
    return Response(status_code=204)
