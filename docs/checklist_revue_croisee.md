# Check-list de revue croisée — EduParcours

Written for : le membre de l'équipe qui teste la tranche d'un autre (Imem teste Zahra, Zahra teste Linda).

Cocher chaque point, et signaler les échecs avec une fiche de bogue (`docs/fiche_bogue.md`).

## Données

- [ ] `python scripts/verify.py` affiche « tout est correct ».
- [ ] Les individus de la tranche ont un type et un nom (`rdfs:label` ou `edu:nom`).

## API (Swagger : http://localhost:8000/docs)

- [ ] `GET` de liste renvoie `{ "total": n, "donnees": [...] }`.
- [ ] Un id inconnu renvoie 404, avec le message `{ "detail": "..." }`.
- [ ] Un id avec un caractère interdit (tiret, espace) renvoie 400.
- [ ] `POST` valide renvoie 201 avec l'id créé.
- [ ] `POST` avec un élément lié inconnu (module, formateur, prérequis) renvoie 400.
- [ ] `DELETE` renvoie 204, puis `GET` du même id renvoie 404.
- [ ] Un module qui a des cours ou des dépendants ne peut pas être supprimé (409).
- [ ] Un prérequis qui crée un cycle est refusé (400).

## Front (http://localhost:5173)

- [ ] Les listes affichent les éléments et la pagination fonctionne.
- [ ] La recherche et les filtres renvoient les bons résultats, et « Réinitialiser » remet tout à zéro.
- [ ] La fiche affiche tous les champs et les liens sont cliquables.
- [ ] Le formulaire de création refuse un champ vide, et la modification met bien à jour la fiche.
- [ ] Le bouton « Supprimer » demande une confirmation avant d'agir.

## Questions (NLP)

- [ ] Les 8 questions de `docs/questions_types.csv` donnent la bonne intention.
- [ ] Une question hors sujet renvoie `INCONNUE`.
- [ ] Une entité manquante renvoie un message clair, sans erreur 500.

## Tests automatiques

- [ ] `python -m pytest tests -v` passe dans le dossier `backend`.
