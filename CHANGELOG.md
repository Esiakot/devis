# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

## [1.1.0] - 2026-03-18

### Ajouté
- Suite de tests unitaires et d'intégration (71 tests pytest)
  - Tests authentification : hachage, vérification, force du mot de passe
  - Tests validation SIRET : format, algorithme de Luhn
  - Tests repositories : AuthRepo, AffaireRepo, DevisRepo, ProduitRepo
  - Tests controllers : VendeurController, ClientController
  - Tests constantes métier et helpers de statuts
- Intégration continue avec GitHub Actions (Python 3.12 / 3.13)
- Fichier `.gitignore`
- Fichier `README.md` avec documentation du projet
- Ce fichier `CHANGELOG.md`

## [1.0.0] - 2026-03-17

### Ajouté
- Lanceur principal avec choix d'interface (Client / Vendeur / Les deux)
- Interface Vendeur : connexion, gestion des affaires, création de devis, réponse, clôture, export PDF
- Interface Client : inscription par SIRET (validation format + Luhn + API gouv.fr), ouverture d'affaires, consultation et réponse aux devis
- Architecture MVC avec patterns Repository, Facade, Template Method
- Base de données SQLite (11 tables, données de démonstration)
- Sécurité : PBKDF2-SHA256 (100k itérations), requêtes paramétrées
- Génération de devis PDF (fpdf)
- Thème sombre avec palettes par application
