# Configurateur de Devis

Application de bureau (PyQt6) permettant la création et le suivi de devis commerciaux entre vendeurs et clients.

## Fonctionnalités

- **Interface Vendeur** : gestion des affaires, création de devis avec produits/options, réponse aux clients, clôture d'affaires, export PDF.
- **Interface Client** : inscription par SIRET (validé via API gouv.fr), ouverture d'affaires, consultation et réponse aux devis reçus.
- **Lanceur** : fenêtre de lancement permettant d'ouvrir l'une ou les deux interfaces.
- **Sécurité** : mots de passe hashés (PBKDF2-SHA256, 100 000 itérations), requêtes SQL paramétrées, validation SIRET (format + Luhn + API).

## Architecture

```
main.py                  # Point d'entrée — lanceur
client_app.py            # Fenêtre principale client
vendeur_app.py           # Fenêtre principale vendeur
src/
├── constants/           # Constantes métier, statuts, PDF
├── controllers/         # Logique applicative (BaseController → Client/Vendeur)
├── models/
│   ├── database.py      # Schéma SQLite, migrations
│   ├── db_manager.py    # Facade (DatabaseManager)
│   └── repositories/    # Accès données (Auth, Affaire, Devis, Produit)
├── utils/               # Authentification, PDF, session, validation SIRET
└── views/               # Fenêtres, dialogues, widgets, thème sombre
tests/                   # Tests unitaires et d'intégration (pytest)
```

**Patterns** : MVC, Repository, Facade, Template Method.

## Prérequis

- Python 3.12+
- Système : Linux, macOS ou Windows

## Installation

```bash
git clone https://github.com/Esiakot/devis.git
cd devis
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Stack technique

| Composant       | Technologie              |
|-----------------|--------------------------|
| Interface       | PyQt6                    |
| Base de données | SQLite                   |
| Export PDF      | fpdf                     |
| Tests           | pytest                   |
| CI              | GitHub Actions           |
| Langage         | Python 3.13              |

## Licence

Projet réalisé dans le cadre du BTS SIO option SLAM.
