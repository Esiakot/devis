# ──────────────────────────────────────────────────────────────────────────────
# src/controllers/base_controller.py — Contrôleur de base (MVC)
# ──────────────────────────────────────────────────────────────────────────────
# Couche intermédiaire entre les vues et la base de données. Fournit les
# méthodes de lecture et d'écriture communes aux deux rôles (client et vendeur) :
# gestion des affaires, des devis, des commentaires, du catalogue produits et
# de la génération PDF. Les vues n'accèdent JAMAIS au DatabaseManager
# directement — elles passent systématiquement par ce contrôleur.
# ──────────────────────────────────────────────────────────────────────────────

import os
from src.models.db_manager import DatabaseManager
from src.utils.pdf_generator import generer_devis_pdf


class BaseController:
    """Méthodes de lecture/écriture communes aux deux rôles (client & vendeur)."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    # ─── Affaires ─────────────────────────────────────────────────
    def get_affaires(self):
        return self.db.get_liste_affaires()

    def get_affaire_details(self, affaire_id):
        return self.db.get_affaire_details(affaire_id)

    def is_affaire_cloturee(self, affaire_id):
        return self.db.is_affaire_cloturee(affaire_id)

    # ─── Clients ──────────────────────────────────────────────────
    def get_tous_clients(self):
        return self.db.get_tous_clients()

    # ─── Devis ────────────────────────────────────────────────────
    def get_devis(self, affaire_id):
        return self.db.get_devis_affaire(affaire_id)

    def get_devis_info(self, devis_id):
        return self.db.get_devis_info(devis_id)

    def get_devis_detail(self, devis_id):
        return self.db.get_options_devis_detail(devis_id)

    # ─── Commentaires ─────────────────────────────────────────────
    def get_commentaires(self, affaire_id):
        return self.db.get_commentaires_affaire(affaire_id)

    def envoyer_commentaire(self, affaire_id, auteur, role, contenu):
        return self.db.ajouter_commentaire(affaire_id, auteur, role, contenu)

    # ─── Catalogue produits (pour ProduitConfigWidget) ────────────
    def get_produits(self):
        return self.db.get_produits()

    def get_options_pour_produit(self, produit_id):
        return self.db.get_options_pour_produit(produit_id)

    # ─── PDF ──────────────────────────────────────────────────────
    def generer_pdf(self, devis_id, client_nom):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "generated_devis")
        return generer_devis_pdf(self.db, devis_id, client_nom=client_nom, output_dir=output_dir)
