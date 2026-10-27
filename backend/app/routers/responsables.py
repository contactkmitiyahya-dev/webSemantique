"""Routeur /api/responsables (Ala) : personnel administratif.

Deux catégories DISJOINTES dans l'ontologie :
  - ResponsableFormation : ResponsableDeFormation, ResponsablePedagogique (administrent des formations)
  - ServiceScolarite     : AgentScolarite, GestionnaireInscription (n'administrent rien :
    le domaine de edu:administreFormation est ResponsableFormation)
"""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app import ala_commun as c
from app.sparql_client import select
from app.utils import make_id, pagination

router = APIRouter(prefix="/api/responsables", tags=["Personnel (Ala)"])

CATEGORIES = {
    "ResponsableDeFormation": "ResponsableFormation",
    "ResponsablePedagogique": "ResponsableFormation",
    "AgentScolarite": "ServiceScolarite",
    "GestionnaireInscription": "ServiceScolarite",
}
TYPES = list(CATEGORIES)
LIENS = {"formations": ("edu:administreFormation", "edu:estAdministreePar")}
CHAMPS = ["nom", "prenom", "email", "telephone", "label"]


class PersonnelIn(BaseModel):
    id: str | None = None
    type: str
    nom: str
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    label: str | None = None
    formations: list[str] = []


class PersonnelMaj(BaseModel):
    type: str | None = None
    nom: str | None = None
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    label: str | None = None
    formations: list[str] | None = None


def valider(type_: str, nom, email, formations: list[str]) -> None:
    c.verifier_type(type_, TYPES)
    c.verifier_texte(nom, "nom")
    c.verifier_email(email)
    if formations and CATEGORIES[type_] == "ServiceScolarite":
        raise HTTPException(400, "Un agent de scolarité ne peut pas administrer de formation "
                                 "(ServiceScolarite et ResponsableFormation sont disjointes).")
    c.verifier_cibles(formations, "Formation", "Formation")


def detail(id_: str) -> dict:
    type_ = c.type_de(id_, "PersonnelAdministratif")
    fiche = {"id": id_, "type": type_, "categorie": CATEGORIES.get(type_)}
    fiche.update(c.proprietes(id_))
    fiche["prenom"] = c.prenom_affiche(fiche.get("prenom"))
    fiche["nom_complet"] = c.nom_complet(fiche.get("prenom"), fiche.get("nom"))
    fiche.update(c.relations(id_, LIENS))
    return fiche


def exiger(id_: str) -> None:
    """404 si l'individu n'est ni ResponsableFormation ni ServiceScolarite."""
    c.verifier_id(id_)
    if not (c.est_de_classe(id_, "ResponsableFormation") or c.est_de_classe(id_, "ServiceScolarite")):
        raise HTTPException(404, f"Membre du personnel « {id_} » introuvable.")


@router.get("", response_model=c.Page, summary="Liste du personnel (filtre type)")
def lister(q: str | None = Query(None, description="recherche dans prénom + nom"),
           type: str | None = Query(None, description=", ".join(TYPES)),
           page: int = 1, taille: int = 20):
    limite, decalage = pagination(page, taille)
    where = """VALUES ?categorie { edu:ResponsableFormation edu:ServiceScolarite }
  ?p a/rdfs:subClassOf* ?categorie ; edu:nom ?nom .
  OPTIONAL { ?p edu:prenom ?prenom }
  OPTIONAL { ?p edu:email ?email }"""
    if type:
        where += f"\n  ?p a/rdfs:subClassOf* edu:{c.verifier_type(type, TYPES)} ."
    if q:
        where += "\n  " + c.filtre_contient('CONCAT(COALESCE(?prenom, ""), " ", ?nom)', q)

    total = c.compter(where, "p")
    lignes = select(f"""SELECT ?p (SAMPLE(?nom) AS ?nomP) (SAMPLE(?prenom) AS ?prenomP)
       (SAMPLE(?email) AS ?emailP) (SAMPLE(?categorie) AS ?cat) (SAMPLE(?t) AS ?type)
       (COUNT(DISTINCT ?f) AS ?nbFormations) WHERE {{
  {where}
  {c.motif_type("p", "t", "PersonnelAdministratif")}
  OPTIONAL {{ ?f (edu:estAdministreePar|^edu:administreFormation) ?p }}
}} GROUP BY ?p ORDER BY ?cat ?nomP LIMIT {limite} OFFSET {decalage}""")

    donnees = [{
        "id": l["p"],
        "nom": l.get("nomP"),
        "prenom": c.prenom_affiche(l.get("prenomP")),
        "nom_complet": c.nom_complet(l.get("prenomP"), l.get("nomP")),
        "email": l.get("emailP"),
        "type": l.get("type"),
        "categorie": l.get("cat"),
        "nb_formations": int(l["nbFormations"]),
    } for l in lignes]
    return {"total": total, "donnees": donnees}


@router.get("/{id}", summary="Fiche : propriétés + formations administrées")
def lire(id: str):
    exiger(id)
    return detail(id)


@router.post("", status_code=201, summary="Créer un membre du personnel")
def creer(p: PersonnelIn):
    valider(p.type, p.nom, p.email, p.formations)
    id_ = p.id or make_id(f"{p.prenom or ''} {p.nom}")
    c.verifier_id(id_)
    if c.existe(id_):
        raise HTTPException(409, f"L'identifiant « {id_} » existe déjà.")
    valeurs = {k: getattr(p, k) for k in CHAMPS}
    valeurs["label"] = p.label or c.nom_complet(p.prenom, p.nom)
    c.creer(id_, p.type, valeurs, [("edu:administreFormation", p.formations)])
    return detail(id_)


@router.put("/{id}", summary="Modifier (champs envoyés uniquement)")
def modifier(id: str, p: PersonnelMaj):
    exiger(id)
    envoye = p.model_dump(exclude_unset=True)
    actuel = c.proprietes(id)
    type_final = envoye.get("type") or c.type_de(id, "PersonnelAdministratif")
    final = {**actuel, **{k: v for k, v in envoye.items() if k in CHAMPS}}
    # Formations finales = liens en lecture seule (écrits par Imem, non modifiables ici)
    #                     + liens écrits par moi (nouvelle liste si envoyée, sinon les actuels)
    actuelles = c.relations(id, LIENS)["formations"]
    lecture_seule = [x["id"] for x in actuelles if not x["modifiable"]]
    modifiables = (envoye["formations"] if envoye.get("formations") is not None
                   else [x["id"] for x in actuelles if x["modifiable"]])
    if lecture_seule and CATEGORIES[c.verifier_type(type_final, TYPES)] == "ServiceScolarite":
        raise HTTPException(400, "Impossible de passer en agent de scolarité : des formations "
                                 f"le désignent comme administrateur ({', '.join(lecture_seule)}), "
                                 "liens définis par une autre partie.")
    valider(type_final, final.get("nom"), final.get("email"), modifiables)

    if envoye.get("type"):
        c.changer_type(id, envoye["type"])
    c.modifier(id, {k: v for k, v in envoye.items() if k in CHAMPS})
    if envoye.get("formations") is not None:
        c.remplacer_relation(id, "edu:administreFormation", envoye["formations"])
    return detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer (triplets sortants et entrants)")
def supprimer(id: str):
    exiger(id)
    c.supprimer(id)
    return Response(status_code=204)
