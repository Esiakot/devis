# ──────────────────────────────────────────────────────────────────────────────
# src/models/db_manager.py — Facade DatabaseManager
# ──────────────────────────────────────────────────────────────────────────────
# Point d'entrée unique pour tout accès aux données. Instancie la connexion
# SQLite et les trois repositories (ProduitRepository, AffaireRepository,
# DevisRepository), puis expose une API unifiée en déléguant chaque appel
# au repository concerné. Les contrôleurs n'interagissent qu'avec cette facade.
# ──────────────────────────────────────────────────────────────────────────────

from src.models.database import Database
from src.models.repositories import ProduitRepository, AffaireRepository, DevisRepository, AuthRepository


class DatabaseManager:
    """Point d'entrée unique pour l'accès aux données. Délègue aux repositories."""

    def __init__(self, db_name="devis_database.db"):
        self._db = Database(db_name)
        self._produit = ProduitRepository(self._db.get_connection)
        self._affaire = AffaireRepository(self._db.get_connection)
        self._devis = DevisRepository(self._db.get_connection)
        self._auth = AuthRepository(self._db.get_connection)

    # ─── Produits ─────────────────────────────────────────────────
    def get_produits(self):
        return self._produit.get_produits()

    def get_options_pour_produit(self, produit_id):
        return self._produit.get_options_pour_produit(produit_id)

    def get_options(self):
        return self._produit.get_options()

    # ─── Affaires ─────────────────────────────────────────────────
    def creer_affaire(self, client_id, titre, description=""):
        return self._affaire.creer_affaire(client_id, titre, description)

    def get_liste_affaires(self):
        return self._affaire.get_liste_affaires()

    def get_affaire_details(self, affaire_id):
        return self._affaire.get_affaire_details(affaire_id)

    def cloturer_affaire(self, affaire_id, resultat, commentaire=""):
        return self._affaire.cloturer_affaire(affaire_id, resultat, commentaire)

    def is_affaire_cloturee(self, affaire_id):
        return self._affaire.is_affaire_cloturee(affaire_id)

    def mettre_a_jour_statut_affaire(self, affaire_id, nouveau_statut):
        return self._affaire.mettre_a_jour_statut_affaire(affaire_id, nouveau_statut)

    # ─── Clients ──────────────────────────────────────────────────
    def creer_ou_obtenir_client(self, nom_societe, contact_nom="",
                                contact_prenom="", contact_service="",
                                contact_email="", contact_tel="", siret=""):
        return self._affaire.creer_ou_obtenir_client(
            nom_societe, contact_nom, contact_prenom, contact_service,
            contact_email, contact_tel, siret)

    def get_client_par_siret(self, siret):
        return self._affaire.get_client_par_siret(siret)

    def get_affaires_client(self, client_id):
        return self._affaire.get_affaires_client(client_id)

    def get_tous_clients(self):
        return self._affaire.get_tous_clients()

    # ─── Commentaires ─────────────────────────────────────────────
    def ajouter_commentaire(self, affaire_id, auteur, role, contenu):
        return self._affaire.ajouter_commentaire(affaire_id, auteur, role, contenu)

    def get_commentaires_affaire(self, affaire_id):
        return self._affaire.get_commentaires_affaire(affaire_id)

    # ─── Devis ────────────────────────────────────────────────────
    def creer_devis_pour_affaire(self, affaire_id, produits_data, notes=""):
        return self._devis.creer_devis_pour_affaire(affaire_id, produits_data, notes)

    def get_devis_affaire(self, affaire_id):
        return self._devis.get_devis_affaire(affaire_id)

    def get_devis_info(self, devis_id):
        return self._devis.get_devis_info(devis_id)

    def get_produits_devis(self, devis_id):
        return self._devis.get_produits_devis(devis_id)

    def get_options_devis_detail(self, devis_id):
        return self._devis.get_options_devis_detail(devis_id)

    def creer_nouvelle_version_devis(self, devis_id_source, role_createur):
        return self._devis.creer_nouvelle_version_devis(devis_id_source, role_createur)

    # ─── Réponses options ─────────────────────────────────────────
    def repondre_option_standard(self, ligne_option_id, statut, prix_propose=None, commentaire=""):
        return self._devis.repondre_option_standard(ligne_option_id, statut, prix_propose, commentaire)

    def repondre_option_perso(self, option_perso_id, statut, prix_propose=None, commentaire="", poids=0):
        return self._devis.repondre_option_perso(option_perso_id, statut, prix_propose, commentaire, poids)

    def repondre_option_standard_acheteur(self, ligne_option_id, statut, commentaire=None):
        return self._devis.repondre_option_standard_acheteur(ligne_option_id, statut, commentaire)

    def repondre_option_perso_acheteur(self, option_perso_id, statut, commentaire=None):
        return self._devis.repondre_option_perso_acheteur(option_perso_id, statut, commentaire)

    # ─── Authentification vendeur ─────────────────────────────────
    def creer_vendeur(self, username, password, nom="", prenom="", email=""):
        return self._auth.creer_vendeur(username, password, nom, prenom, email)

    def authentifier_vendeur(self, username, password):
        return self._auth.authentifier_vendeur(username, password)

    def username_existe(self, username):
        return self._auth.username_existe(username)

    # ─── Authentification client ──────────────────────────────────
    def creer_client(self, username, password, nom_societe, siret,
                     contact_nom, contact_prenom, contact_service,
                     contact_email, contact_telephone, indicatif_tel):
        return self._auth.creer_client(
            username, password, nom_societe, siret,
            contact_nom, contact_prenom, contact_service,
            contact_email, contact_telephone, indicatif_tel)

    def authentifier_client(self, username, password):
        return self._auth.authentifier_client(username, password)

    def client_username_existe(self, username):
        return self._auth.client_username_existe(username)

    def client_siret_existe(self, siret):
        return self._auth.client_siret_existe(siret)

    def get_client_par_id(self, client_id):
        return self._auth.get_client_par_id(client_id)

    def get_vendeur_par_id(self, vendeur_id):
        return self._auth.get_vendeur_par_id(vendeur_id)
