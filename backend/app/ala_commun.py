"""Fonctions communes aux 4 routeurs d'Ala : formateurs, responsables, organismes, domaines.

Toute la construction SPARQL passe par ici :
  - les identifiants sont validés (valid_id) avant d'être placés dans une URI edu:X ;
  - les chaînes sont échappées (esc) et les nombres convertis en int avant insertion ;
  - les relations sont lues dans les deux sens (chemin « p|^inverse »).
"""
import re

from fastapi import HTTPException
from pydantic import BaseModel

from app.sparql_client import ask, select, update
from app.utils import esc, valid_id

# Clé simple de l'API -> prédicat RDF
PROPRIETES = {
    "nom": "edu:nom",
    "prenom": "edu:prenom",
    "email": "edu:email",
    "telephone": "edu:telephone",
    "specialite": "edu:specialiteFormateur",
    "experience": "edu:anneesExperience",
    "label": "rdfs:label",
    "intitule": "edu:intitule",
}
# Prédicat tel que renvoyé par sparql_client (nom court) -> clé simple
_CLES = {"nom": "nom", "prenom": "prenom", "email": "email", "telephone": "telephone",
         "specialiteFormateur": "specialite", "anneesExperience": "experience",
         "rdfs:label": "label", "intitule": "intitule"}
ENTIERS = {"experience"}

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class Page(BaseModel):
    """Réponse d'une liste (contrat d'API) – TEMPORAIRE (Ala) : à remplacer par le modèle de Zahra."""
    total: int
    donnees: list[dict]


# ----------------------------------------------------------------------------- validation

def verifier_id(id_: str) -> str:
    """400 si l'identifiant contient autre chose que lettres, chiffres, _."""
    if not valid_id(id_):
        raise HTTPException(400, f"Identifiant invalide : « {id_} » (lettres, chiffres et _ uniquement).")
    return id_


def verifier_type(type_: str, autorises: list[str]) -> str:
    if type_ not in autorises:
        raise HTTPException(400, f"Type invalide : « {type_} ». Types acceptés : {', '.join(autorises)}.")
    return type_


def verifier_email(email: str | None) -> None:
    if email and not EMAIL.fullmatch(email):
        raise HTTPException(400, f"Email invalide : « {email} ».")


def verifier_texte(valeur: str | None, libelle: str) -> None:
    """400 si un champ obligatoire est vide."""
    if valeur is None or not str(valeur).strip():
        raise HTTPException(400, f"Le champ « {libelle} » est obligatoire.")


# ----------------------------------------------------------------------------- lecture

def existe(id_: str) -> bool:
    """L'identifiant est-il déjà utilisé (comme sujet OU comme objet) ? -> 409 à la création."""
    return ask(f"ASK {{ {{ edu:{id_} ?p ?o }} UNION {{ ?s ?p edu:{id_} }} }}")


def est_de_classe(id_: str, classe: str) -> bool:
    """Sous-classes comprises (pas de raisonnement dans Fuseki)."""
    return ask(f"ASK {{ edu:{id_} a/rdfs:subClassOf* edu:{classe} }}")


def exiger(id_: str, classe: str, libelle: str) -> None:
    """400 si id invalide, 404 si l'individu n'est pas de la classe attendue."""
    verifier_id(id_)
    if not est_de_classe(id_, classe):
        raise HTTPException(404, f"{libelle} « {id_} » introuvable.")


def verifier_cibles(ids: list[str], classe: str, libelle: str) -> None:
    """400 si un individu à relier n'existe pas (ex. un cours inconnu)."""
    for i in ids:
        verifier_id(i)
        if not est_de_classe(i, classe):
            raise HTTPException(400, f"{libelle} « {i} » introuvable.")


def motif_type(var: str, var_type: str, racine: str) -> str:
    """Motif SPARQL qui lie ?var_type à la classe la PLUS SPÉCIFIQUE de ?var sous racine
    (exclut owl:NamedIndividual et les super-classes)."""
    return (f"?{var} a ?{var_type} . ?{var_type} rdfs:subClassOf* edu:{racine} . "
            f"FILTER NOT EXISTS {{ ?{var} a ?autre_{var_type} . "
            f"?autre_{var_type} rdfs:subClassOf+ ?{var_type} . FILTER(?autre_{var_type} != ?{var_type}) }}")


def type_de(id_: str, racine: str) -> str | None:
    lignes = select(f"SELECT ?t WHERE {{ VALUES ?x {{ edu:{id_} }} {motif_type('x', 't', racine)} }}")
    return lignes[0]["t"] if lignes else None


def proprietes(id_: str) -> dict:
    """Propriétés littérales avec des clés simples (nom, prenom, email, ..., label, intitule)."""
    lignes = select(f"SELECT ?p ?v WHERE {{ edu:{id_} ?p ?v . FILTER(isLiteral(?v)) }}")
    resultat = {}
    for ligne in lignes:
        cle = _CLES.get(ligne["p"])
        if cle and cle not in resultat:
            resultat[cle] = int(ligne["v"]) if cle in ENTIERS else ligne["v"]
    return resultat


def relations(id_: str, liens: dict[str, tuple[str, str]]) -> dict[str, list[dict]]:
    """liens = {"cours": ("edu:enseigne", "edu:enseignePar"), ...} : (propriété portée par MON
    individu, propriété inverse portée par l'autre). Lecture dans les deux sens avec
    « ?id (inverse|^propriete) edu:X ».
    Renvoie {"cours": [{"id", "label", "modifiable"}], ...} ; modifiable = True si le lien est
    écrit par moi (edu:X propriete ?id), False s'il n'est écrit que dans l'autre sens
    (triplet d'un autre membre : lecture seule)."""
    blocs = " UNION ".join(
        f'{{ ?id ({inverse}|^{propriete}) edu:{id_} . BIND("{nom}" AS ?rel) '
        f'BIND(EXISTS {{ edu:{id_} {propriete} ?id }} AS ?modif) }}'
        for nom, (propriete, inverse) in liens.items())
    lignes = select(f"""SELECT ?rel ?id ?modif (SAMPLE(?lib) AS ?label) WHERE {{
  {blocs}
  OPTIONAL {{ ?id edu:intitule ?intitule }}
  OPTIONAL {{ ?id rdfs:label ?libelle }}
  OPTIONAL {{ ?id edu:nom ?nom }}
  BIND(COALESCE(?intitule, ?libelle, ?nom, STRAFTER(STR(?id), "#")) AS ?lib)
}} GROUP BY ?rel ?id ?modif ORDER BY ?rel ?label""")
    resultat = {nom: [] for nom in liens}
    for ligne in lignes:
        resultat[ligne["rel"]].append({"id": ligne["id"], "label": ligne["label"],
                                       "modifiable": ligne["modif"] == "true"})
    return resultat


def compter(where: str, var: str) -> int:
    return int(select(f"SELECT (COUNT(DISTINCT ?{var}) AS ?n) WHERE {{ {where} }}")[0]["n"])


def filtre_contient(expression: str, texte: str) -> str:
    """FILTER de recherche insensible à la casse ; le texte est échappé (anti-injection)."""
    return f'FILTER( CONTAINS(LCASE(STR({expression})), LCASE("{esc(texte)}")) )'


# ----------------------------------------------------------------------------- affichage

def prenom_affiche(prenom: str | None) -> str | None:
    """Ignore un titre stocké comme prénom (ex. « Dr. » pour Dr_Benali)."""
    if not prenom or prenom.strip().endswith("."):
        return None
    return prenom


def nom_complet(prenom: str | None, nom: str | None) -> str:
    p = prenom_affiche(prenom)
    return f"{p} {nom}" if p else (nom or "")


# ----------------------------------------------------------------------------- écriture

def litteral(cle: str, valeur) -> str:
    """Valeur Python -> littéral SPARQL sûr (entier converti, chaîne échappée)."""
    if cle in ENTIERS:
        return str(int(valeur))
    if cle == "label":
        return f'"{esc(valeur)}"@fr'
    return f'"{esc(valeur)}"^^xsd:string'


def creer(id_: str, classe: str, valeurs: dict, liens: list[tuple[str, list[str]]]) -> None:
    """INSERT DATA : type feuille + owl:NamedIndividual, propriétés, relations portées par l'individu.
    liens = [("edu:enseigne", ["Cours_React", ...]), ...]"""
    triplets = [f"edu:{id_} a owl:NamedIndividual, edu:{classe}"]
    for cle, valeur in valeurs.items():
        if valeur not in (None, ""):
            triplets.append(f"edu:{id_} {PROPRIETES[cle]} {litteral(cle, valeur)}")
    for propriete, cibles in liens:
        for cible in cibles:
            triplets.append(f"edu:{id_} {propriete} edu:{cible}")
    update("INSERT DATA {\n  " + " .\n  ".join(triplets) + " .\n}")


def modifier(id_: str, valeurs: dict) -> None:
    """Remplace chaque propriété : DELETE de l'ancienne valeur puis INSERT de la nouvelle,
    dans UNE requête (une transaction) -> jamais deux edu:nom. None ou "" = suppression."""
    operations = []
    for cle, valeur in valeurs.items():
        predicat = PROPRIETES[cle]
        operations.append(f"DELETE WHERE {{ edu:{id_} {predicat} ?ancien }}")
        if valeur not in (None, ""):
            operations.append(f"INSERT DATA {{ edu:{id_} {predicat} {litteral(cle, valeur)} }}")
    if operations:
        update(" ;\n".join(operations))


def changer_type(id_: str, classe: str) -> None:
    """Remplace le type (garde owl:NamedIndividual)."""
    update(f"DELETE {{ edu:{id_} a ?t }} WHERE {{ edu:{id_} a ?t . FILTER(?t != owl:NamedIndividual) }} ;\n"
           f"INSERT DATA {{ edu:{id_} a edu:{classe} }}")


def remplacer_relation(id_: str, propriete: str, cibles: list[str]) -> None:
    """Remplace les liens ÉCRITS PAR MOI (edu:X propriete ?y) par la nouvelle liste.
    Ne touche jamais un triplet dont le sujet est un individu d'un autre membre
    (ex. edu:Cours_X edu:enseignePar edu:X reste en place : lien en lecture seule)."""
    operations = [f"DELETE WHERE {{ edu:{id_} {propriete} ?x }}"]
    if cibles:
        objets = ", ".join(f"edu:{c}" for c in cibles)
        operations.append(f"INSERT DATA {{ edu:{id_} {propriete} {objets} }}")
    update(" ;\n".join(operations))


def supprimer(id_: str) -> None:
    """Supprime les triplets sortants PUIS entrants (aucun lien orphelin)."""
    update(f"DELETE WHERE {{ edu:{id_} ?p ?o }} ;\nDELETE WHERE {{ ?s ?p edu:{id_} }}")
