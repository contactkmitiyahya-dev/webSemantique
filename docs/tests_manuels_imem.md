# Tests manuels – tranche d'Imem (formations, parcours, recherche)

Passés le 27/10/2026 sur la branche `imem` (données d'Ala et d'Imem chargées) : `load_data.py --reset`,
back-end, front-end. Les mêmes parcours sont rejoués automatiquement par un script Playwright (navigateur headless),
qui vérifie aussi que les listes d'Ala (formateurs, personnel, organismes, domaines) marchent avec le DataTable d'Imem.

| # | Page | Étapes | Résultat attendu | Obtenu |
|---|---|---|---|---|
| 1 | Catalogue `/formations` | Ouvrir la page | 14 formations, 10 par page, pagination 1/2 | OK |
| 2 | Catalogue | Coût max = 1000 | 9 résultats, l'URL contient `cout_max=1000` | OK |
| 3 | Catalogue | Clic sur l'en-tête « Coût » | Tri croissant, formations gratuites en tête ; 2e clic : décroissant | OK |
| 4 | Catalogue | Niveau = Avancé + Coût max 1000 | Spécialisation Angular, Développement back-end | OK |
| 5 | Catalogue | État = Inactives | Bootcamp Git et agilité, Bootcamp Node.js (badge « inactive ») | OK |
| 6 | Catalogue | « À venir seulement » | Aucune formation déjà commencée | OK |
| 7 | Catalogue | Ouvrir « Requête SPARQL envoyée à Fuseki » | La requête contient les FILTER des filtres choisis | OK |
| 8 | Fiche `/formations/Formation_FullStack` | Ouvrir | 5 modules, 2 inscrits (Ahmed, Sarra), places 28 / 30, certification ; « EduParcours Académie » ouvre la fiche organisme d'Ala | OK |
| 9 | Formulaire `/formations/nouvelle` | Enregistrer à vide | « L'intitulé est obligatoire », rien n'est envoyé | OK |
| 10 | Formulaire | Intitulé + module, sans domaine | « Choisir au moins un domaine » | OK |
| 11 | Formulaire | Formulaire complet | Redirection vers `/formations/Formation_Atelier_E2E_Vue` | OK |
| 12 | Formulaire (modifier) | Modifier, coût = 0 | Champs pré-remplis ; la fiche affiche « Gratuit » | OK |
| 13 | Fiche | Supprimer → Annuler | Rien n'est supprimé | OK |
| 14 | Fiche | Supprimer → Confirmer | Retour au catalogue + notification « supprimée » | OK |
| 15 | Parcours `/parcours` | Ouvrir | 9 parcours avec nombre de modules, d'apprenants, animateurs | OK |
| 16 | Fiche parcours `Parcours_Frontend_Complet` | Ouvrir | Étapes : CSS, HTML (0 prérequis), JavaScript (1), React (2) | OK |
| 17 | Formulaire parcours | Créer « Parcours E2E » avec Module Git, puis supprimer | Création puis suppression avec confirmation | OK |
| 18 | Recherche `/recherche?q=react` | Ouvrir | 7 résultats dans 7 catégories différentes | OK |
| 19 | Swagger `POST /api/nlp/question` | « Quelles formations coûtent moins de 1000 dinars ? » | Intention FILTRE_COUT, 9 lignes, requête SPARQL renvoyée | OK |
| 20 | Catalogue (mobile 390 px) | Ouvrir | Pas de défilement horizontal de la page | OK |

Automatisés : `python -m pytest backend/tests/test_imem.py -q` → 42 tests, dont les 12 questions d'Imem de
`docs/questions_types.csv` (12/12 intentions, 12/12 entités, 12/12 requêtes avec résultat). Les tests d'Ala
(`test_ala.py`) passent aussi avec `utils.py` et `intents.py` d'Imem.
