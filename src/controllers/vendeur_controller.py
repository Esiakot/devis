# ──────────────────────────────────────────────────────────────────────────────
# src/controllers/vendeur_controller.py — Contrôleur VENDEUR
# ──────────────────────────────────────────────────────────────────────────────
# Logique métier spécifique à l'interface vendeur. Étend BaseController avec
# l'enregistrement des réponses du vendeur (acceptation, refus, contre-
# propositions avec prix et poids), la création de nouvelles versions de devis,
# et la clôture des affaires (gagnée, perdue, annulée) avec génération d'un
# devis FINAL si l'affaire est gagnée.
# ──────────────────────────────────────────────────────────────────────────────

from src.controllers.base_controller import BaseController
from src.models.db_manager import DatabaseManager


class VendeurController(BaseController):

    def __init__(self, db: DatabaseManager):
        super().__init__(db)

    # --- Authentification ---
    def authentifier(self, username, password):
        """Authentifie un vendeur. Returns dict info ou None."""
        return self.db.authentifier_vendeur(username, password)

    def creer_compte_vendeur(self, username, password, nom, prenom, email=""):
        """Crée un compte vendeur. Returns vendeur_id ou None."""
        return self.db.creer_vendeur(username, password, nom, prenom, email)

    def username_existe(self, username):
        """Vérifie si un nom d'utilisateur existe déjà."""
        return self.db.username_existe(username)

    def get_vendeur_par_id(self, vendeur_id):
        """Récupère les infos vendeur par ID."""
        return self.db.get_vendeur_par_id(vendeur_id)

    # --- Réponses vendeur ---
    def sauvegarder_reponses_vendeur(self, devis_id, reponses):
        """Enregistre les réponses du vendeur et crée une nouvelle version.

        Returns (new_id, new_version) or (None, None)
        """
        for rep in reponses:
            prix = rep.get('prix') if rep['statut'] == 'contre_proposition' else None
            if rep['type'] == 'standard':
                self.db.repondre_option_standard(rep['id'], rep['statut'], prix, rep['commentaire'])
            else:
                poids = rep.get('poids', 0)
                self.db.repondre_option_perso(rep['id'], rep['statut'], prix, rep['commentaire'], poids)

        return self.db.creer_nouvelle_version_devis(devis_id, 'vendeur')

    # --- Clôture ---
    def cloturer_affaire(self, affaire_id, resultat, commentaire=""):
        """Clôture l'affaire. Crée un devis FINAL si gagnée.

        Returns dict: success, final_id, final_version
        """
        final_id = None
        final_version = None

        if resultat == 'gagne':
            devis_list = self.db.get_devis_affaire(affaire_id)
            if devis_list:
                dernier_devis_id = devis_list[-1][0]
                final_id, final_version = self.db.creer_nouvelle_version_devis(dernier_devis_id, 'FINAL')

        success = self.db.cloturer_affaire(affaire_id, resultat, commentaire)
        return {'success': success, 'final_id': final_id, 'final_version': final_version}
