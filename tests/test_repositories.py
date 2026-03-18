# ──────────────────────────────────────────────────────────────────────────────
# tests/test_repositories.py — Tests d'intégration des repositories
# ──────────────────────────────────────────────────────────────────────────────
# Utilise une base SQLite temporaire (fixture db) pour tester les opérations
# CRUD réelles sur les affaires, devis, authentification et produits.
# ──────────────────────────────────────────────────────────────────────────────
import pytest


# ─── AuthRepository — Vendeur ─────────────────────────────────────

class TestAuthVendeur:

    def test_creer_vendeur(self, db):
        """Création d'un vendeur retourne un ID valide."""
        vid = db.creer_vendeur("testvendeur", "MotDePasse1!", "Dupont", "Jean")
        assert vid is not None
        assert isinstance(vid, int)

    def test_authentifier_vendeur_ok(self, db):
        """Authentification réussie retourne les infos vendeur."""
        db.creer_vendeur("authtest", "SecurePass1!", "Martin", "Paul")
        result = db.authentifier_vendeur("authtest", "SecurePass1!")
        assert result is not None
        assert result["username"] == "authtest"
        assert result["nom"] == "Martin"

    def test_authentifier_vendeur_mauvais_mdp(self, db):
        """Authentification avec mauvais mot de passe retourne None."""
        db.creer_vendeur("authfail", "SecurePass1!", "Test", "User")
        result = db.authentifier_vendeur("authfail", "mauvais")
        assert result is None

    def test_authentifier_vendeur_inconnu(self, db):
        """Authentification avec utilisateur inconnu retourne None."""
        result = db.authentifier_vendeur("nexistepas", "test")
        assert result is None

    def test_username_existe(self, db):
        """Détection correcte d'un username existant."""
        db.creer_vendeur("existant", "MotDePasse1!")
        assert db.username_existe("existant") is True
        assert db.username_existe("inexistant") is False

    def test_doublon_username_vendeur(self, db):
        """Un doublon de username vendeur retourne None."""
        db.creer_vendeur("doublon", "MotDePasse1!")
        result = db.creer_vendeur("doublon", "MotDePasse2!")
        assert result is None


# ─── AuthRepository — Client ─────────────────────────────────────

class TestAuthClient:

    def test_creer_client(self, db):
        """Création d'un client retourne un ID valide."""
        cid = db.creer_client(
            "clientuser", "MotDePasse1!", "ACME SAS", "12345678901234",
            "Doe", "John", "Achats", "john@acme.fr", "0612345678", "+33"
        )
        assert cid is not None
        assert isinstance(cid, int)

    def test_authentifier_client_ok(self, db):
        """Authentification client réussie."""
        db.creer_client(
            "clientauth", "SecurePass1!", "TestCorp", "73282932000074",
            "Smith", "Anna", "Tech", "anna@test.fr", "0698765432", "+33"
        )
        result = db.authentifier_client("clientauth", "SecurePass1!")
        assert result is not None
        assert result["username"] == "clientauth"
        assert result["nom_societe"] == "TestCorp"

    def test_authentifier_client_mauvais_mdp(self, db):
        """Authentification client avec mauvais mot de passe."""
        db.creer_client(
            "clientfail", "SecurePass1!", "FailCorp", "00000000000000",
            "X", "Y", "Z", "x@y.fr", "0600000000", "+33"
        )
        assert db.authentifier_client("clientfail", "mauvais") is None

    def test_client_siret_existe(self, db):
        """Détection correcte d'un SIRET client existant."""
        db.creer_client(
            "siretuser", "MotDePasse1!", "SiretCorp", "99999999999999",
            "A", "B", "C", "a@b.fr", "0611111111", "+33"
        )
        assert db.client_siret_existe("99999999999999") is True
        assert db.client_siret_existe("00000000000001") is False


# ─── AffaireRepository ────────────────────────────────────────────

class TestAffaireRepo:

    def _creer_client_test(self, db):
        """Helper : crée un client et retourne son ID."""
        return db.creer_client(
            "affaire_client", "MotDePasse1!", "AffaireCorp", "11111111111111",
            "Test", "User", "Service", "test@corp.fr", "0600000000", "+33"
        )

    def test_creer_affaire(self, db):
        """Création d'une affaire retourne un ID et un numéro."""
        client_id = self._creer_client_test(db)
        affaire_id, numero = db.creer_affaire(client_id, "Projet Test", "Description")
        assert affaire_id is not None
        assert numero is not None
        assert len(numero) >= 5  # Format AANNNN

    def test_get_affaire_details(self, db):
        """Récupération des détails d'une affaire."""
        client_id = self._creer_client_test(db)
        affaire_id, _ = db.creer_affaire(client_id, "Détail Test")
        details = db.get_affaire_details(affaire_id)
        assert details is not None
        assert details[5] == "Détail Test"  # titre

    def test_get_liste_affaires(self, db):
        """La liste des affaires contient les affaires créées."""
        client_id = self._creer_client_test(db)
        db.creer_affaire(client_id, "Affaire A")
        db.creer_affaire(client_id, "Affaire B")
        affaires = db.get_liste_affaires()
        # Au moins 2 + les éventuelles données démo
        titres = [a[3] for a in affaires]
        assert "Affaire A" in titres
        assert "Affaire B" in titres

    def test_cloturer_affaire(self, db):
        """Clôture d'une affaire change son statut."""
        client_id = self._creer_client_test(db)
        affaire_id, _ = db.creer_affaire(client_id, "À clôturer")
        result = db.cloturer_affaire(affaire_id, "gagne", "Bravo")
        assert result is True
        cloturee, statut = db.is_affaire_cloturee(affaire_id)
        assert cloturee is True
        assert statut == "gagne"

    def test_affaire_non_cloturee(self, db):
        """Une affaire fraîchement créée n'est pas clôturée."""
        client_id = self._creer_client_test(db)
        affaire_id, _ = db.creer_affaire(client_id, "En cours")
        cloturee, statut = db.is_affaire_cloturee(affaire_id)
        assert cloturee is False
        assert statut is None


# ─── Commentaires ─────────────────────────────────────────────────

class TestCommentaires:

    def _setup_affaire(self, db):
        cid = db.creer_client(
            "com_client", "MotDePasse1!", "ComCorp", "22222222222222",
            "A", "B", "C", "a@b.fr", "0600000000", "+33"
        )
        aid, _ = db.creer_affaire(cid, "Affaire Commentaires")
        return aid

    def test_ajouter_et_lire_commentaire(self, db):
        """Un commentaire ajouté est retrouvé dans la liste."""
        affaire_id = self._setup_affaire(db)
        db.ajouter_commentaire(affaire_id, "Jean", "vendeur", "Premier commentaire")
        comments = db.get_commentaires_affaire(affaire_id)
        assert len(comments) >= 1
        contenus = [c[3] for c in comments]  # contenu est à l'index 3
        assert "Premier commentaire" in contenus


# ─── ProduitRepository ────────────────────────────────────────────

class TestProduitRepo:

    def test_get_produits_retourne_liste(self, db):
        """get_produits retourne une liste non vide (données démo)."""
        produits = db.get_produits()
        assert isinstance(produits, list)
        assert len(produits) > 0

    def test_produit_a_structure_correcte(self, db):
        """Chaque produit a (id, nom, prix_base, charge_max)."""
        produits = db.get_produits()
        p = produits[0]
        assert len(p) == 4
        assert isinstance(p[0], int)   # id
        assert isinstance(p[1], str)   # nom

    def test_get_options_pour_produit(self, db):
        """Les options d'un produit incluent les universelles."""
        produits = db.get_produits()
        if produits:
            options = db.get_options_pour_produit(produits[0][0])
            assert isinstance(options, list)


# ─── DevisRepository ──────────────────────────────────────────────

class TestDevisRepo:

    def _setup_affaire_avec_produit(self, db):
        """Helper : crée client + affaire, retourne (affaire_id, premier_produit_id)."""
        cid = db.creer_client(
            "devis_client", "MotDePasse1!", "DevisCorp", "33333333333333",
            "A", "B", "C", "a@b.fr", "0600000000", "+33"
        )
        aid, _ = db.creer_affaire(cid, "Affaire Devis")
        produits = db.get_produits()
        return aid, produits[0][0]

    def test_creer_devis(self, db):
        """Création d'un devis avec un produit."""
        aid, pid = self._setup_affaire_avec_produit(db)
        devis_id, version = db.creer_devis_pour_affaire(
            aid, [(pid, 2, 1000.0, [], [])]
        )
        assert devis_id is not None
        assert version == 1

    def test_devis_versioning(self, db):
        """Le deuxième devis d'une affaire a la version 2."""
        aid, pid = self._setup_affaire_avec_produit(db)
        db.creer_devis_pour_affaire(aid, [(pid, 1, 500.0, [], [])])
        _, v2 = db.creer_devis_pour_affaire(aid, [(pid, 1, 600.0, [], [])])
        assert v2 == 2

    def test_get_devis_affaire(self, db):
        """get_devis_affaire retourne les devis créés."""
        aid, pid = self._setup_affaire_avec_produit(db)
        db.creer_devis_pour_affaire(aid, [(pid, 1, 500.0, [], [])])
        devis_list = db.get_devis_affaire(aid)
        assert len(devis_list) >= 1

    def test_get_devis_info(self, db):
        """get_devis_info retourne les infos du devis."""
        aid, pid = self._setup_affaire_avec_produit(db)
        did, _ = db.creer_devis_pour_affaire(aid, [(pid, 1, 750.0, [], [])])
        info = db.get_devis_info(did)
        assert info is not None
        assert info[0] == did  # id
        assert info[3] == 750.0  # total_estime

    def test_creer_devis_avec_options(self, db):
        """Création d'un devis avec des options standard."""
        aid, pid = self._setup_affaire_avec_produit(db)
        options = db.get_options_pour_produit(pid)
        opt_ids = [o[0] for o in options[:2]] if options else []
        did, ver = db.creer_devis_pour_affaire(
            aid, [(pid, 1, 500.0, opt_ids, [])]
        )
        assert did is not None

    def test_creer_devis_avec_options_perso(self, db):
        """Création d'un devis avec une option personnalisée."""
        aid, pid = self._setup_affaire_avec_produit(db)
        perso = [{"description": "Peinture spéciale", "prix": 200.0, "poids": 5.0}]
        did, ver = db.creer_devis_pour_affaire(
            aid, [(pid, 1, 500.0, [], perso)]
        )
        assert did is not None
