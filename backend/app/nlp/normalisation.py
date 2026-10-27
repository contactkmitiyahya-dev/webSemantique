"""Étape 1 du pipeline NLP : normalisation du texte (Ala).

normaliser("Qui enseigne le cours React ?") -> "qui enseigner le cours react"

Ordre : minuscules -> lemmatisation spaCy (sans la ponctuation) -> suppression
des accents -> nettoyage des caractères restants -> espaces multiples réduits.
Les accents sont retirés APRÈS la lemmatisation, car spaCy reconnaît mieux
les mots accentués (« enseigné » -> « enseigner »).
"""
import logging
import re
import unicodedata

log = logging.getLogger("nlp")

_nlp = None          # modèle spaCy, chargé une seule fois
_spacy_ok = None     # None = pas encore essayé, True / False ensuite


def _charger_spacy():
    """Charge fr_core_news_md au premier appel ; renvoie None si indisponible."""
    global _nlp, _spacy_ok
    if _spacy_ok is None:
        try:
            import spacy
            # parser et ner inutiles ici : on ne garde que ce qui sert au lemmatiseur
            _nlp = spacy.load("fr_core_news_md", disable=["parser", "ner"])
            _spacy_ok = True
        except (ImportError, OSError) as e:
            log.warning("spaCy ou fr_core_news_md indisponible (%s) : "
                        "normalisation sans lemmatisation.", e)
            _spacy_ok = False
    return _nlp


def sans_accents(texte: str) -> str:
    """« prérequis » -> « prerequis » (décomposition Unicode puis retrait des accents)."""
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def normaliser(texte: str, lemmes: bool = True) -> str:
    """Renvoie le texte en minuscules, lemmatisé, sans accents ni ponctuation."""
    texte = texte.lower()

    nlp = _charger_spacy() if lemmes else None
    if nlp is not None:
        doc = nlp(texte)
        texte = " ".join(t.lemma_.lower() for t in doc if not t.is_punct and not t.is_space)

    texte = sans_accents(texte)
    texte = re.sub(r"[^a-z0-9]+", " ", texte)   # ponctuation, apostrophes, symboles -> espace
    return re.sub(r"\s+", " ", texte).strip()
