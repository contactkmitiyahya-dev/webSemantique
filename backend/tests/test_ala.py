"""Tests de la tranche d'Ala (formateurs, personnel, organismes, domaines, NLP), contre le vrai Fuseki.

Lancement depuis la racine (Fuseki démarré) :
    backend\\venv\\Scripts\\python -m pytest backend/tests/test_ala.py -v

Tous les individus créés ont un identifiant commençant par Test_Ala_ : ils sont supprimés
à la fin du module par une fixture, même si un test échoue.
"""
import csv
import sys
import warnings
from pathlib import Path

import pytest

# Rend le paquet « app » importable quel que soit le dossier de lancement
RACINE_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_BACKEND))

# Starlette conseille le paquet httpx2 ; tant qu'il n'est pas installé, on masque cet avertissement
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated")
    from fastapi.testclient import TestClient  # noqa: E402

from app.ala_commun import supprimer  # noqa: E402
from app.main import app  # noqa: E402
from app.sparql_client import ask, select, update  # noqa: E402

EDU = "http://www.eduparcours.org/ontologie#"
PREFIXE_TEST = "Test_Ala_"
CSV_QUESTIONS = RACINE_BACKEND.parent / "docs" / "questions_types.csv"


# =============================================================================== outils

def nb_triplets() -> int:
    return int(select("SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }")[0]["n"])


def ids_de_test() -> list[str]:
    """Tous les identifiants Test_Ala_ présents dans Fuseki (sujet ou objet)."""
    lignes = select(f"""SELECT DISTINCT ?x WHERE {{
  {{ ?x ?p ?o }} UNION {{ ?s ?p ?x }}
  FILTER(isIRI(?x) && STRSTARTS(STR(?x), "{EDU}{PREFIXE_TEST}")) }}""")
    return [l["x"] for l in lignes]


def nettoyer_tests() -> None:
    for id_ in ids_de_test():
        supprimer(id_)


def nb_noms(id_: str) -> int:
    return int(select(f"SELECT (COUNT(?n) AS ?k) WHERE {{ edu:{id_} edu:nom ?n }}")[0]["k"])


def lie(id_: str) -> bool:
    """Reste-t-il un triplet sortant OU entrant pour cet individu ?"""
    return ask(f"ASK {{ {{ edu:{id_} ?p ?o }} UNION {{ ?s ?p edu:{id_} }} }}")


# =============================================================================== fixtures

@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module", autouse=True)
def donnees_propres():
    """Avant : supprime les restes d'une exécution précédente.
    Après (même en cas d'échec) : supprime tous les Test_Ala_ et remet Dr_Benali en état."""
    nettoyer_tests()
    total_initial = nb_triplets()
    yield total_initial
    nettoyer_tests()
    update("DELETE WHERE { edu:Dr_Benali edu:enseigne ?c }")


@pytest.fixture
def formateur_test(client):
    """Un formateur de test créé avant le test (supprimé par donnees_propres)."""
    r = client.post("/api/formateurs", json={
        "id": "Test_Ala_Formateur", "type": "FormateurJunior", "nom": "Testeur", "prenom": "Ala",
        "email": "test@eduparcours.org", "experience": 1, "cours": ["Cours_React"]})
    assert r.status_code == 201, r.text
    yield "Test_Ala_Formateur"
    if lie("Test_Ala_Formateur"):
        supprimer("Test_Ala_Formateur")


# =============================================================================== formateurs

def test_formateurs_get_liste(client):
    r = client.get("/api/formateurs", params={"taille": 3})
    assert r.status_code == 200
    corps = r.json()
    assert corps["total"] >= 11 and len(corps["donnees"]) == 3
    assert {"id", "nom", "nom_complet", "type", "nb_cours"} <= set(corps["donnees"][0])


def test_formateurs_get_liste_filtres(client):
    assert client.get("/api/formateurs", params={"type": "FormateurVacataire"}).json()["total"] == 5
    assert client.get("/api/formateurs", params={"specialite": "devops"}).json()["total"] == 3
    r = client.get("/api/formateurs", params={"q": "HICHEM"}).json()
    assert [f["id"] for f in r["donnees"]] == ["Dr_Mansouri"]
    r = client.get("/api/formateurs", params={"experience_min": 10, "tri": "nb_cours", "ordre": "desc"}).json()
    assert r["donnees"][0]["id"] == "Dr_Benali"
    assert all(f["experience"] >= 10 for f in r["donnees"])


def test_formateurs_get_detail(client):
    r = client.get("/api/formateurs/Dr_Benali")
    assert r.status_code == 200
    f = r.json()
    assert f["type"] == "FormateurSenior"
    assert f["prenom"] is None and f["nom_complet"] == "Benali"   # prénom « Dr. » ignoré
    assert len(f["cours"]) == 6
    assert all(c["modifiable"] is False for c in f["cours"])      # écrits par Zahra (enseignePar)


def test_formateurs_post(client):
    r = client.post("/api/formateurs", json={"id": "Test_Ala_Creation", "type": "FormateurSenior",
                                             "nom": "Créé", "experience": 7, "cours": ["Cours_Git"]})
    assert r.status_code == 201
    assert [(c["id"], c["modifiable"]) for c in r.json()["cours"]] == [("Cours_Git", True)]
    assert ask("ASK { edu:Test_Ala_Creation a edu:FormateurSenior , owl:NamedIndividual }")


def test_formateurs_post_id_existant_409(client, formateur_test):
    r = client.post("/api/formateurs", json={"id": formateur_test, "type": "FormateurSenior", "nom": "Doublon"})
    assert r.status_code == 409
    assert "existe déjà" in r.json()["detail"]


@pytest.mark.parametrize("corps, extrait", [
    ({"type": "Chef", "nom": "X"}, "Type invalide"),
    ({"type": "FormateurSenior", "nom": ""}, "obligatoire"),
    ({"type": "FormateurSenior", "nom": "X", "email": "pas-un-email"}, "Email invalide"),
    ({"type": "FormateurSenior", "nom": "X", "experience": -1}, "positif"),
    ({"type": "FormateurJunior", "nom": "X", "experience": 5}, "au plus 3"),
    ({"type": "FormateurSenior", "nom": "X", "experience": "beaucoup"}, "experience"),
    ({"type": "FormateurSenior", "nom": "X", "cours": ["Cours_Inexistant"]}, "introuvable"),
    ({"id": "Test_Ala_a b;", "type": "FormateurSenior", "nom": "X"}, "Identifiant invalide"),
])
def test_formateurs_post_invalide_400(client, corps, extrait):
    r = client.post("/api/formateurs", json=corps)
    assert r.status_code == 400
    assert extrait in r.json()["detail"]


def test_formateurs_put(client, formateur_test):
    r = client.put(f"/api/formateurs/{formateur_test}", json={
        "type": "FormateurSenior", "experience": 9, "specialite": "Tests", "apprenants": ["Karim"]})
    assert r.status_code == 200
    f = r.json()
    assert (f["type"], f["experience"], f["specialite"]) == ("FormateurSenior", 9, "Tests")
    assert [a["id"] for a in f["apprenants"]] == ["Karim"]
    assert [c["id"] for c in f["cours"]] == ["Cours_React"]          # non envoyé : inchangé


def test_formateurs_put_nom_une_seule_valeur(client, formateur_test):
    for nom in ("Premier", "Second"):
        assert client.put(f"/api/formateurs/{formateur_test}", json={"nom": nom}).status_code == 200
    assert nb_noms(formateur_test) == 1
    assert client.get(f"/api/formateurs/{formateur_test}").json()["nom"] == "Second"


def test_formateurs_put_junior_trop_experimente_400(client, formateur_test):
    r = client.put(f"/api/formateurs/{formateur_test}", json={"experience": 8})
    assert r.status_code == 400
    assert client.get(f"/api/formateurs/{formateur_test}").json()["experience"] == 1   # rien modifié


def test_formateurs_put_ne_touche_pas_aux_liens_des_autres(client, donnees_propres):
    """Modifier les cours de Dr_Benali ne supprime aucun triplet edu:enseignePar
    (sujet = cours de Zahra) et le nombre de triplets ne baisse pas."""
    def enseigne_par():
        return {l["c"] for l in select("SELECT ?c WHERE { ?c edu:enseignePar edu:Dr_Benali }")}
    liens_avant, total_avant = enseigne_par(), nb_triplets()
    assert liens_avant

    r = client.put("/api/formateurs/Dr_Benali", json={"cours": ["Cours_Git"]})
    assert r.status_code == 200
    cours = {c["id"]: c["modifiable"] for c in r.json()["cours"]}
    assert cours["Cours_Git"] is True and all(cours[c] is False for c in liens_avant)
    assert enseigne_par() == liens_avant
    assert nb_triplets() == total_avant + 1

    r = client.put("/api/formateurs/Dr_Benali", json={"cours": []})
    assert {c["id"] for c in r.json()["cours"]} == liens_avant      # seuls MES liens disparaissent
    assert enseigne_par() == liens_avant
    assert nb_triplets() == total_avant


def test_formateurs_delete_supprime_liens_entrants(client, formateur_test):
    # Lien ENTRANT ajouté à la main (comme si Zahra l'avait écrit) : il doit disparaître aussi
    update(f"INSERT DATA {{ edu:Cours_Docker edu:enseignePar edu:{formateur_test} }}")
    assert ask(f"ASK {{ ?s ?p edu:{formateur_test} }}")

    r = client.delete(f"/api/formateurs/{formateur_test}")
    assert r.status_code == 204
    assert not ask(f"ASK {{ ?s ?p edu:{formateur_test} }}")        # entrants supprimés
    assert not lie(formateur_test)
    assert client.get(f"/api/formateurs/{formateur_test}").status_code == 404


@pytest.mark.parametrize("methode", ["GET", "PUT", "DELETE"])
def test_formateurs_id_invalide_400(client, methode):
    r = client.request(methode, "/api/formateurs/a b;", json={} if methode == "PUT" else None)
    assert r.status_code == 400
    assert "Identifiant invalide" in r.json()["detail"]


def test_formateurs_introuvable_404(client):
    assert client.get("/api/formateurs/Test_Ala_Fantome").status_code == 404
    assert client.get("/api/formateurs/Cours_React").status_code == 404   # existe mais pas formateur
    assert client.delete("/api/formateurs/Test_Ala_Fantome").status_code == 404


# =============================================================================== personnel

def test_responsables_get_liste(client):
    r = client.get("/api/responsables").json()
    assert r["total"] == 7
    r = client.get("/api/responsables", params={"type": "ResponsablePedagogique"}).json()
    assert {p["id"] for p in r["donnees"]} == {"Mr_Dridi", "Mr_Zouari"}
    assert client.get("/api/responsables", params={"type": "Directeur"}).status_code == 400


def test_responsables_get_detail(client):
    p = client.get("/api/responsables/Mr_Dridi").json()
    assert (p["type"], p["categorie"]) == ("ResponsablePedagogique", "ResponsableFormation")
    assert {f["id"] for f in p["formations"]} >= {"Formation_Backend"}     # lien estAdministreePar
    assert all(f["modifiable"] is False for f in p["formations"])


def test_responsables_post_put_delete(client):
    r = client.post("/api/responsables", json={"id": "Test_Ala_Resp", "type": "ResponsableDeFormation",
                                               "nom": "Resp", "formations": ["Formation_Angular"]})
    assert r.status_code == 201
    assert r.json()["categorie"] == "ResponsableFormation"
    assert client.post("/api/responsables", json={"id": "Test_Ala_Resp", "type": "AgentScolarite",
                                                  "nom": "X"}).status_code == 409

    # Passer en agent de scolarité en gardant une formation : refusé (classes disjointes)
    assert client.put("/api/responsables/Test_Ala_Resp", json={"type": "AgentScolarite"}).status_code == 400
    r = client.put("/api/responsables/Test_Ala_Resp", json={"type": "AgentScolarite", "formations": []})
    assert r.status_code == 200
    assert (r.json()["categorie"], r.json()["formations"]) == ("ServiceScolarite", [])

    assert client.delete("/api/responsables/Test_Ala_Resp").status_code == 204
    assert not lie("Test_Ala_Resp")


def test_responsables_agent_avec_formation_400(client):
    r = client.post("/api/responsables", json={"id": "Test_Ala_Agent", "type": "AgentScolarite",
                                               "nom": "Agent", "formations": ["BootCamp_Web"]})
    assert r.status_code == 400
    assert "disjointes" in r.json()["detail"]


# =============================================================================== organismes

def test_organismes_get_liste(client):
    r = client.get("/api/organismes", params={"type": "OrganismeCertificateur"}).json()
    assert r["total"] == 4                                   # sous-classes comprises
    assert client.get("/api/organismes", params={"q": "UNIV"}).json()["total"] == 2


def test_organismes_get_detail(client):
    o = client.get("/api/organismes/EduParcours_Academie").json()
    assert o["type"] == "AcademieEnLigne"
    assert len(o["formations"]) >= 5   # les deux sens (|) ; >= : les autres membres en ajoutent (Imem : 2)
    modifiables = {f["modifiable"] for f in o["formations"]}
    assert modifiables == {True, False}                       # proposeFormation ET estProposeePar


def test_organismes_post_put_delete(client):
    r = client.post("/api/organismes", json={"id": "Test_Ala_Org", "type": "MOOC", "label": "MOOC Test",
                                             "formations": ["Formation_Angular"]})
    assert r.status_code == 201
    assert client.post("/api/organismes", json={"id": "Test_Ala_Org", "type": "MOOC",
                                                "label": "X"}).status_code == 409
    assert client.post("/api/organismes", json={"type": "Banque", "label": "X"}).status_code == 400
    r = client.put("/api/organismes/Test_Ala_Org", json={"label": "MOOC Test 2", "certifications": ["Certificat_Backend"]})
    assert r.status_code == 200
    assert r.json()["label"] == "MOOC Test 2"
    assert [c["id"] for c in r.json()["certifications"]] == ["Certificat_Backend"]
    assert client.delete("/api/organismes/Test_Ala_Org").status_code == 204
    assert not lie("Test_Ala_Org")


# =============================================================================== domaines

def test_domaines_get_liste(client):
    assert client.get("/api/domaines").json()["total"] == 8
    assert client.get("/api/domaines", params={"type": "DomaineInformatique"}).json()["total"] == 6


def test_domaines_get_detail(client):
    d = client.get("/api/domaines/Domaine_FullStack").json()
    assert d["intitule"] == "Développement full-stack"
    assert {f["id"] for f in d["formations"]} == {"Formation_FullStack", "BootCamp_Web"}


def test_domaines_post_put_delete(client):
    r = client.post("/api/domaines", json={"id": "Test_Ala_Dom", "type": "UXDesign", "intitule": "Domaine test"})
    assert r.status_code == 201
    assert r.json()["label"] == "Domaine test"
    assert client.post("/api/domaines", json={"id": "Test_Ala_Dom", "type": "UXDesign",
                                              "intitule": "X"}).status_code == 409
    r = client.put("/api/domaines/Test_Ala_Dom", json={"intitule": "Domaine modifié", "formations": ["Formation_Frontend"]})
    assert r.status_code == 200
    assert (r.json()["intitule"], r.json()["label"]) == ("Domaine modifié", "Domaine modifié")
    assert client.delete("/api/domaines/Test_Ala_Dom").status_code == 204
    assert not lie("Test_Ala_Dom")


# =============================================================================== sécurité

INJECTIONS = [
    '") } DROP ALL #',
    'x")) } } ; DELETE WHERE { ?s ?p ?o } #',
    '\\" } ; CLEAR DEFAULT ; #',
]


@pytest.mark.parametrize("ressource", ["formateurs", "responsables", "organismes", "domaines"])
@pytest.mark.parametrize("injection", INJECTIONS)
def test_injection_dans_q(client, ressource, injection):
    total = nb_triplets()
    r = client.get(f"/api/{ressource}", params={"q": injection})
    assert r.status_code == 200                     # jamais 500
    assert r.json()["total"] == 0
    assert nb_triplets() == total                   # données intactes


def test_injection_dans_un_champ_stocke_tel_quel(client):
    """Une chaîne malveillante est échappée : elle est enregistrée comme simple texte."""
    total = nb_triplets()
    nom = 'Pirate" . } ; DROP ALL ; #\n"'
    r = client.post("/api/formateurs", json={"id": "Test_Ala_Pirate", "type": "FormateurSenior", "nom": nom})
    assert r.status_code == 201
    assert client.get("/api/formateurs/Test_Ala_Pirate").json()["nom"] == nom
    assert client.delete("/api/formateurs/Test_Ala_Pirate").status_code == 204
    assert nb_triplets() == total


# =============================================================================== NLP

COLONNES_CSV = ["auteur", "question", "intention", "entites", "requete_attendue"]


def questions_ala() -> list[dict]:
    """Colonnes données explicitement : le fichier commun n'a pas d'en-tête
    (format de Yahya) ; une éventuelle ligne d'en-tête est écartée par le filtre « Ala »."""
    with open(CSV_QUESTIONS, encoding="utf-8-sig", newline="") as f:
        return [l for l in csv.DictReader(f, fieldnames=COLONNES_CSV) if l["auteur"] == "Ala"]


@pytest.mark.parametrize("ligne", questions_ala(), ids=lambda l: l["intention"])
def test_nlp_questions_csv(client, ligne):
    r = client.post("/api/nlp/question", json={"question": ligne["question"]})
    assert r.status_code == 200
    d = r.json()
    assert d["intention"] == ligne["intention"]
    assert [e["uri"] for e in d["entites"]] == [e for e in ligne["entites"].split(";") if e]
    assert d["resultats"], "résultat vide"


def test_nlp_faute_de_frappe_reakt(client):
    d = client.post("/api/nlp/question", json={"question": "Qui enseigne le cours reakt ?"}).json()
    assert d["intention"] == "ENSEIGNANT"
    assert d["entites"][0]["uri"] == "Cours_React"
    assert d["resultats"]


def test_nlp_cours_de_cuisine_pas_reconnu(client):
    r = client.post("/api/nlp/question", json={"question": "Qui enseigne le cours de cuisine ?"})
    assert r.status_code == 200
    d = r.json()
    assert d["entites"] == [] and d["resultats"] == []
    assert "aucun élément" in d["message"]


@pytest.mark.parametrize("question", ["Quelle est la météo demain ?", ""])
def test_nlp_question_inconnue_message_aide(client, question):
    r = client.post("/api/nlp/question", json={"question": question})
    assert r.status_code == 200
    d = r.json()
    assert d["intention"] == "INCONNUE"
    assert "Exemples de questions" in d["message"]


# =============================================================================== fin

def test_zz_aucune_trace_apres_nettoyage(donnees_propres):
    """Dernier test : après nettoyage, plus aucun Test_Ala_ et le nombre de triplets initial."""
    nettoyer_tests()
    assert ids_de_test() == []
    assert nb_triplets() == donnees_propres
