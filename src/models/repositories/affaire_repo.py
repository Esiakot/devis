# ──────────────────────────────────────────────────────────────────────────────
# src/models/repositories/affaire_repo.py — Repository Affaires
# ──────────────────────────────────────────────────────────────────────────────
# Gère toutes les opérations en base de données liées aux affaires (création,
# listing, détail, clôture, numérotation automatique), aux clients (création
# ou récupération, listing) et aux commentaires de discussion entre acheteur
# et vendeur. Chaque méthode ouvre et ferme sa propre connexion SQLite.
# ──────────────────────────────────────────────────────────────────────────────

from datetime import datetime


class AffaireRepository:

    def __init__(self, get_connection):
        self._conn = get_connection

    # ─── Numérotation ─────────────────────────────────────────────
    def generer_numero_affaire(self):
        annee = datetime.now().strftime("%y")
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero_affaire FROM affaire
            WHERE numero_affaire LIKE ?
            ORDER BY numero_affaire DESC LIMIT 1
        """, (f"{annee}%",))
        result = cursor.fetchone()
        conn.close()
        if result:
            return str(int(result[0]) + 1)
        return f"{annee}001"

    # ─── CRUD Affaire ─────────────────────────────────────────────
    def creer_affaire(self, client_id, titre, description=""):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            numero = self.generer_numero_affaire()
            cursor.execute("""
                INSERT INTO affaire (numero_affaire, client_id, titre, description)
                VALUES (?, ?, ?, ?)
            """, (numero, client_id, titre, description))
            affaire_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Affaire N°{numero} créée.")
            return affaire_id, numero
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur création affaire : {e}")
            return None, None
        finally:
            conn.close()

    def get_liste_affaires(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.numero_affaire, c.nom_societe, a.titre, a.statut,
                   a.date_creation, a.date_modification,
                   (SELECT COUNT(*) FROM devis WHERE affaire_id = a.id) as nb_devis
            FROM affaire a
            LEFT JOIN client c ON a.client_id = c.id
            ORDER BY a.date_creation DESC
        """)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_affaire_details(self, affaire_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.numero_affaire, c.nom_societe, c.contact_nom, c.contact_email,
                   a.titre, a.description, a.statut, a.date_creation
            FROM affaire a
            LEFT JOIN client c ON a.client_id = c.id
            WHERE a.id = ?
        """, (affaire_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def cloturer_affaire(self, affaire_id, resultat, commentaire=""):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE affaire
                SET statut = ?, date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (resultat, affaire_id))
            if commentaire:
                cursor.execute("""
                    INSERT INTO commentaire (affaire_id, auteur, role, contenu)
                    VALUES (?, 'SYSTÈME', 'vendeur', ?)
                """, (affaire_id, f"[CLÔTURE - {resultat.upper()}] {commentaire}"))
            conn.commit()
            print(f"✅ Affaire clôturée: {resultat}")
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur clôture affaire : {e}")
            return False
        finally:
            conn.close()

    def is_affaire_cloturee(self, affaire_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT statut FROM affaire WHERE id = ?", (affaire_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0] in ('gagne', 'perdu', 'annule'):
            return True, result[0]
        return False, None

    def mettre_a_jour_statut_affaire(self, affaire_id, nouveau_statut):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE affaire
            SET statut = ?, date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nouveau_statut, affaire_id))
        conn.commit()
        conn.close()

    # ─── Clients ──────────────────────────────────────────────────
    def creer_ou_obtenir_client(self, nom_societe, contact_nom="",
                                contact_prenom="", contact_service="",
                                contact_email="", contact_tel="", siret=""):
        conn = self._conn()
        cursor = conn.cursor()
        if siret:
            cursor.execute("SELECT id FROM client WHERE siret = ?", (siret,))
            result = cursor.fetchone()
            if result:
                cursor.execute("""
                    UPDATE client SET contact_nom = ?, contact_prenom = ?,
                        contact_service = ?, contact_email = ?,
                        contact_telephone = ?, nom_societe = ?
                    WHERE id = ?
                """, (contact_nom, contact_prenom, contact_service,
                      contact_email, contact_tel, nom_societe, result[0]))
                conn.commit()
                conn.close()
                return result[0]
        else:
            cursor.execute("SELECT id FROM client WHERE nom_societe = ?", (nom_societe,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return result[0]
        cursor.execute("""
            INSERT INTO client (nom_societe, contact_nom, contact_prenom,
                               contact_service, contact_email, contact_telephone, siret)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nom_societe, contact_nom, contact_prenom, contact_service,
              contact_email, contact_tel, siret))
        client_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return client_id

    def get_client_par_siret(self, siret):
        """Recherche un client par numéro SIRET."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom_societe, contact_nom, contact_prenom, contact_service,
                   contact_email, contact_telephone, siret
            FROM client WHERE siret = ?
        """, (siret,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_tous_clients(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom_societe, contact_nom, contact_prenom, contact_service,
                   contact_email, contact_telephone, siret
            FROM client ORDER BY nom_societe
        """)
        results = cursor.fetchall()
        conn.close()
        return results

    def get_affaires_client(self, client_id):
        """Retourne uniquement les affaires d'un client donné."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.numero_affaire, c.nom_societe, a.titre, a.statut,
                   a.date_creation, a.date_modification,
                   (SELECT COUNT(*) FROM devis WHERE affaire_id = a.id) as nb_devis
            FROM affaire a
            LEFT JOIN client c ON a.client_id = c.id
            WHERE a.client_id = ?
            ORDER BY a.date_creation DESC
        """, (client_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    # ─── Commentaires ─────────────────────────────────────────────
    def ajouter_commentaire(self, affaire_id, auteur, role, contenu):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO commentaire (affaire_id, auteur, role, contenu)
                VALUES (?, ?, ?, ?)
            """, (affaire_id, auteur, role, contenu))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur ajout commentaire : {e}")
            return None
        finally:
            conn.close()

    def get_commentaires_affaire(self, affaire_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, auteur, role, contenu, date_creation
            FROM commentaire
            WHERE affaire_id = ?
            ORDER BY date_creation ASC
        """, (affaire_id,))
        results = cursor.fetchall()
        conn.close()
        return results
