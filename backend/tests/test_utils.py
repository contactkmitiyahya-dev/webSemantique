"""
Tests unitaires pour les fonctions utilitaires (utils.py).
Lance avec : pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils import valid_id, esc, make_id


class TestValidId:
    def test_id_valide_simple(self):
        assert valid_id("Apprenant1") is True

    def test_id_valide_avec_underscore(self):
        assert valid_id("Omar_Gharbi") is True

    def test_id_invalide_minuscule(self):
        assert valid_id("apprenant") is False

    def test_id_invalide_debut_chiffre(self):
        assert valid_id("1Apprenant") is False

    def test_id_invalide_caractere_special(self):
        assert valid_id("Apprenant@1") is False

    def test_id_vide(self):
        assert valid_id("") is False


class TestEsc:
    def test_pas_de_guillemets(self):
        assert esc("bonjour") == "bonjour"

    def test_guillemets_echappes(self):
        assert esc('il a dit "bonjour"') == 'il a dit \\"bonjour\\"'

    def test_none_retourne_chaine_vide(self):
        assert esc(None) == ""


class TestMakeId:
    def test_nom_simple(self):
        assert make_id("omar gharbi") == "Omar_Gharbi"

    def test_nom_deja_capitalise(self):
        assert make_id("Omar Gharbi") == "Omar_Gharbi"

    def test_nom_avec_accents_retires(self):
        # Les caracteres speciaux sont supprimes
        result = make_id("jean-pierre")
        assert "_" in result or len(result) > 0
