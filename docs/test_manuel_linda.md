# Test de bout en bout – tranche Linda

Date : 27/10/2026. Poste de Linda.
- Fuseki 6.2.0 (Java 21), dataset `eduparcours` : ontologie (3087 triplets) + `membre_linda.ttl`, soit 3220 triplets.
- API : `uvicorn app.main:app --port 8000`.
- Front : `npm run dev`, port 5173.

## 1. Scénario rejoué par l'API, avec l'origine du front (`Origin: http://localhost:5173`)

Chaque étape correspond à une action dans les pages. Le contrôle est fait directement dans Fuseki.

| N° | Action (page) | Vérification | Résultat |
|---|---|---|---|
| 1 | Compétences > Nouvelle compétence : « Tests E2E Cypress », type CompetenceJavaScript, parent JavaScript, équivalente à POO JavaScript, technologie JavaScript | POST 201, id généré `Comp_Tests_E2e_Cypress`, en-tête CORS présent | ✅ |
| 2 | – | Fuseki : 8 triplets sortants (2 types, label, intitulé, score, parent, équivalence, technologie) | ✅ |
| 3 | – | Fuseki : `Comp_POO_JavaScript estEquivalenteA Comp_Tests_E2e_Cypress` (sens inverse écrit) | ✅ |
| 4 | Compétences > onglet Arbre | La compétence apparaît sous Programmation Web > JavaScript | ✅ |
| 5 | Modifier JavaScript en lui donnant la nouvelle compétence comme parent | 400 « Cycle refusé » | ✅ |
| 6 | Évaluations > Nouvelle évaluation « Quiz E2E » sur cette compétence, module JavaScript | POST 201 | ✅ |
| 7 | Évaluations : filtre module JavaScript + après le 01/05/2027 | Quiz E2E dans la liste | ✅ |
| 8 | Supprimer la compétence | 409 : l'évaluation n'aurait plus de compétence | ✅ |
| 9 | Barre de question : « Quelles sont les sous-compétences de JavaScript ? » | SOUS_COMPETENCES, entité JavaScript, la nouvelle compétence est dans les résultats (le dictionnaire NLP est rechargé à chaque question) | ✅ |
| 10 | Supprimer l'évaluation | 204 | ✅ |
| 11 | Supprimer la compétence | 204 | ✅ |
| 12 | – | Fuseki : aucun triplet sortant ni entrant restant ; total revenu à 3220 | ✅ |

## 2. Tests automatiques dans le même environnement

| Commande | Résultat |
|---|---|
| `cd backend && venv\Scripts\python -m pytest tests/ -q` | 78 passent (53 Linda, 25 Yahya) |
| `python scripts/eval_nlp.py` | 94 % d'intentions, 100 % de requêtes (18 questions) |
| HermiT (owlready2) sur ontologie + `membre_linda.ttl` | Cohérent. Le contre-test (Comp_GraphQL typée aussi CompetenceREST, classes disjointes) est bien détecté comme incohérent |
| `npm run build` et `oxlint` sur `pages/linda` et `components` | Build OK, aucun avertissement |

## 3. Vérification visuelle à faire dans le navigateur (http://localhost:5173)

À cocher par Linda :

- [ ] Menu : Compétences, Technologies, Évaluations visibles ; barre de question sous le menu
- [ ] Compétences : recherche « sql », filtre type, score minimal, pagination « Page 1 / 3 »
- [ ] Onglet Arbre : déplier Programmation Web > Programmation back-end > Conception d'API > GraphQL
- [ ] Onglet « Les plus répandues » : HTML en tête (7 apprenants), puis JavaScript (6) et CSS (5)
- [ ] Fiche Programmation back-end : « 9 au total », modules pour l'acquérir, bouton « + Sous-compétence » (fenêtre modale)
- [ ] Supprimer Autonomie : boîte de confirmation, puis notification rouge (409)
- [ ] Technologies : filtre « Technologie outil » → Git, Docker, GitHub Actions
- [ ] Évaluations : bouton « À venir », dates futures en vert, graphique des moyennes par type
- [ ] Formulaire évaluation sans compétence : message « Choisissez au moins une compétence »
- [ ] Barre de question : « Quelles sont les compétences équivalentes à Reakt ? » → Vue.js et Angular, bouton « Voir la requête SPARQL »
