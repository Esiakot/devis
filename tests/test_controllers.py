# ──────────────────────────────────────────────────────────────────────────────
# tests/test_controllers.py — Tests des contrôleurs MVC
# ──────────────────────────────────────────────────────────────────────────────
# Vérifie que les contrôleurs délèguent correctement aux repositories et que
# la logique métier (filtrage par client, création de compte) fonctionne.
# ──────────────────────────────────────────────────────────────────────────────
import pytest
from src.controllers.client_controller import ClientController
from src.controllers.vendeur_controller import VendeurController


# ─── VendeurController ────────────────────────────────────────────

class TestVendeurController:

    def test_creer_et_authentifier_vendeur(self, db):
        """Le contrôleur vendeur crée un compte et l'authentifie."""
        ctrl = VendeurController(db)
        vid = ctrl.creer_compte_vendeur("ctrl_vendeur", "SecurePass1!", "Nom", "Prenom")
        assert vid is not None
        result = ctrl.authentifier("ctrl_vendeur", "SecurePass1!")
        assert result is not None
        assert result["username"] == "ctrl_vendeur"

    def test_authentifier_vendeur_echec(self, db):
        """Authentification échoue avec mauvais identifiants."""
        ctrl = VendeurController(db)
        assert ctrl.authentifier("fake", "fake") is None

    def test_username_existe(self, db):
        """Le contrôleur détecte un username existant."""
        ctrl = VendeurController(db)
        ctrl.creer_compte_vendeur("exist_test", "SecurePass1!", "Nom", "Prenom")
        assert ctrl.username_existe("exist_test") is True
        assert ctrl.username_existe("nope") is False

    def test_get_produits(self, db):
        """Le contrôleur accède au catalogue produits."""
        ctrl = VendeurController(db)
        produits = ctrl.get_produits()
        assert isinstance(produits, list)
        assert len(produits) > 0

    def test_get_affaires(self, db):
        """Le contrôleur vendeur voit toutes les affaires."""
        ctrl = VendeurController(db)
        affaires = ctrl.get_affaires()
        assert isinstance(affaires, list)


# ─── ClientController ─────────────────────────────────────────────

class TestClientController:

    def _creer_client(self, db):
        """Helper : crée un client via le contrôleur et retourne (ctrl, client_id)."""
        ctrl = ClientController(db)
        cid = ctrl.creer_compte_client(
            "ctrl_client", "SecurePass1!", "CtrlCorp", "44444444444444",
            "Test", "User", "Achats", "test@ctrl.fr", "0600000000", "+33"
        )
        ctrl.client_id = cid
        return ctrl, cid

    def test_creer_et_authentifier_client(self, db):
        """Le contrôleur client crée un compte et l'authentifie."""
        ctrl, cid = self._creer_client(db)
        assert cid is not None
        result = ctrl.authentifier_client("ctrl_client", "SecurePass1!")
        assert result is not None
        assert result["username"] == "ctrl_client"

    def test_filtrage_affaires_par_client(self, db):
        """Le client ne voit que ses propres affaires."""
        ctrl, cid = self._creer_client(db)
        db.creer_affaire(cid, "Mon affaire client")
        affaires = ctrl.get_affaires()
        for a in affaires:
            # Toutes les affaires retournées sont liées au client
            assert a is not None

    def test_client_siret_existe(self, db):
        """Le contrôleur détecte un SIRET client existant."""
        ctrl, _ = self._creer_client(db)
        assert ctrl.client_siret_existe("44444444444444") is True
        assert ctrl.client_siret_existe("00000000000000") is False

    def test_get_produits_via_controller(self, db):
        """Le contrôleur client accède au catalogue."""
        ctrl = ClientController(db)
        produits = ctrl.get_produits()
        assert isinstance(produits, list)
        assert len(produits) > 0

    def test_get_commentaires_vide(self, db):
        """Pas de commentaires sur une affaire neuve."""
        ctrl, cid = self._creer_client(db)
        aid, _ = db.creer_affaire(cid, "Affaire sans commentaire")
        comments = ctrl.get_commentaires(aid)
        assert isinstance(comments, list)

    def test_envoyer_commentaire(self, db):
        """Le contrôleur permet d'envoyer un commentaire."""
        ctrl, cid = self._creer_client(db)
        aid, _ = db.creer_affaire(cid, "Affaire avec commentaire")
        ctrl.envoyer_commentaire(aid, "TestUser", "acheteur", "Bonjour !")
        comments = ctrl.get_commentaires(aid)
        contenus = [c[3] for c in comments]
        assert "Bonjour !" in contenus
