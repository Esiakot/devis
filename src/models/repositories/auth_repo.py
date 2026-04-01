# ──────────────────────────────────────────────────────────────────────────────
# src/models/repositories/auth_repo.py — Repository Authentification
# ──────────────────────────────────────────────────────────────────────────────
# Gère les comptes vendeur ET client : création avec mot de passe haché et
# salé, authentification sécurisée, et vérification d'existence d'identifiants.
# ──────────────────────────────────────────────────────────────────────────────

from src.utils.auth import hash_password, verify_password


class AuthRepository:

    def __init__(self, get_connection):
        self._conn = get_connection

    # ─── Comptes vendeur ──────────────────────────────────────────
    def creer_vendeur(self, username, password, nom="", prenom="", email=""):
        """Crée un compte vendeur avec mot de passe haché. Returns vendeur_id ou None."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO vendeur (username, password_hash, nom, prenom, email)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, nom, prenom, email))
            vendeur_id = cursor.lastrowid
            conn.commit()
            print(f"Compte vendeur '{username}' créé.")
            return vendeur_id
        except Exception as e:
            conn.rollback()
            print(f"Erreur création vendeur : {e}")
            return None
        finally:
            conn.close()

    def authentifier_vendeur(self, username, password):
        """Authentifie un vendeur. Returns dict info ou None si échec."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, nom, prenom
            FROM vendeur WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        conn.close()

        if result and verify_password(password, result[2]):
            return {
                "id": result[0],
                "username": result[1],
                "nom": result[3],
                "prenom": result[4],
            }
        return None

    def username_existe(self, username):
        """Vérifie si un nom d'utilisateur vendeur existe déjà."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM vendeur WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    # ─── Comptes client ───────────────────────────────────────────
    def creer_client(self, username, password, nom_societe, siret,
                     contact_nom, contact_prenom, contact_service,
                     contact_email, contact_telephone, indicatif_tel):
        """Crée un compte client avec mot de passe haché. Returns client_id ou None."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO client (username, password_hash, nom_societe, siret,
                    contact_nom, contact_prenom, contact_service,
                    contact_email, contact_telephone, indicatif_tel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password_hash, nom_societe, siret,
                  contact_nom, contact_prenom, contact_service,
                  contact_email, contact_telephone, indicatif_tel))
            client_id = cursor.lastrowid
            conn.commit()
            print(f"Compte client '{username}' créé.")
            return client_id
        except Exception as e:
            conn.rollback()
            print(f"Erreur création client : {e}")
            return None
        finally:
            conn.close()

    def authentifier_client(self, username, password):
        """Authentifie un client. Returns dict info ou None si échec."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, nom_societe, siret,
                   contact_nom, contact_prenom, contact_service,
                   contact_email, contact_telephone
            FROM client WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        conn.close()

        if result and verify_password(password, result[2]):
            return {
                "id": result[0],
                "username": result[1],
                "nom_societe": result[3],
                "siret": result[4],
                "nom": result[5],
                "prenom": result[6],
                "service": result[7],
                "email": result[8],
                "telephone": result[9],
            }
        return None

    def client_username_existe(self, username):
        """Vérifie si un nom d'utilisateur client existe déjà."""
        username = username.lower()
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM client WHERE username = ?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def client_siret_existe(self, siret):
        """Vérifie si un SIRET est déjà enregistré (avec un compte)."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM client WHERE siret = ? AND username IS NOT NULL", (siret,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_client_par_id(self, client_id):
        """Récupère les infos client par ID (pour restauration de session)."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, nom_societe, siret,
                   contact_nom, contact_prenom, contact_service,
                   contact_email, contact_telephone
            FROM client WHERE id = ?
        """, (client_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "id": result[0], "username": result[1],
                "nom_societe": result[2], "siret": result[3],
                "nom": result[4], "prenom": result[5],
                "service": result[6], "email": result[7],
                "telephone": result[8],
            }
        return None

    def get_vendeur_par_id(self, vendeur_id):
        """Récupère les infos vendeur par ID (pour restauration de session)."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, nom, prenom
            FROM vendeur WHERE id = ?
        """, (vendeur_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "id": result[0], "username": result[1],
                "nom": result[2], "prenom": result[3],
            }
        return None
