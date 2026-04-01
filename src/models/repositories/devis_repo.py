# ──────────────────────────────────────────────────────────────────────────────
# src/models/repositories/devis_repo.py — Repository Devis
# ──────────────────────────────────────────────────────────────────────────────
# Gère toutes les opérations en base liées aux devis : création d'un devis
# avec ses produits et options (standard et personnalisées), récupération des
# détails, gestion du versioning (nouvelles versions suite aux réponses vendeur
# ou acheteur), et enregistrement des réponses sur chaque option.
# ──────────────────────────────────────────────────────────────────────────────


class DevisRepository:

    def __init__(self, get_connection):
        self._conn = get_connection

    # ─── Création ─────────────────────────────────────────────────
    def creer_devis_pour_affaire(self, affaire_id, produits_data, notes=""):
        """
        Crée un nouveau devis pour une affaire avec plusieurs produits.
        produits_data = [(produit_id, quantite, prix_unitaire, [options_ids], [options_perso]), ...]
        """
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(version) FROM devis WHERE affaire_id = ?", (affaire_id,))
            version = (cursor.fetchone()[0] or 0) + 1

            total = 0
            for item in produits_data:
                prod_id, qte, prix_unit, options_ids = item[0], item[1], item[2], item[3]
                options_perso = item[4] if len(item) > 4 else []
                subtotal = prix_unit * qte
                if options_ids:
                    cursor.execute(
                        f"SELECT SUM(prix) FROM option WHERE id IN ({','.join('?' * len(options_ids))})",
                        options_ids)
                    prix_opts = cursor.fetchone()[0] or 0
                    subtotal += prix_opts * qte
                for opt_perso in options_perso:
                    prix = opt_perso.get('prix') if isinstance(opt_perso, dict) else (
                        opt_perso[1] if len(opt_perso) > 1 else None)
                    if prix:
                        subtotal += prix * qte
                total += subtotal

            cursor.execute("""
                INSERT INTO devis (affaire_id, version, total_estime, notes)
                VALUES (?, ?, ?, ?)
            """, (affaire_id, version, total, notes))
            devis_id = cursor.lastrowid

            for item in produits_data:
                prod_id, qte, prix_unit, options_ids = item[0], item[1], item[2], item[3]
                options_perso = item[4] if len(item) > 4 else []
                cursor.execute("""
                    INSERT INTO produit_devis (devis_id, produit_id, quantite, prix_unitaire)
                    VALUES (?, ?, ?, ?)
                """, (devis_id, prod_id, qte, prix_unit))
                prod_devis_id = cursor.lastrowid

                for opt_id in options_ids:
                    cursor.execute("""
                        INSERT INTO ligne_option_produit_devis (produit_devis_id, option_id)
                        VALUES (?, ?)
                    """, (prod_devis_id, opt_id))

                for opt_perso in options_perso:
                    if isinstance(opt_perso, dict):
                        desc = opt_perso.get('description', '')
                        prix = opt_perso.get('prix')
                        poids = opt_perso.get('poids', 0)
                    else:
                        desc = opt_perso[0] if len(opt_perso) > 0 else ''
                        prix = opt_perso[1] if len(opt_perso) > 1 else None
                        poids = 0
                    cursor.execute("""
                        INSERT INTO option_personnalisee (produit_devis_id, description, prix_demande, poids)
                        VALUES (?, ?, ?, ?)
                    """, (prod_devis_id, desc, prix, poids))

            conn.commit()
            print(f"Devis V{version} créé pour l'affaire.")
            return devis_id, version
        except Exception as e:
            conn.rollback()
            print(f"Erreur création devis : {e}")
            return None, None
        finally:
            conn.close()

    # ─── Lecture ───────────────────────────────────────────────────
    def get_devis_affaire(self, affaire_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, version, date_creation, total_estime, statut, notes
            FROM devis WHERE affaire_id = ? ORDER BY version DESC
        """, (affaire_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_devis_info(self, devis_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id, d.affaire_id, d.version, d.total_estime, d.notes, a.numero_affaire
            FROM devis d
            JOIN affaire a ON d.affaire_id = a.id
            WHERE d.id = ?
        """, (devis_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def get_produits_devis(self, devis_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pd.id, p.nom, pd.quantite, pd.prix_unitaire
            FROM produit_devis pd
            JOIN produit p ON pd.produit_id = p.id
            WHERE pd.devis_id = ?
        """, (devis_id,))
        produits = cursor.fetchall()
        result = []
        for pd_id, nom, qte, prix in produits:
            cursor.execute("""
                SELECT o.nom, o.prix
                FROM ligne_option_produit_devis lopd
                JOIN option o ON lopd.option_id = o.id
                WHERE lopd.produit_devis_id = ?
            """, (pd_id,))
            options = cursor.fetchall()
            result.append((pd_id, nom, qte, prix, options))
        conn.close()
        return result

    def get_options_devis_detail(self, devis_id):
        conn = self._conn()
        cursor = conn.cursor()
        result = {'produits': []}

        cursor.execute("""
            SELECT pd.id, p.nom, pd.quantite, pd.prix_unitaire
            FROM produit_devis pd
            JOIN produit p ON pd.produit_id = p.id
            WHERE pd.devis_id = ?
        """, (devis_id,))

        for pd_id, nom, qte, prix in cursor.fetchall():
            prod_data = {
                'id': pd_id, 'nom': nom, 'quantite': qte, 'prix_unitaire': prix,
                'options_standard': [], 'options_perso': [],
            }

            cursor.execute("""
                SELECT lopd.id, o.nom, o.prix, lopd.statut_vendeur, lopd.prix_propose,
                       lopd.commentaire_vendeur, lopd.statut_acheteur, lopd.commentaire_acheteur
                FROM ligne_option_produit_devis lopd
                JOIN option o ON lopd.option_id = o.id
                WHERE lopd.produit_devis_id = ?
            """, (pd_id,))
            for row in cursor.fetchall():
                prod_data['options_standard'].append({
                    'id': row[0], 'nom': row[1], 'prix': row[2],
                    'statut_vendeur': row[3], 'prix_propose': row[4],
                    'commentaire_vendeur': row[5],
                    'statut_acheteur': row[6], 'commentaire_acheteur': row[7],
                })

            cursor.execute("""
                SELECT id, description, prix_demande, statut_vendeur, prix_propose,
                       commentaire_vendeur, statut_acheteur, commentaire_acheteur
                FROM option_personnalisee WHERE produit_devis_id = ?
            """, (pd_id,))
            for row in cursor.fetchall():
                prod_data['options_perso'].append({
                    'id': row[0], 'description': row[1], 'prix_demande': row[2],
                    'statut_vendeur': row[3], 'prix_propose': row[4],
                    'commentaire_vendeur': row[5],
                    'statut_acheteur': row[6], 'commentaire_acheteur': row[7],
                })

            result['produits'].append(prod_data)

        conn.close()
        return result

    # ─── Réponses vendeur ─────────────────────────────────────────
    def repondre_option_standard(self, ligne_option_id, statut, prix_propose=None, commentaire=""):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE ligne_option_produit_devis
                SET statut_vendeur = ?, prix_propose = ?, commentaire_vendeur = ?
                WHERE id = ?
            """, (statut, prix_propose, commentaire, ligne_option_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erreur réponse option : {e}")
            return False
        finally:
            conn.close()

    def repondre_option_perso(self, option_perso_id, statut, prix_propose=None, commentaire="", poids=0):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE option_personnalisee
                SET statut_vendeur = ?, prix_propose = ?, commentaire_vendeur = ?, poids = ?
                WHERE id = ?
            """, (statut, prix_propose, commentaire, poids, option_perso_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erreur réponse option perso : {e}")
            return False
        finally:
            conn.close()

    # ─── Réponses acheteur ────────────────────────────────────────
    def repondre_option_standard_acheteur(self, ligne_option_id, statut, commentaire=None):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE ligne_option_produit_devis
                SET statut_acheteur = ?, commentaire_acheteur = ?
                WHERE id = ?
            """, (statut, commentaire, ligne_option_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erreur réponse acheteur option standard : {e}")
            return False
        finally:
            conn.close()

    def repondre_option_perso_acheteur(self, option_perso_id, statut, commentaire=None):
        conn = self._conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE option_personnalisee
                SET statut_acheteur = ?, commentaire_acheteur = ?
                WHERE id = ?
            """, (statut, commentaire, option_perso_id))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Erreur réponse acheteur option perso : {e}")
            return False
        finally:
            conn.close()

    # ─── Versioning ───────────────────────────────────────────────
    def creer_nouvelle_version_devis(self, devis_id_source, role_createur):
        """
        Crée une nouvelle version du devis en copiant toutes les données
        avec les réponses actuelles et un total recalculé.

        Règles de calcul du prix:
        - Option refusée → 0€
        - Contre-proposition acceptée → prix_propose
        - Acceptée / en attente → prix catalogue ou prix_demande
        """
        conn = self._conn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT affaire_id, total_estime, notes FROM devis WHERE id = ?",
                (devis_id_source,))
            affaire_id, _old_total, notes = cursor.fetchone()

            cursor.execute("SELECT MAX(version) FROM devis WHERE affaire_id = ?", (affaire_id,))
            new_version = (cursor.fetchone()[0] or 0) + 1

            # Charger les produits source
            cursor.execute("""
                SELECT id, produit_id, quantite, prix_unitaire
                FROM produit_devis WHERE devis_id = ?
            """, (devis_id_source,))
            produits_data = cursor.fetchall()

            new_total = self._calculer_total(cursor, produits_data)

            cursor.execute("""
                INSERT INTO devis (affaire_id, version, total_estime, notes)
                VALUES (?, ?, ?, ?)
            """, (affaire_id, new_version, new_total,
                  f"{notes or ''}\n[V{new_version} par {role_createur}]"))
            new_devis_id = cursor.lastrowid

            self._copier_produits_devis(cursor, produits_data, new_devis_id)

            conn.commit()
            print(f"Nouvelle version V{new_version} créée. Total: {new_total}€")
            return new_devis_id, new_version
        except Exception as e:
            conn.rollback()
            print(f"Erreur création nouvelle version : {e}")
            return None, None
        finally:
            conn.close()

    # ─── Helpers privés pour le versioning ────────────────────────
    @staticmethod
    def _calculer_total(cursor, produits_data):
        total = 0
        for old_pd_id, _prod_id, qte, prix_unit in produits_data:
            total += prix_unit * qte

            # Options standard
            cursor.execute("""
                SELECT o.prix, lopd.statut_vendeur, lopd.prix_propose, lopd.statut_acheteur
                FROM ligne_option_produit_devis lopd
                JOIN option o ON lopd.option_id = o.id
                WHERE lopd.produit_devis_id = ?
            """, (old_pd_id,))
            for prix_cat, sv, pp, sa in cursor.fetchall():
                if sv == 'refuse' or sa == 'refuse':
                    continue
                if sv == 'contre_proposition' and sa == 'accepte' and pp:
                    total += pp * qte
                elif sv == 'contre_proposition' and pp:
                    total += pp * qte
                elif sv in ('accepte', 'en_attente'):
                    total += prix_cat * qte

            # Options personnalisées
            cursor.execute("""
                SELECT prix_demande, statut_vendeur, prix_propose, statut_acheteur
                FROM option_personnalisee WHERE produit_devis_id = ?
            """, (old_pd_id,))
            for prix_dem, sv, pp, sa in cursor.fetchall():
                if sv == 'refuse' or sa == 'refuse':
                    continue
                if sv == 'contre_proposition' and sa == 'accepte' and pp:
                    total += pp * qte
                elif sv == 'contre_proposition' and pp:
                    total += pp * qte
                elif sv == 'accepte' and prix_dem:
                    total += prix_dem * qte
                elif sv == 'en_attente' and prix_dem:
                    total += prix_dem * qte
        return total

    @staticmethod
    def _copier_produits_devis(cursor, produits_data, new_devis_id):
        for old_pd_id, prod_id, qte, prix in produits_data:
            cursor.execute("""
                INSERT INTO produit_devis (devis_id, produit_id, quantite, prix_unitaire)
                VALUES (?, ?, ?, ?)
            """, (new_devis_id, prod_id, qte, prix))
            new_pd_id = cursor.lastrowid

            # Copier options standard
            cursor.execute("""
                SELECT option_id, statut_vendeur, prix_propose, commentaire_vendeur,
                       statut_acheteur, commentaire_acheteur
                FROM ligne_option_produit_devis WHERE produit_devis_id = ?
            """, (old_pd_id,))
            for opt_id, sv, pv, cv, sa, ca in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO ligne_option_produit_devis
                    (produit_devis_id, option_id, statut_vendeur, prix_propose,
                     commentaire_vendeur, statut_acheteur, commentaire_acheteur)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (new_pd_id, opt_id, sv, pv, cv, sa, ca))

            # Copier options personnalisées
            cursor.execute("""
                SELECT description, prix_demande, poids, statut_vendeur, prix_propose,
                       commentaire_vendeur, statut_acheteur, commentaire_acheteur
                FROM option_personnalisee WHERE produit_devis_id = ?
            """, (old_pd_id,))
            for desc, pd, poids, sv, pv, cv, sa, ca in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO option_personnalisee
                    (produit_devis_id, description, prix_demande, poids, statut_vendeur,
                     prix_propose, commentaire_vendeur, statut_acheteur, commentaire_acheteur)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_pd_id, desc, pd, poids, sv, pv, cv, sa, ca))
