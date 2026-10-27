import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==========================================
# 1. Tests de base (Santé et Liste)
# ==========================================

def test_sante():
    response = client.get("/api/sante")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_liste_apprenants():
    response = client.get("/api/apprenants")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "donnees" in data

def test_recherche_apprenant():
    response = client.get("/api/apprenants?q=Gharbi")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

def test_stats_apprenants():
    response = client.get("/api/apprenants/stats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# ==========================================
# 2. Tests de Détail et d'Erreur (404)
# ==========================================

def test_detail_apprenant_existant():
    response = client.get("/api/apprenants/Omar")
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "Gharbi"

def test_detail_apprenant_inexistant():
    response = client.get("/api/apprenants/Apprenant_Inexistant_123")
    assert response.status_code == 404

# ==========================================
# 3. Tests de Création (Conflit 409)
# ==========================================

def test_creation_apprenant_existant():
    payload = {
        "id": "Ahmed",
        "nom": "Test", "prenom": "Test", "email": "test@test.com", 
        "niveauEtudes": "Licence", "dateNaissance": "2000-01-01T00:00:00"
    }
    response = client.post("/api/apprenants", json=payload)
    assert response.status_code == 409
    assert "existe" in response.json()["detail"].lower()

# ==========================================
# 4. Tests de la contrainte OWL (Limite de 3 inscriptions)
# ==========================================

def test_limite_inscriptions():
    """
    Pour être fiable, on crée un apprenant de test, on l'inscrit 3 fois,
    on vérifie que la 4ème renvoie 409, puis on le supprime.
    """
    test_id = "Apprenant_Test_Limite"
    
    # 1. Nettoyage préventif au cas où le test aurait échoué avant
    client.delete(f"/api/apprenants/{test_id}")

    # 2. Création de l'apprenant
    payload = {
        "id": test_id,
        "nom": "Test", "prenom": "Limite", "email": "limite@test.com", 
        "niveauEtudes": "Licence", "dateNaissance": "2000-01-01T00:00:00"
    }
    resp_creation = client.post("/api/apprenants", json=payload)
    assert resp_creation.status_code == 201

    # 3. On l'inscrit 3 fois à des formations existantes
    client.post(f"/api/apprenants/{test_id}/inscription", params={"formation_id": "Formation_FullStack"})
    client.post(f"/api/apprenants/{test_id}/inscription", params={"formation_id": "Formation_Frontend"})
    client.post(f"/api/apprenants/{test_id}/inscription", params={"formation_id": "Formation_Backend"})

    # 4. La 4ème inscription doit échouer avec un code 409
    response_4eme = client.post(
        f"/api/apprenants/{test_id}/inscription", 
        params={"formation_id": "BootCamp_Web"}
    )
    
    # 5. Nettoyage (suppression de l'apprenant de test)
    client.delete(f"/api/apprenants/{test_id}")

    # 6. Vérification de l'erreur 409
    assert response_4eme.status_code == 409
    assert "Limite" in response_4eme.json()["detail"] or "limite" in response_4eme.json()["detail"]

# ==========================================
# 5. Test de Suppression
# ==========================================

def test_suppression_apprenant_inexistant():
    response = client.delete("/api/apprenants/Apprenant_Inexistant_XYZ")
    assert response.status_code in [200, 404]

# ==========================================
# 6. Tests du Module NLP
# ==========================================

def test_nlp_exemples():
    response = client.get("/api/nlp/exemples")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8

def test_nlp_question_niveau():
    response = client.post("/api/nlp/question", json={"question": "Quels sont les apprenants de niveau Master ?"})
    assert response.status_code == 200
    data = response.json()
    assert data["intention"] == "APPRENANTS_NIVEAU"
    assert "sparql" in data
    assert "resultats" in data
    assert "SELECT" in data["sparql"]

def test_nlp_question_compter():
    response = client.post("/api/nlp/question", json={"question": "Combien y a-t-il d'apprenants en tout ?"})
    assert response.status_code == 200
    data = response.json()
    assert data["intention"] == "COMPTER_APPRENANTS"
    assert "COUNT" in data["sparql"]

def test_nlp_question_compter_certifications():
    response = client.post("/api/nlp/question", json={"question": "combien y a-t-il de certifications en tout"})
    assert response.status_code == 200
    data = response.json()
    assert data["intention"] == "COMPTER_CERTIFICATIONS"
    assert "Certification" in data["sparql"]
    assert "resultats" in data
    # La valeur retournée doit être 6 (ou 6 en string)
    assert any("6" in str(v) for row in data["resultats"] for v in row.values())
