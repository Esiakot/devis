# ──────────────────────────────────────────────────────────────────────────────
# src/controllers/client_controller.py — Contrôleur CLIENT
# ──────────────────────────────────────────────────────────────────────────────
# Logique métier spécifique à l'interface acheteur. Étend BaseController avec
# la création d'affaires (validation, gestion des clients), la soumission de
# devis (validation du poids des produits, calcul des totaux), et le traitement
# des réponses de l'acheteur aux contre-propositions du vendeur.
# ──────────────────────────────────────────────────────────────────────────────

from src.controllers.base_controller import BaseController
from src.models.db_manager import DatabaseManager
from src.constants import POIDS_LIMITE_POURCENTAGE


class ClientController(BaseController):

    def __init__(self, db: DatabaseManager):
        super().__init__(db)
        self.client_id = None  # Défini après inscription

    # --- Authentification client ---
    def authentifier_client(self, username, password):
        """Authentifie un client. Returns dict info ou None."""
        return self.db.authentifier_client(username, password)

    def creer_compte_client(self, username, password, nom_societe, siret,
                            contact_nom, contact_prenom, contact_service,
                            contact_email, contact_telephone, indicatif_tel):
        """Crée un compte client. Returns client_id ou None."""
        return self.db.creer_client(
            username, password, nom_societe, siret,
            contact_nom, contact_prenom, contact_service,
            contact_email, contact_telephone, indicatif_tel)

    def client_username_existe(self, username):
        return self.db.client_username_existe(username)

    def client_siret_existe(self, siret):
        return self.db.client_siret_existe(siret)

    def get_client_par_id(self, client_id):
        """Récupère les infos client par ID."""
        return self.db.get_client_par_id(client_id)

    # --- Inscription client ---
    def inscrire_client(self, societe, nom, prenom, service, email, tel, siret):
        """Inscrit ou retrouve un client par SIRET. Returns client_id."""
        return self.db.creer_ou_obtenir_client(
            societe, nom, prenom, service, email, tel, siret)

    def get_client_par_siret(self, siret):
        """Recherche un client par numéro SIRET."""
        return self.db.get_client_par_siret(siret)

    # --- Affaires (filtrées par client connecté) ---
    def get_affaires(self):
        """Retourne uniquement les affaires du client connecté."""
        if self.client_id:
            return self.db.get_affaires_client(self.client_id)
        return self.db.get_liste_affaires()

    # --- Affaires ---
    def creer_affaire(self, data: dict):
        """Valide, crée le client si besoin, puis crée l'affaire.
        Returns (affaire_id, numero, error_msg). error_msg is None on success.
        """
        if not data['titre']:
            return None, None, "Le titre du projet est requis."

        client_id = data.get('client_id', self.client_id)
        if not client_id:
            return None, None, "Client non identifié."

        affaire_id, numero = self.db.creer_affaire(client_id, data['titre'], data.get('description', ''))
        return affaire_id, numero, None

    # --- Devis ---
    def valider_et_soumettre(self, affaire_id, produit_widgets, produits_data, commentaire):
        """Valide le poids, puis crée le devis.

        Returns dict:
            error: str | None — message d'erreur si validation échouée
            devis_id, version: si succès
        """
        if not affaire_id:
            return {'error': "Sélectionnez d'abord une affaire."}
        if not produits_data:
            return {'error': "Ajoutez au moins un produit."}

        for i, w in enumerate(produit_widgets):
            if not w.is_poids_valide():
                pd = w.combo_modele.currentData()
                nom = pd[1] if pd else f"Produit #{i+1}"
                charge_max = pd[3] if pd and len(pd) > 3 else 1000
                poids = w.calculer_poids_total()
                limite = charge_max * POIDS_LIMITE_POURCENTAGE
                return {'error': (
                    f"Le produit '{nom}' dépasse la limite de charge.\n\n"
                    f"Charge: {poids:.1f} kg | Limite: {limite:.1f} kg | Max: {charge_max:.1f} kg\n\n"
                    f"Veuillez retirer des options.")}

        devis_id, version = self.db.creer_devis_pour_affaire(
            affaire_id, produits_data, notes=commentaire)
        return {'error': None, 'devis_id': devis_id, 'version': version}

    def soumettre_devis(self, affaire_id, produits_data, commentaire):
        """Crée un devis pour l'affaire. Returns (devis_id, version)."""
        return self.db.creer_devis_pour_affaire(affaire_id, produits_data, notes=commentaire)

    def sauvegarder_reponses_acheteur(self, devis_id, reponses, auto_adoptes):
        """Enregistre les réponses de l'acheteur. Gère la conclusion automatique.

        Returns dict:
            concluded: bool — True si l'affaire a été conclue
            final_id, final_version: si concluded
            new_id, new_version: si pas concluded
        """
        for auto in auto_adoptes:
            if auto['type'] == 'standard':
                self.db.repondre_option_standard_acheteur(auto['id'], 'accepte', "")
            else:
                self.db.repondre_option_perso_acheteur(auto['id'], 'accepte', "")

        toutes_decidees = True
        for rep in reponses:
            if rep['type'] == 'standard':
                self.db.repondre_option_standard_acheteur(rep['id'], rep['statut'], rep['commentaire'])
            else:
                self.db.repondre_option_perso_acheteur(rep['id'], rep['statut'], rep['commentaire'])
            if rep['statut'] == 'en_attente':
                toutes_decidees = False

        if toutes_decidees:
            devis_info = self.db.get_devis_info(devis_id)
            affaire_id = devis_info[1] if devis_info else None
            if affaire_id:
                final_id, final_version = self.db.creer_nouvelle_version_devis(devis_id, 'FINAL')
                self.db.cloturer_affaire(affaire_id, 'gagne')
                return {'concluded': True, 'final_id': final_id, 'final_version': final_version}

        new_id, new_version = self.db.creer_nouvelle_version_devis(devis_id, 'acheteur')
        return {'concluded': False, 'new_id': new_id, 'new_version': new_version}
