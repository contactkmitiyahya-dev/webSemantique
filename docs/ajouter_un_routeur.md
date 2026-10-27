# Ajouter un routeur en 10 minutes

Modèle complet : `backend/app/routers/technologies.py`. C'est le plus court des trois routeurs de Linda (liste, types, détail, POST, PUT, DELETE). Copiez-le et suivez les étapes.

## 1. Copier le modèle (1 min)

```bash
cp backend/app/routers/technologies.py backend/app/routers/organismes.py
```

Dans le fichier : remplacez `Technologie` par votre classe (`Organisme`) et le préfixe d'identifiant `"Tech"` par le vôtre (`"Org"`).

## 2. Les outils déjà prêts (`backend/app/sparql_outils.py`)

| Fonction | Rôle |
|---|---|
| `exiger_instance(id, "Organisme")` | 400 si l'id est mal formé, 404 s'il n'est pas de cette classe ou d'une sous-classe |
| `exiger_instances(ids, "Formation")` | les ids liés doivent exister (sinon 400) |
| `exiger_sous_classe(type, "Organisme")` | refuse un type qui n'est pas une sous-classe (400) |
| `existe(id)` | pour renvoyer 409 à la création |
| `generer_id("Org", libelle)` | « Université de Sfax » → `Org_Universite_De_Sfax` |
| `lit(texte)` / `lit_date(iso)` | littéraux échappés (anti-injection) / `xsd:dateTime` validé |
| `relations("?x edu:proposeFormation edu:ID .")` | liste `[{id, label}]` pour la fiche |
| `sous_classes("Organisme")` | options des listes déroulantes de type |
| `type_direct(id, "Organisme")` | type le plus précis de l'individu |
| `compter(where)`, `pagination(page, taille)` | `total` et `LIMIT/OFFSET` du contrat `{total, donnees}` |
| `supprimer_individu(id)` | DELETE : triplets sortants puis entrants |

## 3. Adapter (5 min)

1. Le modèle Pydantic `…In` : vos champs.
2. `_valider()` : vos contraintes (bornes, relations obligatoires…). Levez `HTTPException(400, …)`.
3. `_triplets()` : les triplets à insérer. Les chaînes passent **toujours** par `lit()`, les ids par `verifier_id()` / `exiger_instances()`.
4. Dans le PUT : un `DELETE WHERE` par propriété gérée (et par inverse), puis `INSERT DATA`.
5. Dans le détail : une ligne `relations(...)` par relation. Pour une relation portée par l'autre classe, utilisez `^` ou `|` (voir `docs/memo_sparql.md`).

**Attention à l'ordre des routes** : `/types`, `/statistiques`, etc. doivent être déclarées **avant** `/{id}`.

## 4. Brancher (1 min) dans `backend/app/main.py`

```python
from .routers import organismes
app.include_router(organismes.router, prefix="/api/organismes", tags=["Organismes"])
```

## 5. Vérifier (3 min)

- Ouvrez http://localhost:8000/docs : vos routes apparaissent et se testent dans Swagger.
- Écrivez les tests dans `backend/tests/test_<prenom>.py`, sur le modèle de `test_linda.py` : un test par route, plus 409, 404 et 400.
- Lancez `pytest tests/test_<prenom>.py -v`.

## Contrat d'API (rappel)

| Méthode | Code | Corps |
|---|---|---|
| GET liste | 200 | `{"total", "page", "taille", "donnees": [...]}` |
| GET détail | 200 / 404 | propriétés + relations `[{id, label}]` |
| POST | 201 / 400 / 409 | la fiche créée |
| PUT | 200 / 400 / 404 | la fiche modifiée |
| DELETE | 204 / 404 / 409 | rien |
| Erreur | – | `{"detail": "message"}` |
