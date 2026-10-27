"""Tests d'intégration des routes Modules, Cours et Ressources (tranche Zahra).

Ils s'exécutent contre le dataset Fuseki réel : Fuseki doit tourner sur le port 3030.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lister_modules():
    r = client.get("/api/modules", params={"taille": 5})
    assert r.status_code == 200
    corps = r.json()
    assert corps["total"] > 0
    assert len(corps["donnees"]) <= 5


def test_detail_module():
    r = client.get("/api/modules/Module_HTML")
    assert r.status_code == 200
    assert r.json()["intitule"] == "Module HTML"


def test_detail_module_inconnu_renvoie_404():
    r = client.get("/api/modules/Module_Inexistant")
    assert r.status_code == 404


def test_id_invalide_renvoie_400():
    r = client.get("/api/modules/Module-Invalide")
    assert r.status_code == 400


def test_prerequis_module():
    r = client.get("/api/modules/Module_Interactivite/prerequis")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()["prerequis"]}
    assert ids == {"Module_Mise_En_Forme", "Module_Fondamentaux_Web"}


def test_competences_requises_module():
    r = client.get("/api/modules/Module_Production/competences-requises")
    assert r.status_code == 200
    ids = {c["id"] for c in r.json()["competencesRequises"]}
    assert {"Comp_NodeJS", "Comp_JavaScript", "Comp_CSS", "Comp_HTML"} <= ids


def test_creer_modifier_supprimer_module():
    client.delete("/api/modules/Test_Pytest_Module")
    corps = {"intitule": "Test Pytest Module", "dureeHeures": 10, "niveauDifficulte": "Débutant"}
    r = client.post("/api/modules", json=corps)
    assert r.status_code == 201
    id_ = r.json()["id"]
    try:
        r = client.put(f"/api/modules/{id_}", json={"dureeHeures": 12})
        assert r.status_code == 200
        assert str(client.get(f"/api/modules/{id_}").json()["dureeHeures"]) == "12"

        assert client.delete(f"/api/modules/{id_}").status_code == 204
        assert client.get(f"/api/modules/{id_}").status_code == 404
    finally:
        client.delete(f"/api/modules/{id_}")


def test_prerequis_cycle_refuse():
    r = client.post("/api/modules/Module_Fondamentaux_Web/prerequis", json={"prerequisId": "Module_Production"})
    assert r.status_code == 400


def test_ajouter_prerequis_valide():
    r = client.post("/api/modules", json={"intitule": "Test Pytest Prerequis", "dureeHeures": 4, "niveauDifficulte": "Débutant"})
    assert r.status_code == 201
    id_ = r.json()["id"]
    try:
        r = client.post(f"/api/modules/{id_}/prerequis", json={"prerequisId": "Module_HTML"})
        assert r.status_code == 201
        ids = {p["id"] for p in client.get(f"/api/modules/{id_}/prerequis").json()["prerequis"]}
        assert "Module_HTML" in ids
    finally:
        client.delete(f"/api/modules/{id_}")


def test_supprimer_module_avec_cours_refuse():
    assert client.delete("/api/modules/Module_HTML").status_code == 409


def test_lister_cours():
    r = client.get("/api/cours", params={"taille": 5})
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_detail_cours():
    r = client.get("/api/cours/Cours_HTML5_Semantique")
    assert r.status_code == 200
    corps = r.json()
    assert corps["module"][0]["id"] == "Module_Fondamentaux_Web"
    assert corps["formateur"][0]["id"] == "Dr_Benali"
    assert corps["technologies"][0]["id"] == "Tech_HTML5"


def test_creer_modifier_supprimer_cours():
    corps = {
        "intitule": "Test Pytest",
        "dureeHeures": 5,
        "niveauDifficulte": "Débutant",
        "ordreDansModule": 2,
        "moduleId": "Module_Fondamentaux_Web",
        "formateurId": "Dr_Benali",
        "competenceId": "Comp_HTML",
        "technologieId": "Tech_HTML5",
    }
    r = client.post("/api/cours", json=corps)
    assert r.status_code == 201
    id_ = r.json()["id"]
    try:
        r = client.put(f"/api/cours/{id_}", json={"dureeHeures": 8})
        assert r.status_code == 200
        assert str(client.get(f"/api/cours/{id_}").json()["dureeHeures"]) == "8"

        assert client.delete(f"/api/cours/{id_}").status_code == 204
        assert client.get(f"/api/cours/{id_}").status_code == 404
    finally:
        client.delete(f"/api/cours/{id_}")


def test_cours_module_inconnu_refuse():
    corps = {
        "intitule": "Test Pytest Refus",
        "dureeHeures": 5,
        "niveauDifficulte": "Débutant",
        "ordreDansModule": 1,
        "moduleId": "Module_Inexistant",
        "formateurId": "Dr_Benali",
        "competenceId": "Comp_HTML",
        "technologieId": "Tech_HTML5",
    }
    assert client.post("/api/cours", json=corps).status_code == 400


def test_cours_formateur_inconnu_refuse():
    corps = {
        "intitule": "Test Pytest Refus",
        "dureeHeures": 5,
        "niveauDifficulte": "Débutant",
        "ordreDansModule": 1,
        "moduleId": "Module_Fondamentaux_Web",
        "formateurId": "Dr_Inexistant",
        "competenceId": "Comp_HTML",
        "technologieId": "Tech_HTML5",
    }
    assert client.post("/api/cours", json=corps).status_code == 400


def test_lister_ressources():
    r = client.get("/api/ressources", params={"taille": 5})
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_detail_ressource():
    r = client.get("/api/ressources/Video_HTML5_Intro")
    assert r.status_code == 200
    corps = r.json()
    assert corps["langue"] == "fr"
    assert any(c["id"] == "Cours_HTML5_Semantique" for c in corps["utiliseeParCours"])


def test_type_ressource_invalide_renvoie_400():
    corps = {
        "intitule": "Test Pytest",
        "urlRessource": "https://example.org/test",
        "langue": "fr",
        "type": "TypeInconnu",
        "competenceId": "Comp_HTML",
    }
    r = client.post("/api/ressources", json=corps)
    assert r.status_code == 400


def test_creer_modifier_supprimer_ressource():
    corps = {
        "intitule": "Test Pytest",
        "urlRessource": "https://example.org/test",
        "langue": "fr",
        "type": "Video",
        "competenceId": "Comp_HTML",
        "dureeMinutes": 5,
    }
    r = client.post("/api/ressources", json=corps)
    assert r.status_code == 201
    id_ = r.json()["id"]
    try:
        r = client.put(f"/api/ressources/{id_}", json={"langue": "en"})
        assert r.status_code == 200
        assert client.get(f"/api/ressources/{id_}").json()["langue"] == "en"

        assert client.delete(f"/api/ressources/{id_}").status_code == 204
        assert client.get(f"/api/ressources/{id_}").status_code == 404
    finally:
        client.delete(f"/api/ressources/{id_}")
