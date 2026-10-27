"""Tests de détection d'intention sur le jeu de questions docs/questions_types.csv."""

import csv
from pathlib import Path

from app.nlp.intentions import detecter_intention

FICHIER_QUESTIONS = Path(__file__).resolve().parents[2] / "docs" / "questions_types.csv"


def test_chaque_question_du_csv_donne_son_intention():
    with FICHIER_QUESTIONS.open(encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    assert len(lignes) == 8
    for ligne in lignes:
        assert detecter_intention(ligne["question"]) == ligne["intention"], ligne["question"]


def test_question_hors_sujet_est_inconnue():
    assert detecter_intention("Bonjour, comment ça va ?") == "INCONNUE"
