"""
Fonctions utilitaires : validation d'ID, echappement SPARQL et generation d'IDs.
"""

import re


def valid_id(identifiant: str) -> bool:
    """Valide un identifiant SPARQL : lettres/chiffres/underscores, debut par majuscule."""
    return bool(re.match(r"^[A-Z][a-zA-Z0-9_]*$", identifiant))


def esc(text: str) -> str:
    """Echappe les guillemets doubles pour eviter les injections SPARQL."""
    if text is None:
        return ""
    return text.replace('"', '\\"')


def make_id(nom: str) -> str:
    """
    Genere un identifiant propre depuis un nom libre.
    Exemple : 'omar gharbi' -> 'Omar_Gharbi'
    """
    nom_propre = re.sub(r'[^a-zA-Z0-9\s]', '', nom).strip()
    return "_".join([mot.capitalize() for mot in nom_propre.split()])
