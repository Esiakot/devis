# ──────────────────────────────────────────────────────────────────────────────
# src/models/repositories/__init__.py — Package des repositories
# ──────────────────────────────────────────────────────────────────────────────
# Réexporte les trois repositories de la couche d'accès aux données :
# ProduitRepository (catalogue), AffaireRepository (affaires, clients,
# commentaires) et DevisRepository (devis, options, versioning). Le découpage
# par domaine facilite la maintenance et la testabilité.
# ──────────────────────────────────────────────────────────────────────────────

from src.models.repositories.produit_repo import ProduitRepository
from src.models.repositories.affaire_repo import AffaireRepository
from src.models.repositories.devis_repo import DevisRepository
from src.models.repositories.auth_repo import AuthRepository
