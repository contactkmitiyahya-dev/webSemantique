"""Tests de la route POST /api/questions (Fuseki doit tourner sur le port 3030)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def poser(question: str) -> dict:
    r = client.post("/api/questions", json={"question": question})
    assert r.status_code == 200
    return r.json()


def test_question_prerequis():
    r = poser("Quels sont les prérequis du module Interactivité et dynamisme ?")
    assert r["intention"] == "PREREQUIS"
    assert "Module_Mise_En_Forme" in {p["id"] for p in r["reponse"]}


def test_question_cours_module():
    r = poser("Quels cours sont dans le Module HTML ?")
    assert r["intention"] == "COURS_MODULE"
    assert "Cours_Intro_HTML" in {c["id"] for c in r["reponse"]}


def test_question_niveau_cours():
    r = poser("Quel est le niveau du cours Introduction HTML ?")
    assert r["intention"] == "NIVEAU_COURS"
    assert r["reponse"] == "Débutant"


def test_question_techno_cours():
    r = poser("Quelles technologies sont utilisées dans le cours HTML5 sémantique et accessibilité ?")
    assert r["intention"] == "TECHNO_COURS"
    assert "Tech_HTML5" in {t["id"] for t in r["reponse"]}


def test_question_competences_module():
    r = poser("Quelles compétences faut-il pour suivre le module Mise en production ?")
    assert r["intention"] == "COMPETENCES_MODULE"
    assert "Comp_HTML" in {c["id"] for c in r["reponse"]}


def test_question_ressources_competence():
    r = poser("Quelles ressources existent pour la compétence HTML ?")
    assert r["intention"] == "RESSOURCES_COMPETENCE"
    assert "Video_HTML5_Intro" in {x["id"] for x in r["reponse"]}


def test_question_videos():
    r = poser("Quelles vidéos sont disponibles sur HTML ?")
    assert r["intention"] == "VIDEOS"
    assert {"Video_HTML5_Intro", "Video_Intro_HTML"} <= {v["id"] for v in r["reponse"]}


def test_question_suivant_module():
    r = poser("Quel est le module qui suit Interactivité et dynamisme ?")
    assert r["intention"] == "SUIVANT_MODULE"
    assert "Module_Architecture_MVC" in {m["id"] for m in r["reponse"]}


def test_question_inconnue():
    r = poser("Bonjour, comment ça va ?")
    assert r["intention"] == "INCONNUE"
