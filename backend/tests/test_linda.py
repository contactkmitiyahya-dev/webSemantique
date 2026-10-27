"""
Tests de la tranche Linda : /api/competences, /api/technologies, /api/evaluations et NLP.
Prerequis : Fuseki demarre avec l'ontologie + data/membre_linda.ttl.
Lance avec : pytest tests/test_linda.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def ids(liste):
    return {e["id"] for e in liste}


def chercher(noeuds, cible):
    """Cherche un id dans un arbre {id, enfants} et renvoie le noeud."""
    for n in noeuds:
        if n["id"] == cible:
            return n
        trouve = chercher(n["enfants"], cible)
        if trouve:
            return trouve
    return None


# ==========================================
# 1. Competences : lecture
# ==========================================

def test_liste_competences():
    r = client.get("/api/competences?taille=100")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 29
    assert {"Comp_CSS", "Comp_GraphQL", "Comp_Autonomie"} <= ids(data["donnees"])


def test_pagination_competences():
    data = client.get("/api/competences?page=2&taille=5").json()
    assert len(data["donnees"]) == 5
    assert data["total"] >= 29


def test_filtre_type_competences():
    data = client.get("/api/competences?type=CompetenceTransversale&taille=100").json()
    trouves = ids(data["donnees"])
    assert "Comp_Autonomie" in trouves and "Comp_Communication" in trouves
    assert "Comp_CSS" not in trouves


def test_recherche_competence():
    data = client.get("/api/competences?q=sql").json()
    assert {"Comp_SQL", "Comp_PostgreSQL", "Comp_NoSQL"} <= ids(data["donnees"])


def test_types_competences():
    r = client.get("/api/competences/types")
    assert r.status_code == 200
    assert "CompetenceGraphQL" in ids(r.json())


def test_detail_competence():
    r = client.get("/api/competences/Comp_PostgreSQL")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "CompetenceSQL"
    assert data["scoreMaturite"] == 62
    assert ids(data["parents"]) == {"Comp_BasesDeDonnees"}
    assert "Tech_PostgreSQL" in ids(data["technologies"])
    assert "Soutenance_BDD" in ids(data["evaluations"])


def test_equivalence_dans_les_deux_sens():
    assert "Comp_PostgreSQL" in ids(client.get("/api/competences/Comp_SQL").json()["equivalentes"])
    assert "Comp_SQL" in ids(client.get("/api/competences/Comp_PostgreSQL").json()["equivalentes"])


def test_transitivite_sous_competences():
    data = client.get("/api/competences/Comp_DeveloppementBackend").json()
    directes, toutes = ids(data["sousCompetences"]), ids(data["toutesSousCompetences"])
    assert "Comp_GraphQL" not in directes
    assert {"Comp_GraphQL", "Comp_PostgreSQL", "Comp_Express"} <= toutes
    assert "Comp_ProgrammationWeb" in ids(data["ancetres"])


def test_modules_pour_acquerir_competence():
    data = client.get("/api/competences/Comp_JavaScript").json()
    assert "Module_JavaScript" in ids(data["modulesPourAcquerir"])
    assert "Module_NodeJS" in ids(data["modulesRequierent"])


def test_arbre_competences():
    r = client.get("/api/competences/arbre?racine=Comp_ProgrammationWeb")
    assert r.status_code == 200
    graphql = chercher(r.json(), "Comp_GraphQL")
    assert graphql is not None and graphql["enfants"] == []
    assert chercher(client.get("/api/competences/arbre").json(), "Comp_Autonomie") is not None


def test_competences_repandues():
    r = client.get("/api/competences/repandues?limite=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    nbs = [c["nbApprenants"] for c in data]
    assert nbs == sorted(nbs, reverse=True)
    assert data[0]["id"] == "Comp_HTML"


def test_detail_competence_inexistante():
    assert client.get("/api/competences/Comp_Inexistante_123").status_code == 404


def test_detail_competence_id_invalide():
    assert client.get("/api/competences/comp;DROP").status_code == 400


# ==========================================
# 2. Competences : ecriture et contraintes
# ==========================================

def test_crud_competence():
    cid = "Comp_Test_Linda"
    client.delete(f"/api/competences/{cid}")
    payload = {"id": cid, "intitule": "Test Linda", "type": "CompetenceCSS", "scoreMaturite": 30,
               "parents": ["Comp_CSS"], "equivalentes": ["Comp_ResponsiveDesign"],
               "technologies": ["Tech_CSS3"]}

    r = client.post("/api/competences", json=payload)
    assert r.status_code == 201
    assert ids(r.json()["parents"]) == {"Comp_CSS"}
    # Equivalence ecrite dans les deux sens
    assert cid in ids(client.get("/api/competences/Comp_ResponsiveDesign").json()["equivalentes"])
    # La nouvelle competence apparait sous Programmation Web (transitivite)
    assert cid in ids(client.get("/api/competences/Comp_ProgrammationWeb").json()["toutesSousCompetences"])

    assert client.post("/api/competences", json=payload).status_code == 409

    payload.update(intitule="Test Linda modifie", scoreMaturite=55, equivalentes=[])
    r = client.put(f"/api/competences/{cid}", json=payload)
    assert r.status_code == 200
    assert r.json()["intitule"] == "Test Linda modifie" and r.json()["scoreMaturite"] == 55
    assert cid not in ids(client.get("/api/competences/Comp_ResponsiveDesign").json()["equivalentes"])

    assert client.delete(f"/api/competences/{cid}").status_code == 204
    assert client.get(f"/api/competences/{cid}").status_code == 404
    # Les triplets entrants ont disparu aussi
    assert cid not in ids(client.get("/api/competences/Comp_CSS").json()["sousCompetences"])


def test_id_genere_depuis_intitule():
    r = client.post("/api/competences", json={"intitule": "Tests unitaires Jest", "type": "CompetenceJavaScript"})
    assert r.status_code == 201
    assert r.json()["id"] == "Comp_Tests_Unitaires_Jest"
    assert client.delete("/api/competences/Comp_Tests_Unitaires_Jest").status_code == 204


def test_score_hors_limites_refuse():
    r = client.post("/api/competences", json={"id": "Comp_Test_Score", "intitule": "X", "scoreMaturite": 150})
    assert r.status_code == 400


def test_type_hors_competence_refuse():
    r = client.post("/api/competences", json={"id": "Comp_Test_Type", "intitule": "X", "type": "Formation"})
    assert r.status_code == 400


def test_parent_inexistant_refuse():
    r = client.post("/api/competences", json={"id": "Comp_Test_Parent", "intitule": "X", "parents": ["Comp_Fantome"]})
    assert r.status_code == 400


def test_cycle_sous_competences_refuse():
    for c in ("Comp_Test_B", "Comp_Test_A"):
        client.delete(f"/api/competences/{c}")
    assert client.post("/api/competences", json={"id": "Comp_Test_A", "intitule": "A"}).status_code == 201
    assert client.post("/api/competences", json={"id": "Comp_Test_B", "intitule": "B", "parents": ["Comp_Test_A"]}).status_code == 201
    # A sous-competence de B alors que B est deja sous-competence de A -> cycle
    r = client.put("/api/competences/Comp_Test_A", json={"intitule": "A", "parents": ["Comp_Test_B"]})
    assert r.status_code == 400
    assert "cycle" in r.json()["detail"].lower()
    # Soi-meme comme parent
    r = client.put("/api/competences/Comp_Test_A", json={"intitule": "A", "parents": ["Comp_Test_A"]})
    assert r.status_code == 400
    for c in ("Comp_Test_B", "Comp_Test_A"):
        client.delete(f"/api/competences/{c}")


def test_suppression_refusee_si_evaluation_sans_competence():
    # Autoeval_Autonomie ne porte que sur Comp_Autonomie
    r = client.delete("/api/competences/Comp_Autonomie")
    assert r.status_code == 409
    assert client.get("/api/competences/Comp_Autonomie").status_code == 200


# ==========================================
# 3. Technologies
# ==========================================

def test_liste_technologies():
    data = client.get("/api/technologies?taille=100").json()
    assert data["total"] >= 15
    assert {"Tech_PostgreSQL", "Tech_Vue"} <= ids(data["donnees"])


def test_filtre_type_et_recherche_technologies():
    outils = ids(client.get("/api/technologies?type=TechnologieOutil").json()["donnees"])
    assert {"Tech_Git", "Tech_Docker", "Tech_GitHubActions"} <= outils
    assert "Tech_React" not in outils
    assert ids(client.get("/api/technologies?q=postgre").json()["donnees"]) == {"Tech_PostgreSQL"}


def test_types_technologies():
    assert "BaseSQL" in ids(client.get("/api/technologies/types").json())


def test_detail_technologie():
    data = client.get("/api/technologies/Tech_Vue").json()
    assert data["type"] == "FrameworkVue"
    assert "Comp_Vue" in ids(data["competences"])
    assert client.get("/api/technologies/Tech_Fantome").status_code == 404


def test_crud_technologie():
    tid = "Tech_Test_Linda"
    client.delete(f"/api/technologies/{tid}")
    payload = {"id": tid, "label": "Svelte", "type": "FrameworkFrontend", "competences": ["Comp_JavaScript"]}
    r = client.post("/api/technologies", json=payload)
    assert r.status_code == 201
    assert tid in ids(client.get("/api/competences/Comp_JavaScript").json()["technologies"])
    assert client.post("/api/technologies", json=payload).status_code == 409

    payload.update(label="SvelteKit", competences=[])
    r = client.put(f"/api/technologies/{tid}", json=payload)
    assert r.status_code == 200 and r.json()["label"] == "SvelteKit"
    assert tid not in ids(client.get("/api/competences/Comp_JavaScript").json()["technologies"])

    assert client.delete(f"/api/technologies/{tid}").status_code == 204
    assert client.get(f"/api/technologies/{tid}").status_code == 404


def test_suppression_technologie_refusee_si_cours_sans_technologie():
    # Cours_Git n'utilise que Tech_Git (axiome : un cours utilise au moins une technologie)
    assert client.delete("/api/technologies/Tech_Git").status_code == 409


# ==========================================
# 4. Evaluations
# ==========================================

EVAL = {"id": "Eval_Test_Linda", "label": "Quiz test Linda", "type": "QuizEnLigne",
        "dateEvaluation": "2027-04-01T00:00:00", "noteMinimale": 10, "coefficient": 1.5,
        "competences": ["Comp_React"], "modules": ["Module_React"], "cours": ["Cours_React"]}


def test_liste_evaluations():
    data = client.get("/api/evaluations?taille=100").json()
    assert data["total"] >= 15
    assert {"Quiz_Flexbox", "Soutenance_BDD"} <= ids(data["donnees"])


def test_filtre_module_evaluations():
    trouves = ids(client.get("/api/evaluations?module=Module_NodeJS").json()["donnees"])
    assert {"Quiz_NodeJS", "Examen_Final_Backend", "Projet_API_GraphQL"} <= trouves
    assert "Quiz_HTML" not in trouves


def test_filtre_dates_evaluations():
    data = client.get("/api/evaluations?date_min=2027-01-01&date_max=2027-02-28&taille=100").json()
    dates = [e["dateEvaluation"] for e in data["donnees"]]
    assert dates and all("2027-01-01" <= d[:10] <= "2027-02-28" for d in dates)
    assert "Examen_Final_Backend" in ids(data["donnees"])


def test_filtre_type_et_competence_evaluations():
    quiz = ids(client.get("/api/evaluations?type=Quiz").json()["donnees"])
    assert {"Quiz_HTML", "Quiz_Flexbox"} <= quiz and "Soutenance_BDD" not in quiz
    assert ids(client.get("/api/evaluations?competence=Comp_GraphQL").json()["donnees"]) == {"Projet_API_GraphQL"}


def test_date_invalide_refusee():
    assert client.get("/api/evaluations?date_min=demain").status_code == 400


def test_statistiques_evaluations():
    data = client.get("/api/evaluations/statistiques").json()
    soutenance = next(s for s in data if s["type"] == "SoutenanceProjet")
    assert soutenance["moyenneNoteMinimale"] == 12
    assert soutenance["nbEvaluations"] == 2


def test_options_evaluations():
    data = client.get("/api/evaluations/options").json()
    assert "Module_NodeJS" in ids(data["modules"])
    assert "Cours_React" in ids(data["cours"])
    assert "Comp_GraphQL" in ids(data["competences"])
    assert "SoutenanceProjet" in ids(data["types"])


def test_types_et_detail_evaluation():
    assert "ExamenFinal" in ids(client.get("/api/evaluations/types").json())
    data = client.get("/api/evaluations/Quiz_HTML").json()
    assert data["noteMinimale"] == 10
    # Cours relie seulement par l'inverse (Cours_Intro_HTML estEvaluePar Quiz_HTML)
    assert "Cours_Intro_HTML" in ids(data["cours"])
    assert {"Ahmed", "Mariem"} <= ids(data["apprenants"])
    assert client.get("/api/evaluations/Eval_Fantome").status_code == 404


def test_crud_evaluation():
    client.delete(f"/api/evaluations/{EVAL['id']}")
    r = client.post("/api/evaluations", json=EVAL)
    assert r.status_code == 201
    assert r.json()["dateEvaluation"].startswith("2027-04-01")
    assert client.post("/api/evaluations", json=EVAL).status_code == 409

    r = client.put(f"/api/evaluations/{EVAL['id']}", json={**EVAL, "noteMinimale": 14, "modules": ["Module_JavaScript"]})
    assert r.status_code == 200
    assert r.json()["noteMinimale"] == 14 and ids(r.json()["modules"]) == {"Module_JavaScript"}

    assert client.delete(f"/api/evaluations/{EVAL['id']}").status_code == 204
    assert client.get(f"/api/evaluations/{EVAL['id']}").status_code == 404


@pytest.mark.parametrize("champ, valeur", [
    ("competences", []),
    ("modules", []),
    ("noteMinimale", 25),
    ("coefficient", 0),
    ("dateEvaluation", "pas-une-date"),
    ("type", "Competence"),
    ("modules", ["Module_Fantome"]),
])
def test_evaluation_invalide_refusee(champ, valeur):
    r = client.post("/api/evaluations", json={**EVAL, "id": "Eval_Test_Invalide", champ: valeur})
    assert r.status_code == 400
    assert client.get("/api/evaluations/Eval_Test_Invalide").status_code == 404


# ==========================================
# 5. NLP (tranche Linda)
# ==========================================

def poser(question):
    r = client.post("/api/nlp/question", json={"question": question})
    assert r.status_code == 200
    return r.json()


QUESTIONS_LINDA = [
    ("Quelles sont les sous-compétences de Programmation Web ?", "SOUS_COMPETENCES", "Comp_GraphQL"),
    ("Quelles compétences sont équivalentes à React ?", "EQUIVALENTES", "Comp_Vue"),
    ("Quelles technologies sont liées à la compétence SQL ?", "TECHNO_COMPETENCE", "Tech_MySQL"),
    ("Quels modules permettent d'acquérir la compétence JavaScript ?", "MODULES_COMPETENCE", "Module_JavaScript"),
    ("Quelles sont les évaluations du module Node.js ?", "EVALUATIONS_MODULE", "Quiz_NodeJS"),
    ("Quelles évaluations ont lieu après le 1er février 2027 ?", "EVALUATIONS_APRES", "Soutenance_BDD"),
    ("Quelle est la note minimale du Quiz Angular ?", "NOTE_MINIMALE", "Quiz_Angular"),
    ("Quelles sont les compétences les plus répandues ?", "COMPETENCES_REPANDUES", "Comp_HTML"),
]


@pytest.mark.parametrize("question, intention, attendu", QUESTIONS_LINDA, ids=[q[1] for q in QUESTIONS_LINDA])
def test_nlp_intentions_linda(question, intention, attendu):
    rep = poser(question)
    assert rep["intention"] == intention
    assert any(attendu in r.values() for r in rep["resultats"])


def test_nlp_faute_de_frappe():
    rep = poser("Quelles sont les compétences équivalentes à Reakt ?")
    assert rep["intention"] == "EQUIVALENTES"
    assert "Comp_React" in rep["entites"]["competence"]


def test_nlp_entite_absente_message_aide():
    rep = poser("Quelles sont les sous-compétences de la cuisine ?")
    assert rep["intention"] == "SOUS_COMPETENCES"
    assert rep["sparql"] == "" and "Exemples" in rep["message"]


def test_nlp_question_inconnue_message_aide():
    rep = poser("Quel temps fera-t-il demain ?")
    assert rep["intention"] == "INCONNUE"
    assert rep["message"]
