"""Routeur /api/formateurs (Ala) : CRUD des formateurs et de leurs sous-classes."""
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app import ala_commun as c
from app.sparql_client import select
from app.utils import make_id, pagination

router = APIRouter(prefix="/api/formateurs", tags=["Formateurs (Ala)"])

TYPES = ["FormateurPermanent", "FormateurSenior", "FormateurJunior",
         "FormateurVacataire", "FormateurExpertIndustrie", "FormateurInvite"]
EXPERIENCE_MAX_JUNIOR = 3  # restriction OWL : FormateurJunior => anneesExperience <= 3

# Relation -> (propriété portée par le formateur, propriété inverse, classe cible).
# Lecture dans les deux sens ; écriture uniquement avec la propriété portée par le formateur.
RELATIONS = {
    "cours": ("edu:enseigne", "edu:enseignePar", "Cours"),
    "apprenants": ("edu:encadre", "edu:estEncadrePar", "Apprenant"),
    "parcours": ("edu:animeParcours", "edu:estAnimePar", "Parcours"),
}
LIENS = {rel: (prop, inverse) for rel, (prop, inverse, _) in RELATIONS.items()}
CHAMPS = ["nom", "prenom", "email", "telephone", "specialite", "experience", "label"]
TRIS = {"nom": "?nomF", "type": "?type", "experience": "?experienceF", "nb_cours": "?nbCours"}


class FormateurIn(BaseModel):
    """Création : id facultatif (généré depuis prénom + nom)."""
    id: str | None = None
    type: str
    nom: str
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    specialite: str | None = None
    experience: int | None = None
    label: str | None = None
    cours: list[str] = []
    apprenants: list[str] = []
    parcours: list[str] = []


class FormateurMaj(BaseModel):
    """Modification : seuls les champs envoyés sont modifiés ; null ou "" efface la valeur."""
    type: str | None = None
    nom: str | None = None
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    specialite: str | None = None
    experience: int | None = None
    label: str | None = None
    cours: list[str] | None = None
    apprenants: list[str] | None = None
    parcours: list[str] | None = None


def valider(type_: str, nom, email, experience) -> None:
    """Contraintes métier (400) vérifiées sur l'état FINAL du formateur."""
    c.verifier_type(type_, TYPES)
    c.verifier_texte(nom, "nom")
    c.verifier_email(email)
    if experience is not None and experience < 0:
        raise HTTPException(400, "L'expérience doit être un entier positif ou nul.")
    if type_ == "FormateurJunior" and experience is not None and experience > EXPERIENCE_MAX_JUNIOR:
        raise HTTPException(400, f"Un FormateurJunior a au plus {EXPERIENCE_MAX_JUNIOR} ans d'expérience.")


def detail(id_: str) -> dict:
    """Propriétés (clés simples) + type le plus spécifique + relations {id, label}."""
    fiche = {"id": id_, "type": c.type_de(id_, "Formateur")}
    fiche.update(c.proprietes(id_))
    fiche["prenom"] = c.prenom_affiche(fiche.get("prenom"))
    fiche["nom_complet"] = c.nom_complet(fiche.get("prenom"), fiche.get("nom"))
    fiche.update(c.relations(id_, LIENS))
    return fiche


@router.get("", response_model=c.Page, summary="Liste paginée avec filtres")
def lister(q: str | None = Query(None, description="recherche dans prénom + nom"),
           type: str | None = Query(None, description="FormateurSenior, FormateurVacataire..."),
           specialite: str | None = None,
           experience_min: int | None = None,
           tri: str = Query("nom", description="nom, type, experience ou nb_cours"),
           ordre: str = Query("asc", description="asc ou desc"),
           page: int = 1, taille: int = 20):
    limite, decalage = pagination(page, taille)
    racine = c.verifier_type(type, TYPES) if type else "Formateur"
    if tri not in TRIS:
        raise HTTPException(400, f"Tri invalide : « {tri} » ({', '.join(TRIS)}).")

    # Motif commun à la liste et au comptage
    where = f"""?f a/rdfs:subClassOf* edu:{racine} ; edu:nom ?nom .
  OPTIONAL {{ ?f edu:prenom ?prenom }}
  OPTIONAL {{ ?f edu:specialiteFormateur ?specialite }}
  OPTIONAL {{ ?f edu:anneesExperience ?experience }}"""
    if specialite:
        where += "\n  " + c.filtre_contient("?specialite", specialite)
    if experience_min is not None:
        where += f"\n  FILTER(?experience >= {int(experience_min)})"
    if q:
        where += "\n  " + c.filtre_contient('CONCAT(COALESCE(?prenom, ""), " ", ?nom)', q)

    total = c.compter(where, "f")
    sens = "DESC" if ordre.lower() == "desc" else "ASC"
    lignes = select(f"""SELECT ?f (SAMPLE(?nom) AS ?nomF) (SAMPLE(?prenom) AS ?prenomF)
       (SAMPLE(?specialite) AS ?specialiteF) (SAMPLE(?experience) AS ?experienceF)
       (SAMPLE(?t) AS ?type) (COUNT(DISTINCT ?cours) AS ?nbCours) WHERE {{
  {where}
  {c.motif_type("f", "t", "Formateur")}
  OPTIONAL {{ ?cours (edu:enseignePar|^edu:enseigne) ?f }}
}} GROUP BY ?f ORDER BY {sens}({TRIS[tri]}) ?nomF LIMIT {limite} OFFSET {decalage}""")

    donnees = [{
        "id": l["f"],
        "nom": l.get("nomF"),
        "prenom": c.prenom_affiche(l.get("prenomF")),
        "nom_complet": c.nom_complet(l.get("prenomF"), l.get("nomF")),
        "type": l.get("type"),
        "specialite": l.get("specialiteF"),
        "experience": int(l["experienceF"]) if "experienceF" in l else None,
        "nb_cours": int(l["nbCours"]),
    } for l in lignes]
    return {"total": total, "donnees": donnees}


@router.get("/{id}", summary="Fiche : propriétés + cours, apprenants, parcours")
def lire(id: str):
    c.exiger(id, "Formateur", "Formateur")
    return detail(id)


@router.post("", status_code=201, summary="Créer un formateur")
def creer(f: FormateurIn):
    valider(f.type, f.nom, f.email, f.experience)
    id_ = f.id or make_id(f"{f.prenom or ''} {f.nom}")
    c.verifier_id(id_)
    if c.existe(id_):
        raise HTTPException(409, f"L'identifiant « {id_} » existe déjà.")
    for rel, (_, _, classe) in RELATIONS.items():
        c.verifier_cibles(getattr(f, rel), classe, classe)

    valeurs = {k: getattr(f, k) for k in CHAMPS}
    valeurs["label"] = f.label or c.nom_complet(f.prenom, f.nom)
    liens = [(prop, getattr(f, rel)) for rel, (prop, _, _) in RELATIONS.items()]
    c.creer(id_, f.type, valeurs, liens)
    return detail(id_)


@router.put("/{id}", summary="Modifier un formateur (champs envoyés uniquement)")
def modifier(id: str, f: FormateurMaj):
    c.exiger(id, "Formateur", "Formateur")
    envoye = f.model_dump(exclude_unset=True)

    # État final = état actuel + modifications, pour vérifier les contraintes (ex. Junior <= 3 ans)
    actuel = c.proprietes(id)
    type_final = envoye.get("type") or c.type_de(id, "Formateur")
    final = {**actuel, **{k: v for k, v in envoye.items() if k in CHAMPS}}
    valider(type_final, final.get("nom"), final.get("email"), final.get("experience"))
    for rel, (_, _, classe) in RELATIONS.items():
        if envoye.get(rel) is not None:
            c.verifier_cibles(envoye[rel], classe, classe)

    if "type" in envoye and envoye["type"]:
        c.changer_type(id, envoye["type"])
    c.modifier(id, {k: v for k, v in envoye.items() if k in CHAMPS})
    for rel, (prop, _, _) in RELATIONS.items():
        if envoye.get(rel) is not None:
            c.remplacer_relation(id, prop, envoye[rel])
    return detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer (triplets sortants et entrants)")
def supprimer(id: str):
    c.exiger(id, "Formateur", "Formateur")
    c.supprimer(id)
    return Response(status_code=204)
