"""
Reconnaissance d'entites (tache NLP de Linda, reutilisable par tous) :
1. spaCy PhraseMatcher sur le texte normalise (correspondance exacte des libelles) ;
2. si rien n'est trouve, rapidfuzz sur les n-grammes de la question (fautes de frappe).

Usage :
    m = EntityMatcher()
    m.ajouter("Module React", "Module_React", "Module")
    m.trouver("prerequis du module reakt", types={"Module"})
"""

import re
import unicodedata

import spacy
from spacy.matcher import PhraseMatcher
from rapidfuzz import fuzz, process

# fuzz.ratio : « reakt » / « react » = 80 ; au-dela de 80 on accepte la correction.
# (WRatio est trop permissif ici : « module » obtiendrait 90 contre « module react ».)
SEUIL_FUZZY = 80

MOTS_VIDES = {
    "le", "la", "les", "l", "de", "des", "du", "d", "un", "une", "et", "a", "au", "aux",
    "en", "pour", "par", "sur", "dans", "quel", "quels", "quelle", "quelles", "est", "sont",
    "qui", "que", "qu", "ce", "ces", "il", "y", "on", "avec", "competence", "competences",
    "module", "modules", "evaluation", "evaluations", "technologie", "technologies",
}

_nlp = None


def get_nlp():
    """fr_core_news_md si installe (tokenisation, like_num), sinon un pipeline francais vide."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("fr_core_news_md", exclude=["ner", "parser"])
        except OSError:
            _nlp = spacy.blank("fr")
    return _nlp


def normaliser(texte: str) -> str:
    """Minuscules, sans accents, ponctuation remplacee par des espaces (« Node.js » -> « node js »)."""
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


class EntityMatcher:
    def __init__(self, synonymes: list = None):
        self.nlp = get_nlp()
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.entrees = {}  # (type, texte normalise) -> (uri, libelle)
        # synonymes : groupes de formes equivalentes, ex. ["node js", "nodejs", "node"]
        self.synonymes = [[normaliser(f) for f in groupe] for groupe in (synonymes or [])]

    def _variantes(self, cle: str) -> set:
        """« module nodejs » -> {« module nodejs », « module node js », « module node »}."""
        variantes = {cle}
        for groupe in self.synonymes:
            for forme in groupe:
                if re.search(rf"\b{re.escape(forme)}\b", cle):
                    variantes |= {re.sub(rf"\b{re.escape(forme)}\b", autre, cle) for autre in groupe}
        return variantes

    def ajouter(self, libelle: str, uri: str, type_: str) -> None:
        for cle in self._variantes(normaliser(libelle)):
            if not cle or (type_, cle) in self.entrees:
                continue
            self.entrees[(type_, cle)] = (uri, libelle)
            self.matcher.add(type_, [self.nlp.make_doc(cle)])

    def trouver(self, question: str, types: set) -> list:
        """Entites des types demandes : [{texte, uri, type, label, methode, score}], la plus longue d'abord."""
        doc = self.nlp.make_doc(normaliser(question))
        trouvees = []
        for match_id, debut, fin in self.matcher(doc):
            type_ = self.nlp.vocab.strings[match_id]
            span = doc[debut:fin].text
            if type_ in types and (type_, span) in self.entrees:
                uri, label = self.entrees[(type_, span)]
                trouvees.append({"texte": span, "uri": uri, "type": type_, "label": label,
                                 "methode": "exacte", "score": 100})
        if trouvees:
            # Garder les plus longues (« programmation web » plutot que « web »)
            return sorted(trouvees, key=lambda e: -len(e["texte"]))
        return self._approchee(doc, types)

    def _approchee(self, doc, types: set) -> list:
        choix = {cle: (t, cle) for (t, cle) in self.entrees if t in types}
        if not choix:
            return []
        mots = [t.text for t in doc]
        meilleur = None
        for n in range(4, 0, -1):
            for i in range(len(mots) - n + 1):
                gramme = mots[i:i + n]
                if gramme[0] in MOTS_VIDES or gramme[-1] in MOTS_VIDES:
                    continue
                texte = " ".join(gramme)
                if len(texte) < 4:
                    continue
                res = process.extractOne(texte, list(choix), scorer=fuzz.ratio, score_cutoff=SEUIL_FUZZY)
                if res and (meilleur is None or res[1] > meilleur[2]):
                    meilleur = (texte, res[0], res[1])
        if not meilleur:
            return []
        texte, cle, score = meilleur
        type_ = choix[cle][0]
        uri, label = self.entrees[(type_, cle)]
        return [{"texte": texte, "uri": uri, "type": type_, "label": label,
                 "methode": "approchee", "score": round(score)}]
