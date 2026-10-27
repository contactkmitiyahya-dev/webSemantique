"""Routeur /api/formations (Imem).

Contraintes contrôlées (issues de l'ontologie) :
- au moins un module (composeDe) et au moins un domaine (appartientAuDomaine) ;
- au plus une certification (meneA, maxCardinality 1) ;
- coût positif ou nul, date de fin après la date de début ;
- le nombre de places ne peut pas descendre sous le nombre d'inscrits.
"""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.imem_commun import (booleen, entier, est_sous_classe, exiger, id_utilise, individus_de, libelle,
                             liste, reel, sous_classes, supprimer_individu, uri, verifier_id, verifier_refs)
from app.sparql_client import select, update
from app.utils import esc, lit_bool, lit_date, lit_dec, lit_int, lit_str, make_id, pagination

router = APIRouter(prefix="/api/formations", tags=["Formations (Imem)"])

NIVEAUX = ("Débutant", "Intermédiaire", "Avancé")

# relation API -> (propriété, propriété inverse, classe cible)
RELATIONS = {
    "modules": ("composeDe", "faitPartieDeFormation", "Module"),
    "domaines": ("appartientAuDomaine", "regroupeFormation", "Domaine"),
    "organismes": ("estProposeePar", "proposeFormation", "Organisme"),
    "responsables": ("estAdministreePar", "administreFormation", "ResponsableFormation"),
    "certification": ("meneA", "estObtenueApres", "Certification"),
}
# inscrits : lecture seule ici (l'inscription relève de la tranche Apprenants)
INSCRITS = "^edu:estInscritA|edu:accueilleApprenant"

# propriété de données -> conversion de la chaîne renvoyée par select()
DATA_PROPS = {
    "intitule": str, "dureeHeures": entier, "niveauDifficulte": str, "creditsECTS": entier,
    "coutFormation": reel, "dateDebut": str, "dateFin": str, "nombrePlaces": entier, "estActif": booleen,
}

# paramètre « tri » de l'API -> expression SPARQL (sens donné par le paramètre « ordre »)
TRIS = {
    "intitule": "LCASE(?intitule)",
    "cout": "?cout",
    "duree": "?duree",
    "debut": "?debut",
    "places": "?places_restantes",
}


class FormationIn(BaseModel):
    id: str | None = Field(None, description="Facultatif : généré depuis l'intitulé (Formation_…)")
    intitule: str = Field(..., min_length=2, max_length=200)
    type: str = Field("Formation", description="Classe : FormationCourte, BootCamp, FormationMaster…")
    dureeHeures: int | None = Field(None, ge=1)
    niveauDifficulte: Literal["Débutant", "Intermédiaire", "Avancé"] | None = None
    creditsECTS: int | None = Field(None, ge=0)
    coutFormation: float | None = Field(None, ge=0)
    dateDebut: datetime | None = None
    dateFin: datetime | None = None
    nombrePlaces: int | None = Field(None, ge=0)
    estActif: bool = True
    modules: list[str] = []
    domaines: list[str] = []
    organismes: list[str] = []
    responsables: list[str] = []
    certification: str | None = None

    model_config = {"json_schema_extra": {"example": {
        "intitule": "Atelier Vue.js", "type": "AtelierIntensif", "dureeHeures": 30,
        "niveauDifficulte": "Intermédiaire", "creditsECTS": 3, "coutFormation": 250,
        "dateDebut": "2027-03-01T00:00:00", "dateFin": "2027-03-26T00:00:00", "nombrePlaces": 20,
        "estActif": True, "modules": ["Module_JavaScript"], "domaines": ["Domaine_Frontend"],
        "organismes": ["MOOC_WebDev"], "responsables": ["Mme_Salhi"], "certification": None}}}


# ----------------------------------------------------------------------------- lecture

def _motif_liste(q, type_, cout_min, cout_max, duree_max, niveau, domaine, module, actif, a_venir) -> str:
    """Corps WHERE commun à la liste et au comptage ; chaque filtre ajoute une ligne SPARQL."""
    m = ["?f a/rdfs:subClassOf* edu:Formation .", libelle("f")]
    m += ["OPTIONAL { ?f edu:coutFormation ?c }", "OPTIONAL { ?f edu:dureeHeures ?d }",
          "OPTIONAL { ?f edu:niveauDifficulte ?n }", "OPTIONAL { ?f edu:estActif ?act }",
          "OPTIONAL { ?f edu:dateDebut ?deb }"]
    if type_:
        m.append(f"?f a/rdfs:subClassOf* {uri(type_, 'type')} .")
    if q:
        m.append(f'FILTER(CONTAINS(LCASE(STR(?f_label)), LCASE("{esc(q)}")))')
    if cout_min is not None:
        m.append(f"FILTER(BOUND(?c) && ?c >= {float(cout_min)})")
    if cout_max is not None:
        m.append(f"FILTER(BOUND(?c) && ?c <= {float(cout_max)})")
    if duree_max is not None:
        m.append(f"FILTER(BOUND(?d) && ?d <= {int(duree_max)})")
    if niveau:
        if niveau not in NIVEAUX:
            raise HTTPException(400, f"niveau doit valoir {', '.join(NIVEAUX)}")
        m.append(f'FILTER(STR(?n) = "{niveau}")')
    if domaine:
        m.append(f"?f edu:appartientAuDomaine|^edu:regroupeFormation {uri(domaine, 'domaine')} .")
    if module:
        m.append(f"?f edu:composeDe|^edu:faitPartieDeFormation {uri(module, 'module')} .")
    if actif is not None:
        m.append(f"FILTER(COALESCE(?act, true) = {'true' if actif else 'false'})")
    if a_venir:
        m.append("FILTER(BOUND(?deb) && ?deb > NOW())")
    return "\n  ".join(m)


@router.get("", summary="Catalogue des formations (filtres, recherche, tri, pagination)")
def lister(q: str | None = None,
           type: str | None = Query(None, description="Classe, ex. BootCamp"),
           cout_min: float | None = Query(None, ge=0),
           cout_max: float | None = Query(None, ge=0),
           duree_max: int | None = Query(None, ge=1),
           niveau: str | None = Query(None, description="Débutant | Intermédiaire | Avancé"),
           domaine: str | None = None,
           module: str | None = None,
           actif: bool | None = None,
           a_venir: bool = Query(False, description="seulement les formations qui n'ont pas commencé"),
           tri: str = Query("intitule", description="intitule | cout | duree | debut | places"),
           ordre: str = Query("asc", description="asc | desc"),
           page: int = 1, taille: int = 20):
    if tri not in TRIS:
        raise HTTPException(400, f"tri doit valoir {', '.join(TRIS)}")
    if ordre not in ("asc", "desc"):
        raise HTTPException(400, "ordre doit valoir asc ou desc")
    tri_sparql = f"DESC({TRIS[tri]})" if ordre == "desc" else TRIS[tri]
    limite, decalage = pagination(page, taille)
    motif = _motif_liste(q, type, cout_min, cout_max, duree_max, niveau, domaine, module, actif, a_venir)

    total = select(f"SELECT (COUNT(DISTINCT ?f) AS ?total) WHERE {{\n  {motif}\n}}")[0]["total"]
    requete = f"""SELECT ?f ?intitule ?type ?cout ?duree ?niveau ?actif ?debut ?fin ?places ?inscrits ?places_restantes WHERE {{
 {{ SELECT ?f (SAMPLE(?f_label) AS ?intitule) (SAMPLE(?t) AS ?type) (SAMPLE(?c) AS ?cout)
          (SAMPLE(?d) AS ?duree) (SAMPLE(?n) AS ?niveau) (SAMPLE(?act) AS ?actif)
          (SAMPLE(?deb) AS ?debut) (SAMPLE(?fi) AS ?fin) (SAMPLE(?pl) AS ?places)
          (COUNT(DISTINCT ?a) AS ?inscrits)
   WHERE {{
  {motif}
  OPTIONAL {{ ?f a ?t . ?t rdfs:subClassOf* edu:Formation }}
  OPTIONAL {{ ?f edu:dateFin ?fi }}
  OPTIONAL {{ ?f edu:nombrePlaces ?pl }}
  OPTIONAL {{ ?f {INSCRITS} ?a }}
   }} GROUP BY ?f }}
 BIND(?places - ?inscrits AS ?places_restantes)
}} ORDER BY {tri_sparql} LCASE(?intitule) LIMIT {limite} OFFSET {decalage}"""
    donnees = [{
        "id": l["f"], "intitule": l["intitule"], "type": l.get("type"),
        "cout": reel(l.get("cout")), "duree": entier(l.get("duree")), "niveau": l.get("niveau"),
        "actif": booleen(l.get("actif", "true")), "dateDebut": l.get("debut"), "dateFin": l.get("fin"),
        "places": entier(l.get("places")), "inscrits": entier(l["inscrits"]),
        "places_restantes": entier(l.get("places_restantes")),
    } for l in select(requete)]
    return liste(total, donnees, sparql=requete)


@router.get("/options", summary="Valeurs possibles pour le formulaire (types, modules, domaines…)")
def options():
    return {"types": sous_classes("Formation"), "niveaux": list(NIVEAUX),
            **{nom: individus_de(classe) for nom, (_, _, classe) in RELATIONS.items()}}


def _detail(id_: str) -> dict:
    u = uri(id_)
    props = select(f"""
SELECT ?p ?o WHERE {{
  {u} ?p ?o .
  VALUES ?p {{ {' '.join('edu:' + p for p in DATA_PROPS)} rdfs:label }}
}}""")
    fiche = {"id": id_}
    for l in props:
        if l["p"] == "rdfs:label":
            fiche.setdefault("label", l["o"])
        else:
            fiche[l["p"]] = DATA_PROPS[l["p"]](l["o"])
    fiche.setdefault("intitule", fiche.get("label", id_))
    fiche["types"] = [l["t"] for l in select(
        f"SELECT DISTINCT ?t WHERE {{ {u} a ?t . ?t rdfs:subClassOf* edu:Formation }}")]

    branches = [f'{{ {u} edu:{p}|^edu:{inv} ?x BIND("{nom}" AS ?rel) }}'
                for nom, (p, inv, _) in RELATIONS.items()]
    branches.append(f'{{ {u} {INSCRITS} ?x BIND("inscrits" AS ?rel) }}')
    lignes = select(f"""
SELECT ?rel ?x (SAMPLE(?x_label) AS ?label) WHERE {{
  {' UNION '.join(branches)}
  {libelle('x')}
}} GROUP BY ?rel ?x ORDER BY ?rel LCASE(?label)""")
    for nom in [*RELATIONS, "inscrits"]:
        fiche[nom] = []
    for l in lignes:
        fiche[l["rel"]].append({"id": l["x"], "label": l["label"]})
    cert = fiche.pop("certification")
    fiche["certification"] = cert[0] if cert else None
    fiche["nombreInscrits"] = len(fiche["inscrits"])
    if fiche.get("nombrePlaces") is not None:
        fiche["placesRestantes"] = fiche["nombrePlaces"] - fiche["nombreInscrits"]
    return fiche


@router.get("/{id}", summary="Fiche d'une formation (propriétés, relations, places restantes)")
def detail(id: str):
    exiger(id, "Formation", "Formation")
    return _detail(id)


# ----------------------------------------------------------------------------- écriture

def _ids(valeur) -> list[str]:
    """Liste sans doublons (la certification est un identifiant seul)."""
    return [valeur] if isinstance(valeur, str) else list(dict.fromkeys(valeur or []))


def _valider(f: FormationIn) -> None:
    verifier_id(f.type, "type")
    if not est_sous_classe(f.type, "Formation"):
        raise HTTPException(400, f"type « {f.type} » n'est pas une sous-classe de Formation")
    if not f.modules:
        raise HTTPException(400, "Une formation doit être composée d'au moins un module")
    if not f.domaines:
        raise HTTPException(400, "Une formation doit appartenir à au moins un domaine")
    if f.dateDebut and f.dateFin and f.dateFin.replace(tzinfo=None) <= f.dateDebut.replace(tzinfo=None):
        raise HTTPException(400, "La date de fin doit être postérieure à la date de début")
    for nom, (_, _, classe) in RELATIONS.items():
        verifier_refs(_ids(getattr(f, nom)), classe, nom)


def _triplets(id_: str, f: FormationIn) -> str:
    u = uri(id_)
    t = [f"{u} a owl:NamedIndividual , {uri(f.type)}",
         f"rdfs:label {lit_str(f.intitule, 'fr')}",
         f"edu:intitule {lit_str(f.intitule)}",
         f"edu:estActif {lit_bool(f.estActif)}"]
    if f.dureeHeures is not None:
        t.append(f"edu:dureeHeures {lit_int(f.dureeHeures)}")
    if f.niveauDifficulte:
        t.append(f"edu:niveauDifficulte {lit_str(f.niveauDifficulte)}")
    if f.creditsECTS is not None:
        t.append(f"edu:creditsECTS {lit_int(f.creditsECTS)}")
    if f.coutFormation is not None:
        t.append(f"edu:coutFormation {lit_dec(f.coutFormation)}")
    if f.dateDebut:
        t.append(f"edu:dateDebut {lit_date(f.dateDebut)}")
    if f.dateFin:
        t.append(f"edu:dateFin {lit_date(f.dateFin)}")
    if f.nombrePlaces is not None:
        t.append(f"edu:nombrePlaces {lit_int(f.nombrePlaces)}")
    for nom, (p, _, _) in RELATIONS.items():
        ids = _ids(getattr(f, nom))
        if ids:
            t.append(f"edu:{p} " + " , ".join(uri(i) for i in ids))
        # le sens inverse n'est pas écrit : les lectures utilisent toujours p|^inverse
    return " ;\n    ".join(t) + " ."


@router.post("", status_code=201, summary="Créer une formation (au moins un module et un domaine)")
def creer(f: FormationIn):
    id_ = verifier_id(f.id) if f.id else make_id(f.intitule, "Formation")
    if not id_:
        raise HTTPException(400, "Impossible de générer un identifiant à partir de l'intitulé")
    _valider(f)
    if id_utilise(id_):
        raise HTTPException(409, f"L'identifiant {id_} existe déjà")
    update(f"INSERT DATA {{\n  {_triplets(id_, f)}\n}}")
    return _detail(id_)


@router.put("/{id}", summary="Modifier une formation (remplacement complet, inscriptions conservées)")
def modifier(id: str, f: FormationIn):
    exiger(id, "Formation", "Formation")
    _valider(f)
    u = uri(id)
    if f.nombrePlaces is not None:
        inscrits = entier(select(f"SELECT (COUNT(DISTINCT ?a) AS ?n) WHERE {{ {u} {INSCRITS} ?a }}")[0]["n"])
        if f.nombrePlaces < inscrits:
            raise HTTPException(409, f"Impossible : {inscrits} apprenants déjà inscrits pour {f.nombrePlaces} places")
    sortantes = " ".join(f"edu:{p}" for p in (*DATA_PROPS, *(r[0] for r in RELATIONS.values())))
    entrantes = " ".join(f"edu:{r[1]}" for r in RELATIONS.values())
    # une seule requête de mise à jour = une transaction Fuseki
    update(f"""DELETE {{ {u} ?p ?o }} WHERE {{ {u} ?p ?o . VALUES ?p {{ {sortantes} rdfs:label }} }} ;
DELETE {{ {u} a ?t }} WHERE {{ {u} a ?t . ?t rdfs:subClassOf* edu:Formation }} ;
DELETE {{ ?s ?p {u} }} WHERE {{ ?s ?p {u} . VALUES ?p {{ {entrantes} }} }} ;
INSERT DATA {{
  {_triplets(id, f)}
}}""")
    return _detail(id)


@router.delete("/{id}", status_code=204, summary="Supprimer une formation (liens entrants compris)")
def supprimer(id: str):
    exiger(id, "Formation", "Formation")
    update(supprimer_individu(id))
    return Response(status_code=204)
