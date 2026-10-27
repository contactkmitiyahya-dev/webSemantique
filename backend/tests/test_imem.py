"""Tests de la tranche d'Imem (formations, parcours, recherche globale, utilitaires, NLP), contre le vrai Fuseki.

Lancement depuis la racine (Fuseki démarré, données chargées) :
    backend\\venv\\Scripts\\python -m pytest backend/tests/test_imem.py -v

Un test par route + contraintes (création refusée sans module / sans domaine, filtres combinés,
409 sur id existant, suppression des liens entrants). Tous les individus créés contiennent
« Test_Imem » dans leur identifiant : ils sont supprimés à la fin du module, même si un test échoue.
"""
import csv
import sys
import warnings
from pathlib import Path

import pytest

# Rend le paquet « app » importable quel que soit le dossier de lancement
RACINE_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_BACKEND))

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated")
    from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.nlp.intents import classer_intentions, detecter_intention  # noqa: E402
from app.sparql_client import ask, select, update  # noqa: E402
from app.utils import esc, make_id, pagination, valid_id  # noqa: E402

EDU = "http://www.eduparcours.org/ontologie#"
MARQUE_TEST = "Test_Imem"
CSV_QUESTIONS = RACINE_BACKEND.parent / "docs" / "questions_types.csv"

FORMATION = {
    "intitule": "Test Imem Atelier Vue", "type": "AtelierIntensif", "dureeHeures": 30,
    "niveauDifficulte": "Intermédiaire", "creditsECTS": 3, "coutFormation": 250,
    "dateDebut": "2027-03-01T00:00:00", "dateFin": "2027-03-26T00:00:00", "nombrePlaces": 20,
    "estActif": True, "modules": ["Module_JavaScript"], "domaines": ["Domaine_Frontend"],
    "organismes": ["MOOC_WebDev"], "responsables": ["Mme_Salhi"], "certification": None,
}
PARCOURS = {"label": "Test Imem parcours", "type": "ParcoursAccelere",
            "modules": ["Module_JavaScript", "Module_React"], "animateurs": ["Mme_Jebali"]}


# =============================================================================== outils et fixtures

def nb_triplets() -> int:
    return int(select("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")[0]["n"])


def nettoyer_tests() -> None:
    """Supprime tout individu dont l'identifiant contient Test_Imem (sujet ou objet)."""
    lignes = select(f"""SELECT DISTINCT ?x WHERE {{
  {{ ?x ?p ?o }} UNION {{ ?s ?p ?x }}
  FILTER(isIRI(?x) && STRSTARTS(STR(?x), "{EDU}") && CONTAINS(STR(?x), "{MARQUE_TEST}")) }}""")
    for l in lignes:
        update(f"DELETE WHERE {{ edu:{l['x']} ?p ?o }} ;\nDELETE WHERE {{ ?s ?p edu:{l['x']} }}")


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module", autouse=True)
def donnees_propres():
    """Avant : supprime les restes d'une exécution précédente. Après : vérifie que le graphe
    est revenu à son état initial (aucun triplet de test oublié)."""
    nettoyer_tests()
    total_initial = nb_triplets()
    yield
    nettoyer_tests()
    assert nb_triplets() == total_initial


@pytest.fixture
def formation(client):
    r = client.post("/api/formations", json=FORMATION)
    assert r.status_code == 201, r.text
    yield r.json()["id"]
    client.delete(f"/api/formations/{r.json()['id']}")


@pytest.fixture
def parcours(client):
    r = client.post("/api/parcours", json=PARCOURS)
    assert r.status_code == 201, r.text
    yield r.json()["id"]
    client.delete(f"/api/parcours/{r.json()['id']}")


# =============================================================================== utilitaires (sans Fuseki)

def test_utils_valid_id():
    assert valid_id("Module_React")
    for mauvais in ["a b", "X;DROP", "edu:X", "}", "", "Abc\n", "module_React", "1Module", None, 42]:
        assert not valid_id(mauvais)


def test_utils_esc_make_id_pagination():
    assert esc('a"b\\c\nd') == 'a\\"b\\\\c\\nd'
    assert make_id("Sonia Nasri") == "Sonia_Nasri"                      # usage d'Ala et Yahya
    assert make_id("Atelier Vue.js avancé", "Formation") == "Formation_Atelier_Vue_Js_Avance"
    assert make_id("formation courte", "Formation") == "Formation_Courte"
    assert make_id("!!!", "Formation") == ""
    assert pagination(3, 10) == (10, 20)
    assert pagination(0, 1000) == (100, 0)


def test_intents_score_et_debut_de_mot():
    # « combien de module » (3 mots) l'emporte sur « module » seul
    assert detecter_intention("Combien de modules compte la formation Front-end ?") == "COMPTER_MODULES"
    # LISTER_FORMATIONS (poids 0,4) ne passe qu'après les intentions plus précises
    assert classer_intentions("Quelles formations sont gratuites ?")[0] == "FILTRE_COUT"
    assert detecter_intention("bonjour, il fait beau") == "INCONNUE"


# =============================================================================== formations : lecture

def test_lister_formations(client):
    r = client.get("/api/formations")
    assert r.status_code == 200
    corps = r.json()
    assert corps["total"] >= 14 and len(corps["donnees"]) <= 20
    # les formations de membre_imem.ttl sont présentes (sous-classes trouvées via a/rdfs:subClassOf*)
    ids = {f["id"] for f in client.get("/api/formations", params={"taille": 100}).json()["donnees"]}
    assert {"Formation_Initiation_SQL", "BootCamp_NodeJS", "Formation_Licence_Info",
            "Formation_Master_Cloud", "Formation_FullStack_JS"} <= ids


def test_filtres_combines(client):
    donnees = client.get("/api/formations", params={"cout_max": 1000, "niveau": "Avancé", "actif": True}).json()["donnees"]
    assert donnees and all(f["cout"] <= 1000 and f["niveau"] == "Avancé" and f["actif"] for f in donnees)
    gratuites = client.get("/api/formations", params={"cout_max": 0}).json()["donnees"]
    assert "Formation_Initiation_SQL" in {f["id"] for f in gratuites}
    inactives = client.get("/api/formations", params={"actif": False}).json()["donnees"]
    assert "BootCamp_NodeJS" in {f["id"] for f in inactives}
    futures = client.get("/api/formations", params={"a_venir": True, "type": "FormationMaster"}).json()
    assert [f["id"] for f in futures["donnees"]] == ["Formation_Master_Cloud"]
    par_domaine = client.get("/api/formations", params={"domaine": "Domaine_FullStack"}).json()["donnees"]
    assert "Formation_FullStack" in {f["id"] for f in par_domaine}   # lien écrit dans l'autre sens (Ala)


def test_recherche_tri_pagination(client):
    r = client.get("/api/formations", params={"q": "master", "tri": "cout", "ordre": "desc"}).json()
    couts = [f["cout"] for f in r["donnees"]]
    assert r["total"] == 2 and couts == sorted(couts, reverse=True)
    r = client.get("/api/formations", params={"tri": "places", "ordre": "desc", "taille": 100}).json()
    restantes = [f["places_restantes"] for f in r["donnees"] if f["places_restantes"] is not None]
    assert restantes == sorted(restantes, reverse=True)
    p1 = client.get("/api/formations", params={"taille": 5, "page": 1}).json()
    p2 = client.get("/api/formations", params={"taille": 5, "page": 2}).json()
    assert len(p1["donnees"]) == 5 and not {f["id"] for f in p1["donnees"]} & {f["id"] for f in p2["donnees"]}
    assert "SELECT" in p1["sparql"]


def test_lister_parametres_invalides(client):
    assert client.get("/api/formations", params={"type": "x;y"}).status_code == 400
    assert client.get("/api/formations", params={"niveau": "Expert"}).status_code == 400
    assert client.get("/api/formations", params={"tri": "nimporte"}).status_code == 400
    assert client.get("/api/formations", params={"ordre": "haut"}).status_code == 400


def test_options_formations(client):
    o = client.get("/api/formations/options").json()
    assert {"BootCamp", "FormationMaster"} <= {t["id"] for t in o["types"]}
    assert "Module_React" in {m["id"] for m in o["modules"]}
    assert o["domaines"] and o["organismes"] and o["responsables"] and o["certification"]


def test_detail_formation_places_restantes(client):
    f = client.get("/api/formations/Formation_FullStack").json()
    assert f["nombrePlaces"] == 30
    assert f["placesRestantes"] == f["nombrePlaces"] - f["nombreInscrits"]
    assert {"Ahmed", "Sarra"} <= {a["id"] for a in f["inscrits"]}   # via ^edu:estInscritA
    assert f["certification"]["id"] == "Certificat_DeveloppeurWeb"
    assert client.get("/api/formations/Inexistante_42").status_code == 404
    assert client.get("/api/formations/Module_React").status_code == 404   # existe mais n'est pas une formation
    assert client.get("/api/formations/x;y").status_code == 400


# =============================================================================== formations : écriture

def test_creer_formation(client, formation):
    assert formation == "Formation_Test_Imem_Atelier_Vue"
    f = client.get(f"/api/formations/{formation}").json()
    assert f["types"] == ["AtelierIntensif"] and f["coutFormation"] == 250 and f["estActif"] is True
    assert f["dateDebut"] == "2027-03-01T00:00:00"
    assert [m["id"] for m in f["modules"]] == ["Module_JavaScript"]
    assert client.post("/api/formations", json=FORMATION).status_code == 409


@pytest.mark.parametrize("champ, valeur, attendu", [
    ("modules", [], "module"),
    ("domaines", [], "domaine"),
    ("modules", ["Module_Inexistant"], "Module_Inexistant"),
    ("certification", "Module_React", "Certification"),
    ("type", "Module", "sous-classe"),
    ("dateFin", "2027-01-01T00:00:00", "date de fin"),
    ("coutFormation", -5, "coutFormation"),
])
def test_creation_refusee(client, champ, valeur, attendu):
    r = client.post("/api/formations", json={**FORMATION, "intitule": "Test Imem refus", champ: valeur})
    assert r.status_code == 400, r.text
    assert attendu.lower() in r.json()["detail"].lower()
    assert client.get("/api/formations/Formation_Test_Imem_Refus").status_code == 404


def test_injection_refusee(client):
    r = client.post("/api/formations", json={**FORMATION, "intitule": 'Test Imem "} ; DROP ALL ; #'})
    assert r.status_code == 201
    id_ = r.json()["id"]
    assert client.get(f"/api/formations/{id_}").json()["intitule"] == 'Test Imem "} ; DROP ALL ; #'
    assert client.delete(f"/api/formations/{id_}").status_code == 204
    assert client.post("/api/formations", json={**FORMATION, "id": "X} ; DROP ALL"}).status_code == 400


def test_modifier_formation(client, formation):
    maj = {**FORMATION, "coutFormation": 0, "modules": ["Module_HTML", "Module_CSS"], "estActif": False,
           "certification": "Attestation_Module_React"}
    r = client.put(f"/api/formations/{formation}", json=maj)
    assert r.status_code == 200
    f = r.json()
    assert f["coutFormation"] == 0 and f["estActif"] is False
    assert {m["id"] for m in f["modules"]} == {"Module_HTML", "Module_CSS"}
    assert f["certification"]["id"] == "Attestation_Module_React"
    assert client.put("/api/formations/Inexistante_42", json=maj).status_code == 404
    assert client.put(f"/api/formations/{formation}", json={**maj, "modules": []}).status_code == 400


def test_places_inferieures_aux_inscrits(client):
    f = client.get("/api/formations/Formation_FullStack").json()
    corps = {**FORMATION, "intitule": f["intitule"], "type": "FormationFullStack", "nombrePlaces": 1}
    assert client.put("/api/formations/Formation_FullStack", json=corps).status_code == 409


def test_supprimer_formation_et_liens_entrants(client, formation):
    # un organisme pointe vers la formation (sens inverse) : ce lien doit disparaître aussi
    update(f"INSERT DATA {{ edu:MOOC_WebDev edu:proposeFormation edu:{formation} }}")
    assert client.delete(f"/api/formations/{formation}").status_code == 204
    assert not ask(f"ASK {{ {{ edu:{formation} ?p ?o }} UNION {{ ?s ?p edu:{formation} }} }}")
    assert client.delete(f"/api/formations/{formation}").status_code == 404


# =============================================================================== parcours

def test_lister_parcours(client):
    r = client.get("/api/parcours", params={"taille": 50}).json()
    ids = {p["id"] for p in r["donnees"]}
    assert {"Parcours_Frontend_Complet", "Parcours_DevOps_Accelere", "Parcours_Donnees_Competence"} <= ids
    filtre = client.get("/api/parcours", params={"module": "Module_Deploiement"}).json()["donnees"]
    assert {"Parcours_DevOps_Accelere", "Parcours_Backend"} <= {p["id"] for p in filtre}
    assert client.get("/api/parcours", params={"q": "devops"}).json()["total"] == 1
    # animateur déclaré par Ala dans l'autre sens (Mr_Jaziri edu:animeParcours Parcours_Backend)
    par_anim = client.get("/api/parcours", params={"animateur": "Mr_Jaziri"}).json()["donnees"]
    assert "Parcours_Backend" in {p["id"] for p in par_anim}


def test_options_parcours(client):
    o = client.get("/api/parcours/options").json()
    assert "ParcoursAccelere" in {t["id"] for t in o["types"]} and o["modules"] and o["animateurs"]


def test_detail_parcours_modules_ordonnes(client):
    p = client.get("/api/parcours/Parcours_Frontend_Complet").json()
    ordre = [m["id"] for m in p["modules"]]
    # React a des prérequis (aPourPrerequis+) : il vient après JavaScript
    assert ordre.index("Module_JavaScript") < ordre.index("Module_React")
    assert p["animateurs"][0]["id"] == "Mme_Jebali"
    assert client.get("/api/parcours/Inexistant_42").status_code == 404


def test_crud_parcours(client, parcours):
    assert parcours == "Parcours_Test_Imem_Parcours"
    assert client.post("/api/parcours", json=PARCOURS).status_code == 409
    r = client.put(f"/api/parcours/{parcours}", json={**PARCOURS, "modules": ["Module_Git"], "animateurs": []})
    assert r.status_code == 200 and [m["id"] for m in r.json()["modules"]] == ["Module_Git"]
    assert client.post("/api/parcours", json={**PARCOURS, "label": "Test Imem vide", "modules": []}).status_code == 400
    assert client.post("/api/parcours", json={**PARCOURS, "label": "Test Imem anim",
                                              "animateurs": ["Ahmed"]}).status_code == 400
    assert client.delete(f"/api/parcours/{parcours}").status_code == 204
    assert client.get(f"/api/parcours/{parcours}").status_code == 404


# =============================================================================== recherche globale

def test_recherche_globale(client):
    r = client.get("/api/recherche", params={"q": "react"}).json()
    assert {"Module", "Formation", "Competence"} <= {x["categorie"] for x in r["donnees"]}
    assert client.get("/api/recherche", params={"q": "a"}).status_code == 400


# =============================================================================== NLP

COLONNES_CSV = ["auteur", "question", "intention", "entites", "requete_attendue"]


def questions_imem() -> list[dict]:
    """Le fichier commun n'a pas d'en-tête (format de Yahya) : colonnes données explicitement."""
    with open(CSV_QUESTIONS, encoding="utf-8-sig", newline="") as f:
        return [l for l in csv.DictReader(f, fieldnames=COLONNES_CSV) if l["auteur"] == "Imem"]


def test_nlp_douze_questions():
    assert len(questions_imem()) == 12


@pytest.mark.parametrize("ligne", questions_imem(), ids=lambda l: l["question"][:40])
def test_nlp_questions_csv(client, ligne):
    r = client.post("/api/nlp/question", json={"question": ligne["question"]})
    assert r.status_code == 200
    d = r.json()
    assert d["intention"] == ligne["intention"]
    assert [e["uri"] for e in d["entites"]] == [e for e in ligne["entites"].split(";") if e]
    assert d["resultats"], "résultat vide"


def test_nlp_cout_valeurs(client):
    d = client.post("/api/nlp/question", json={"question": "Quelles formations coûtent moins de 1000 dinars ?"}).json()
    assert all(float(x["cout"]) <= 1000 for x in d["resultats"])
    d = client.post("/api/nlp/question", json={"question": "Quelles formations coûtent entre 500 et 2000 dinars ?"}).json()
    assert d["resultats"] and all(500 <= float(x["cout"]) <= 2000 for x in d["resultats"])
    d = client.post("/api/nlp/question", json={"question": "Formations gratuites ?"}).json()
    assert "Formation_Initiation_SQL" in {x["formation"] for x in d["resultats"]}


def test_nlp_filtres_combines(client):
    d = client.post("/api/nlp/question", json={"question": "Formations pour débutants à moins de 1000 dinars ?"}).json()
    assert 'FILTER(STR(?niveau) = "Débutant")' in d["sparql"] and "FILTER(?cout <= 1000)" in d["sparql"]


def test_nlp_echec_propre(client):
    d = client.post("/api/nlp/question", json={"question": "bonjour, il fait beau"}).json()
    assert d["intention"] == "INCONNUE" and "Exemples" in d["message"]
    d = client.post("/api/nlp/question", json={"question": "Combien de modules compte la formation ?"}).json()
    assert d["resultats"] == [] and "Formation" in d["message"]
    d = client.post("/api/nlp/question", json={"question": "Quelles formations coûtent combien ?"}).json()
    assert d["resultats"] == [] and "montant" in d["message"]
