# Hackathon Flash Trading — Carnet d'Ordres

Bienvenue ! Votre objectif est de construire un moteur de carnet d'ordres performant et déterministe, qui évolue à travers 6 paliers de complexité croissante.

## Démarrage rapide

### Prérequis
- Python 3.11+

### Installation

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/MacOS
# OU .\venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

## Guide de participation

### 1. Enregistrer votre équipe

Ajoutez une entrée dans `config/teams.yaml` :

```yaml
teams:
  - id: nom_de_votre_equipe
    members:
      - "Prénom Nom 1"
      - "Prénom Nom 2"
```

### 2. Structure de répertoire

```
submissions/
└── nom_de_votre_equipe/
    ├── __init__.py
    ├── level1.py
    ├── level2.py
    └── ...
```

Copiez `submissions/_template/` comme point de départ.
Consultez `submissions/example_team/` pour une implémentation de référence.

### 3. Les paliers

Tous les paliers utilisent la même signature :

```python
def process_orders(initial_book: MultiBook, orders: Iterable[Order]) -> MultiBook:
```

| Palier | Concept | Nouveautés |
|--------|---------|------------|
| 1 | Ordres limite de base | Ordres LIMIT, priorité prix-temps |
| 2 | Ordres au marché | Ordres MARKET (non placés si non exécutés) |
| 3 | Annulation et modification | CANCEL supprime ; AMEND = annuler + réinsérer |
| 4 | IOC et FOK | IOC exécute puis annule le reste ; FOK tout-ou-rien |
| 5 | Ordres iceberg | `visible_quantity` cache la profondeur ; rechargement automatique |
| 6 | Enchère de clôture | LOC/MOC en file jusqu'au CLOSE → décroisement max-volume |

Voir `docs/levels.md` pour les spécifications complètes.

### 4. Workflow

1. **Implémenter** : écrivez votre solution dans `submissions/<votre_equipe>/level1.py` jusqu'à `level6.py`.
2. **Tester localement** : `make test` pour valider sur les tests publics.
3. **Soumettre** : `git commit` puis `git push`. Une CI vérifiera automatiquement vos tests publics et affichera un badge ✓/✗ sur votre commit.

## Lancer les tests

```bash
# Tous les tests publics
make test

# Un palier spécifique
make test-level LEVEL=3

# Afficher l'aide
make
```

## Notation

Les équipes sont classées par :
1. **Palier le plus élevé réussi** (les paliers 1 à N doivent tous passer consécutivement)
2. **Nombre total de fixtures réussies** (départage)

## Règles

1. **Déterminisme** : votre moteur doit être déterministe. Pas de graine aléatoire ni d'heure système.
2. **Performance** : chaque fixture a un timeout de 5 secondes.
3. **Pas de secrets** : ne commitez pas de clés API ou autres secrets.
4. **Style de code** : PEP 8 recommandé.

## Dépannage

- Vérifiez le message d'erreur dans la sortie des tests.
- Assurez-vous que votre implémentation gère les cas limites (exécutions partielles, carnets vides).
- Consultez `submissions/_template/` pour les signatures de fonctions correctes.
- Lisez `docs/levels.md` pour les spécifications détaillées.

Bonne chance !
