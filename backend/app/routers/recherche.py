"""Recherche globale /api/recherche?q= (intégration finale : Imem).

Cherche dans les libellés de tous les individus nommés et renvoie leur catégorie
(classe racine du domaine) pour que le front puisse ouvrir la bonne fiche.
"""
from fastapi import APIRouter, HTTPException

from app.imem_commun import libelle, liste
from app.sparql_client import select
from app.utils import esc, pagination

router = APIRouter(prefix="/api/recherche", tags=["Recherche globale (Imem)"])

CATEGORIES = ("Apprenant", "Certification", "Formateur", "ResponsableFormation", "ServiceScolarite",
              "Organisme", "Domaine", "Formation", "Parcours", "Module", "Cours", "RessourcePedagogique",
              "Competence", "Technologie", "Evaluation")


@router.get("", summary="Recherche dans tous les types (formations, modules, apprenants…)")
def rechercher(q: str, page: int = 1, taille: int = 30):
    q = q.strip()
    if len(q) < 2:
        raise HTTPException(400, "Saisir au moins 2 caractères")
    limite, decalage = pagination(page, taille)
    valeurs = " ".join(f"edu:{c}" for c in CATEGORIES)
    motif = f"""?x a owl:NamedIndividual .
  {libelle('x')}
  FILTER(CONTAINS(LCASE(STR(?x_label)), LCASE("{esc(q)}")))
  VALUES ?cat {{ {valeurs} }}
  ?x a/rdfs:subClassOf* ?cat ."""
    total = select(f"SELECT (COUNT(DISTINCT ?x) AS ?total) WHERE {{ {motif} }}")[0]["total"]
    lignes = select(f"""SELECT ?x (SAMPLE(?x_label) AS ?label) (SAMPLE(?cat) AS ?categorie) WHERE {{
  {motif}
}} GROUP BY ?x ORDER BY ?categorie LCASE(?label) LIMIT {limite} OFFSET {decalage}""")
    return liste(total, [{"id": l["x"], "label": l["label"], "categorie": l["categorie"]} for l in lignes])
