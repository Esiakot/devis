import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    """
    Gère la connexion SQLite, la création des tables et les requêtes.
    """
    
    def __init__(self, db_name="devis_database.db"):
        # Chemin dynamique vers le dossier /data
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(base_dir, "data", db_name)
        
        # Création du dossier data si besoin
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Créer les tables et insérer les données de démo si nécessaire
        self.create_tables()
        self.add_demo_data()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table Produit (anciennement Hexapode)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                charge_max REAL,
                prix_base REAL
            )
        """)
        
        # Table Option (avec flag universelle)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prix REAL,
                poids REAL DEFAULT 0,
                universelle INTEGER DEFAULT 0
            )
        """)
        
        # Table Produit_Option (liaison options spécifiques par produit)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produit_option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_id INTEGER,
                option_id INTEGER,
                FOREIGN KEY(produit_id) REFERENCES produit(id),
                FOREIGN KEY(option_id) REFERENCES option(id),
                UNIQUE(produit_id, option_id)
            )
        """)
        
        # Table Client
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_societe TEXT NOT NULL,
                contact_nom TEXT,
                contact_email TEXT,
                contact_telephone TEXT
            )
        """)
        
        # Table Affaire (nouveau système de numérotation YYXXX)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS affaire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_affaire TEXT UNIQUE NOT NULL,
                client_id INTEGER,
                titre TEXT NOT NULL,
                description TEXT,
                statut TEXT DEFAULT 'en_cours',
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_modification DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES client(id)
            )
        """)
        
        # Table Devis (modifiée pour être liée à une affaire)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affaire_id INTEGER,
                version INTEGER DEFAULT 1,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_estime REAL,
                statut TEXT DEFAULT 'brouillon',
                notes TEXT,
                FOREIGN KEY(affaire_id) REFERENCES affaire(id)
            )
        """)
        
        # Table Produit_Devis (liaison Many-to-Many pour plusieurs produits par devis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produit_devis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                devis_id INTEGER,
                produit_id INTEGER,
                quantite INTEGER DEFAULT 1,
                prix_unitaire REAL,
                FOREIGN KEY(devis_id) REFERENCES devis(id),
                FOREIGN KEY(produit_id) REFERENCES produit(id)
            )
        """)

        # Table Liaison Produit_Devis-Option (options par produit dans un devis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ligne_option_produit_devis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_devis_id INTEGER,
                option_id INTEGER,
                statut_vendeur TEXT DEFAULT 'en_attente',
                prix_propose REAL,
                commentaire_vendeur TEXT,
                statut_acheteur TEXT DEFAULT 'en_attente',
                commentaire_acheteur TEXT,
                FOREIGN KEY(produit_devis_id) REFERENCES produit_devis(id),
                FOREIGN KEY(option_id) REFERENCES option(id)
            )
        """)
        
        # Table Options personnalisées (demandes spéciales du client)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS option_personnalisee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_devis_id INTEGER,
                description TEXT NOT NULL,
                prix_demande REAL,
                poids REAL DEFAULT 0,
                statut_vendeur TEXT DEFAULT 'en_attente',
                prix_propose REAL,
                commentaire_vendeur TEXT,
                statut_acheteur TEXT DEFAULT 'en_attente',
                commentaire_acheteur TEXT,
                FOREIGN KEY(produit_devis_id) REFERENCES produit_devis(id)
            )
        """)
        
        # Table Commentaires (échanges acheteur/vendeur)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commentaire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affaire_id INTEGER,
                auteur TEXT NOT NULL,
                role TEXT NOT NULL,
                contenu TEXT NOT NULL,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(affaire_id) REFERENCES affaire(id)
            )
        """)
        
        # Ancienne table pour compatibilité (à supprimer plus tard)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ligne_option_devis (
                devis_id INTEGER,
                option_id INTEGER,
                PRIMARY KEY (devis_id, option_id),
                FOREIGN KEY(devis_id) REFERENCES devis(id),
                FOREIGN KEY(option_id) REFERENCES option(id)
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Base de données vérifiée.")

    def get_produits(self):
        """Récupère la liste de tous les produits avec leur charge max."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix_base, charge_max FROM produit ORDER BY nom")
        results = cursor.fetchall()
        conn.close()
        return results

    def get_options_pour_produit(self, produit_id):
        """Récupère les options disponibles pour un produit (universelles + spécifiques)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT o.id, o.nom, o.prix, o.poids, o.universelle
            FROM option o
            LEFT JOIN produit_option po ON o.id = po.option_id
            WHERE o.universelle = 1 OR po.produit_id = ?
            ORDER BY o.universelle DESC, o.nom
        """, (produit_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_options(self):
        """Récupère la liste de toutes les options avec leur poids."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix, poids FROM option ORDER BY nom")
        results = cursor.fetchall()
        conn.close()
        return results

    def generer_numero_affaire(self):
        """
        Génère un numéro d'affaire au format YYXXX (ex: 26001 pour la 1ère affaire de 2026)
        """
        annee = datetime.now().strftime("%y")  # "26" pour 2026
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Chercher le dernier numéro de cette année
        cursor.execute("""
            SELECT numero_affaire FROM affaire 
            WHERE numero_affaire LIKE ? 
            ORDER BY numero_affaire DESC LIMIT 1
        """, (f"{annee}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            dernier_numero = int(result[0])
            nouveau_numero = dernier_numero + 1
        else:
            nouveau_numero = int(f"{annee}001")
        
        return str(nouveau_numero)

    def creer_affaire(self, client_id, titre, description=""):
        """
        Crée une nouvelle affaire avec un numéro automatique.
        """
        conn = self.get_connection()
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

    def creer_ou_obtenir_client(self, nom_societe, contact_nom="", contact_email="", contact_tel=""):
        """
        Crée un client ou récupère son ID s'il existe déjà.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si le client existe
        cursor.execute("SELECT id FROM client WHERE nom_societe = ?", (nom_societe,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result[0]
        
        # Créer le client
        cursor.execute("""
            INSERT INTO client (nom_societe, contact_nom, contact_email, contact_telephone)
            VALUES (?, ?, ?, ?)
        """, (nom_societe, contact_nom, contact_email, contact_tel))
        client_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return client_id

    def creer_devis_pour_affaire(self, affaire_id, produits_data, notes=""):
        """
        Crée un nouveau devis pour une affaire avec plusieurs produits.
        produits_data = [(produit_id, quantite, prix_unitaire, [options_ids], [options_perso]), ...]
        options_perso = [(description, prix_demande), ...]
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Calculer la version du devis
            cursor.execute("SELECT MAX(version) FROM devis WHERE affaire_id = ?", (affaire_id,))
            result = cursor.fetchone()
            version = (result[0] or 0) + 1
            
            # Calculer le total
            total = 0
            for item in produits_data:
                prod_id, qte, prix_unit, options_ids = item[0], item[1], item[2], item[3]
                options_perso = item[4] if len(item) > 4 else []
                
                # Prix produit
                subtotal = prix_unit * qte
                # Prix options standard
                if options_ids:
                    cursor.execute(f"""
                        SELECT SUM(prix) FROM option WHERE id IN ({','.join('?' * len(options_ids))})
                    """, options_ids)
                    prix_opts = cursor.fetchone()[0] or 0
                    subtotal += prix_opts * qte
                # Prix options personnalisées (peut être dict ou tuple)
                for opt_perso in options_perso:
                    if isinstance(opt_perso, dict):
                        prix = opt_perso.get('prix')
                    else:
                        prix = opt_perso[1] if len(opt_perso) > 1 else None
                    if prix:
                        subtotal += prix * qte
                total += subtotal
            
            # Créer le devis
            cursor.execute("""
                INSERT INTO devis (affaire_id, version, total_estime, notes)
                VALUES (?, ?, ?, ?)
            """, (affaire_id, version, total, notes))
            devis_id = cursor.lastrowid
            
            # Ajouter les produits au devis
            for item in produits_data:
                prod_id, qte, prix_unit, options_ids = item[0], item[1], item[2], item[3]
                options_perso = item[4] if len(item) > 4 else []
                
                cursor.execute("""
                    INSERT INTO produit_devis (devis_id, produit_id, quantite, prix_unitaire)
                    VALUES (?, ?, ?, ?)
                """, (devis_id, prod_id, qte, prix_unit))
                prod_devis_id = cursor.lastrowid
                
                # Ajouter les options standard pour ce produit
                for opt_id in options_ids:
                    cursor.execute("""
                        INSERT INTO ligne_option_produit_devis (produit_devis_id, option_id)
                        VALUES (?, ?)
                    """, (prod_devis_id, opt_id))
                
                # Ajouter les options personnalisées (avec poids)
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
            print(f"✅ Devis V{version} créé pour l'affaire.")
            return devis_id, version
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur création devis : {e}")
            return None, None
        finally:
            conn.close()

    def repondre_option_standard(self, ligne_option_id, statut, prix_propose=None, commentaire=""):
        """
        Le vendeur répond à une option standard.
        statut = 'accepte', 'refuse', 'contre_proposition'
        """
        conn = self.get_connection()
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
            print(f"❌ Erreur réponse option : {e}")
            return False
        finally:
            conn.close()

    def repondre_option_perso(self, option_perso_id, statut, prix_propose=None, commentaire="", poids=0):
        """
        Le vendeur répond à une option personnalisée.
        statut = 'accepte', 'refuse', 'contre_proposition'
        poids = poids de l'option défini par le vendeur (en kg)
        """
        conn = self.get_connection()
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
            print(f"❌ Erreur réponse option perso : {e}")
            return False
        finally:
            conn.close()

    def repondre_option_standard_acheteur(self, ligne_option_id, statut, commentaire=None):
        """
        Enregistre la réponse de l'acheteur pour une option standard.
        statut: 'accepte', 'refuse'
        """
        conn = self.get_connection()
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
            print(f"❌ Erreur réponse acheteur option standard : {e}")
            return False
        finally:
            conn.close()

    def repondre_option_perso_acheteur(self, option_perso_id, statut, commentaire=None):
        """
        Enregistre la réponse de l'acheteur pour une option personnalisée.
        statut: 'accepte', 'refuse'
        """
        conn = self.get_connection()
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
            print(f"❌ Erreur réponse acheteur option perso : {e}")
            return False
        finally:
            conn.close()

    def get_options_devis_detail(self, devis_id):
        """
        Récupère toutes les options (standard et perso) d'un devis avec leur statut vendeur.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result = {'produits': []}
        
        # Récupérer les produits du devis
        cursor.execute("""
            SELECT pd.id, p.nom, pd.quantite, pd.prix_unitaire
            FROM produit_devis pd
            JOIN produit p ON pd.produit_id = p.id
            WHERE pd.devis_id = ?
        """, (devis_id,))
        
        for pd_id, nom, qte, prix in cursor.fetchall():
            prod_data = {
                'id': pd_id,
                'nom': nom,
                'quantite': qte,
                'prix_unitaire': prix,
                'options_standard': [],
                'options_perso': []
            }
            
            # Options standard
            cursor.execute("""
                SELECT lopd.id, o.nom, o.prix, lopd.statut_vendeur, lopd.prix_propose, lopd.commentaire_vendeur,
                       lopd.statut_acheteur, lopd.commentaire_acheteur
                FROM ligne_option_produit_devis lopd
                JOIN option o ON lopd.option_id = o.id
                WHERE lopd.produit_devis_id = ?
            """, (pd_id,))
            
            for row in cursor.fetchall():
                prod_data['options_standard'].append({
                    'id': row[0],
                    'nom': row[1],
                    'prix': row[2],
                    'statut_vendeur': row[3],
                    'prix_propose': row[4],
                    'commentaire_vendeur': row[5],
                    'statut_acheteur': row[6],
                    'commentaire_acheteur': row[7]
                })
            
            # Options personnalisées
            cursor.execute("""
                SELECT id, description, prix_demande, statut_vendeur, prix_propose, commentaire_vendeur,
                       statut_acheteur, commentaire_acheteur
                FROM option_personnalisee
                WHERE produit_devis_id = ?
            """, (pd_id,))
            
            for row in cursor.fetchall():
                prod_data['options_perso'].append({
                    'id': row[0],
                    'description': row[1],
                    'prix_demande': row[2],
                    'statut_vendeur': row[3],
                    'prix_propose': row[4],
                    'commentaire_vendeur': row[5],
                    'statut_acheteur': row[6],
                    'commentaire_acheteur': row[7]
                })
            
            result['produits'].append(prod_data)
        
        conn.close()
        return result

    def get_devis_info(self, devis_id):
        """Récupère les infos de base d'un devis."""
        conn = self.get_connection()
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

    def creer_nouvelle_version_devis(self, devis_id_source, role_createur):
        """
        Crée une nouvelle version du devis en copiant toutes les données
        avec les réponses actuelles.
        role_createur: 'vendeur' ou 'acheteur'
        Retourne le nouveau devis_id et la nouvelle version.
        
        Règles de calcul du prix:
        - Option refusée par vendeur OU refusée par acheteur (contre-prop) → 0€
        - Option acceptée par vendeur → prix catalogue (standard) ou prix_demande (perso)
        - Contre-proposition acceptée par acheteur → prix_propose
        - Option en attente → prix catalogue ou prix_demande
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Récupérer info du devis source
            cursor.execute("""
                SELECT affaire_id, total_estime, notes FROM devis WHERE id = ?
            """, (devis_id_source,))
            affaire_id, old_total, notes = cursor.fetchone()
            
            # Calculer la nouvelle version
            cursor.execute("SELECT MAX(version) FROM devis WHERE affaire_id = ?", (affaire_id,))
            max_version = cursor.fetchone()[0] or 0
            new_version = max_version + 1
            
            # Recalculer le total en excluant les options refusées
            new_total = 0
            
            cursor.execute("""
                SELECT id, produit_id, quantite, prix_unitaire FROM produit_devis WHERE devis_id = ?
            """, (devis_id_source,))
            produits_data = cursor.fetchall()
            
            for old_pd_id, prod_id, qte, prix_unit in produits_data:
                # Prix de base du produit (toujours inclus)
                new_total += prix_unit * qte
                
                # Options standard
                cursor.execute("""
                    SELECT o.prix, lopd.statut_vendeur, lopd.prix_propose, lopd.statut_acheteur
                    FROM ligne_option_produit_devis lopd
                    JOIN option o ON lopd.option_id = o.id
                    WHERE lopd.produit_devis_id = ?
                """, (old_pd_id,))
                
                for prix_cat, stat_v, prix_prop, stat_a in cursor.fetchall():
                    # Option refusée = 0€
                    if stat_v == 'refuse' or stat_a == 'refuse':
                        continue  # Ne pas ajouter au total
                    
                    # Contre-proposition acceptée par client = prix_propose
                    if stat_v == 'contre_proposition' and stat_a == 'accepte' and prix_prop:
                        new_total += prix_prop * qte
                    # Contre-proposition en attente = prix_propose (provisoire)
                    elif stat_v == 'contre_proposition' and prix_prop:
                        new_total += prix_prop * qte
                    # Option acceptée par vendeur ou en attente = prix catalogue
                    elif stat_v in ('accepte', 'en_attente'):
                        new_total += prix_cat * qte
                
                # Options personnalisées
                cursor.execute("""
                    SELECT prix_demande, statut_vendeur, prix_propose, statut_acheteur
                    FROM option_personnalisee WHERE produit_devis_id = ?
                """, (old_pd_id,))
                
                for prix_dem, stat_v, prix_prop, stat_a in cursor.fetchall():
                    # Option refusée = 0€
                    if stat_v == 'refuse' or stat_a == 'refuse':
                        continue  # Ne pas ajouter au total
                    
                    # Contre-proposition acceptée par client = prix_propose
                    if stat_v == 'contre_proposition' and stat_a == 'accepte' and prix_prop:
                        new_total += prix_prop * qte
                    # Contre-proposition en attente = prix_propose (provisoire)
                    elif stat_v == 'contre_proposition' and prix_prop:
                        new_total += prix_prop * qte
                    # Option acceptée par vendeur = prix_demande
                    elif stat_v == 'accepte' and prix_dem:
                        new_total += prix_dem * qte
                    # Option en attente = prix_demande (provisoire)
                    elif stat_v == 'en_attente' and prix_dem:
                        new_total += prix_dem * qte
            
            # Créer le nouveau devis avec le nouveau total
            cursor.execute("""
                INSERT INTO devis (affaire_id, version, total_estime, notes)
                VALUES (?, ?, ?, ?)
            """, (affaire_id, new_version, new_total, f"{notes or ''}\n[V{new_version} par {role_createur}]"))
            new_devis_id = cursor.lastrowid
            
            # Copier les produits (réutiliser produits_data déjà chargé)
            for old_pd_id, prod_id, qte, prix in produits_data:
                cursor.execute("""
                    INSERT INTO produit_devis (devis_id, produit_id, quantite, prix_unitaire)
                    VALUES (?, ?, ?, ?)
                """, (new_devis_id, prod_id, qte, prix))
                new_pd_id = cursor.lastrowid
                
                # Copier les options standard avec leurs statuts
                cursor.execute("""
                    SELECT option_id, statut_vendeur, prix_propose, commentaire_vendeur, 
                           statut_acheteur, commentaire_acheteur
                    FROM ligne_option_produit_devis WHERE produit_devis_id = ?
                """, (old_pd_id,))
                
                for opt_id, stat_v, prix_v, comm_v, stat_a, comm_a in cursor.fetchall():
                    cursor.execute("""
                        INSERT INTO ligne_option_produit_devis 
                        (produit_devis_id, option_id, statut_vendeur, prix_propose, 
                         commentaire_vendeur, statut_acheteur, commentaire_acheteur)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (new_pd_id, opt_id, stat_v, prix_v, comm_v, stat_a, comm_a))
                
                # Copier les options personnalisées
                cursor.execute("""
                    SELECT description, prix_demande, poids, statut_vendeur, prix_propose, 
                           commentaire_vendeur, statut_acheteur, commentaire_acheteur
                    FROM option_personnalisee WHERE produit_devis_id = ?
                """, (old_pd_id,))
                
                for desc, prix_d, poids, stat_v, prix_v, comm_v, stat_a, comm_a in cursor.fetchall():
                    cursor.execute("""
                        INSERT INTO option_personnalisee 
                        (produit_devis_id, description, prix_demande, poids, statut_vendeur, 
                         prix_propose, commentaire_vendeur, statut_acheteur, commentaire_acheteur)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_pd_id, desc, prix_d, poids, stat_v, prix_v, comm_v, stat_a, comm_a))
            
            conn.commit()
            print(f"✅ Nouvelle version V{new_version} créée. Total: {new_total}€")
            return new_devis_id, new_version
        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur création nouvelle version : {e}")
            return None, None
        finally:
            conn.close()

    def ajouter_commentaire(self, affaire_id, auteur, role, contenu):
        """
        Ajoute un commentaire à une affaire.
        role = 'acheteur' ou 'vendeur'
        """
        conn = self.get_connection()
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

    def get_tous_clients(self):
        """Récupère la liste de tous les clients."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nom_societe, contact_nom, contact_email, contact_telephone 
            FROM client ORDER BY nom_societe
        """)
        results = cursor.fetchall()
        conn.close()
        return results

    def cloturer_affaire(self, affaire_id, resultat, commentaire=""):
        """
        Clôture une affaire avec le résultat (gagne/perdu).
        resultat: 'gagne', 'perdu', 'annule'
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE affaire 
                SET statut = ?, date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (resultat, affaire_id))
            
            # Ajouter un commentaire de clôture
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
        """
        Vérifie si une affaire est clôturée (gagne, perdu, annule).
        Retourne (True/False, statut)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT statut FROM affaire WHERE id = ?", (affaire_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            statut = result[0]
            if statut in ('gagne', 'perdu', 'annule'):
                return True, statut
        return False, None

    def get_commentaires_affaire(self, affaire_id):
        """
        Récupère tous les commentaires d'une affaire.
        """
        conn = self.get_connection()
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

    def get_liste_affaires(self):
        """
        Récupère la liste de toutes les affaires avec infos client.
        """
        conn = self.get_connection()
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

    def get_devis_affaire(self, affaire_id):
        """
        Récupère tous les devis d'une affaire.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, version, date_creation, total_estime, statut, notes
            FROM devis
            WHERE affaire_id = ?
            ORDER BY version DESC
        """, (affaire_id,))
        
        results = cursor.fetchall()
        conn.close()
        return results

    def get_produits_devis(self, devis_id):
        """
        Récupère les produits et leurs options pour un devis.
        """
        conn = self.get_connection()
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
            # Récupérer les options
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

    def get_affaire_details(self, affaire_id):
        """
        Récupère les détails complets d'une affaire.
        """
        conn = self.get_connection()
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

    def mettre_a_jour_statut_affaire(self, affaire_id, nouveau_statut):
        """
        Met à jour le statut d'une affaire.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE affaire 
            SET statut = ?, date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nouveau_statut, affaire_id))
        
        conn.commit()
        conn.close()

    def add_demo_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM produit")
        if cursor.fetchone()[0] == 0:
            print("⚠️ Ajout des données de démonstration...")
            
            # Produits
            produits = [
                ("Bras Robotique 6 axes", 50.0, 25000.0),
                ("Table Vibrante Industrielle", 500.0, 45000.0),
                ("Banc d'Essai Hydraulique", 1000.0, 75000.0),
                ("Plateforme de Simulation", 200.0, 35000.0),
                ("Système de Positionnement", 100.0, 18000.0)
            ]
            cursor.executemany("INSERT INTO produit (nom, charge_max, prix_base) VALUES (?, ?, ?)", produits)
            
            # Options UNIVERSELLES (disponibles pour tous les produits)
            # (nom, prix, poids, universelle=1)
            options_universelles = [
                ("Extension de garantie 3 ans", 4000.0, 0, 1),
                ("Formation opérateur (2 jours)", 2500.0, 0, 1),
                ("Caisse de transport renforcée", 1200.0, 15.0, 1),
                ("Logiciel de pilotage avancé", 6000.0, 0, 1),
            ]
            cursor.executemany("INSERT INTO option (nom, prix, poids, universelle) VALUES (?, ?, ?, ?)", options_universelles)
            
            # Options SPÉCIFIQUES (liées à certains produits)
            options_specifiques = [
                # Bras Robotique
                ("Pince de préhension pneumatique", 3500.0, 4.0, 0),
                ("Capteur de couple intégré", 4200.0, 1.5, 0),
                ("Vision industrielle 2D", 8500.0, 2.0, 0),
                ("Interface ROS2", 3000.0, 0, 0),
                
                # Table Vibrante
                ("Amplificateur de puissance 5kN", 12000.0, 35.0, 0),
                ("Accéléromètres triaxiaux", 2800.0, 0.5, 0),
                ("Système de refroidissement actif", 5500.0, 18.0, 0),
                ("Plateau aluminium usiné", 4500.0, 25.0, 0),
                
                # Banc d'Essai Hydraulique
                ("Groupe hydraulique haute pression", 18000.0, 120.0, 0),
                ("Capteurs de pression 0-500 bar", 3200.0, 2.0, 0),
                ("Vérins servo-hydrauliques", 9500.0, 45.0, 0),
                ("Circuit de filtration", 2800.0, 15.0, 0),
                
                # Plateforme de Simulation
                ("Système 6 DDL complet", 25000.0, 80.0, 0),
                ("Interface de réalité virtuelle", 7500.0, 3.0, 0),
                ("Siège dynamique intégré", 8000.0, 35.0, 0),
                ("Écrans immersifs 180°", 15000.0, 50.0, 0),
                
                # Système de Positionnement
                ("Encodeurs absolus haute résolution", 4500.0, 1.0, 0),
                ("Contrôleur multi-axes", 6500.0, 5.0, 0),
                ("Interface EtherCAT", 2200.0, 0.5, 0),
                ("Règles optiques nanométriques", 12000.0, 3.0, 0),
            ]
            cursor.executemany("INSERT INTO option (nom, prix, poids, universelle) VALUES (?, ?, ?, ?)", options_specifiques)
            
            # Liaison Produit-Option (options spécifiques par produit)
            # Récupérer les IDs
            cursor.execute("SELECT id, nom FROM produit")
            produits_db = {nom: id for id, nom in cursor.fetchall()}
            
            cursor.execute("SELECT id, nom FROM option WHERE universelle = 0")
            options_db = {nom: id for id, nom in cursor.fetchall()}
            
            liaisons = [
                # Bras Robotique 6 axes
                (produits_db["Bras Robotique 6 axes"], options_db["Pince de préhension pneumatique"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Capteur de couple intégré"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Vision industrielle 2D"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Interface ROS2"]),
                
                # Table Vibrante Industrielle
                (produits_db["Table Vibrante Industrielle"], options_db["Amplificateur de puissance 5kN"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Accéléromètres triaxiaux"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Système de refroidissement actif"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Plateau aluminium usiné"]),
                
                # Banc d'Essai Hydraulique
                (produits_db["Banc d'Essai Hydraulique"], options_db["Groupe hydraulique haute pression"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Capteurs de pression 0-500 bar"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Vérins servo-hydrauliques"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Circuit de filtration"]),
                
                # Plateforme de Simulation
                (produits_db["Plateforme de Simulation"], options_db["Système 6 DDL complet"]),
                (produits_db["Plateforme de Simulation"], options_db["Interface de réalité virtuelle"]),
                (produits_db["Plateforme de Simulation"], options_db["Siège dynamique intégré"]),
                (produits_db["Plateforme de Simulation"], options_db["Écrans immersifs 180°"]),
                
                # Système de Positionnement
                (produits_db["Système de Positionnement"], options_db["Encodeurs absolus haute résolution"]),
                (produits_db["Système de Positionnement"], options_db["Contrôleur multi-axes"]),
                (produits_db["Système de Positionnement"], options_db["Interface EtherCAT"]),
                (produits_db["Système de Positionnement"], options_db["Règles optiques nanométriques"]),
            ]
            cursor.executemany("INSERT INTO produit_option (produit_id, option_id) VALUES (?, ?)", liaisons)
            
            conn.commit()
        
        conn.close()

    def enregistrer_devis(self, nom_client, nom_produit, total_estime, liste_options):
        """
        Sauvegarde transactionnelle : Client -> Devis -> Options (méthode legacy)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. ID Produit
            cursor.execute("SELECT id FROM produit WHERE nom = ?", (nom_produit,))
            prod_res = cursor.fetchone()
            if not prod_res: raise Exception("Produit inconnu")
            prod_id = prod_res[0]

            # 2. Création Client
            cursor.execute("INSERT INTO client (nom_societe) VALUES (?)", (nom_client,))
            client_id = cursor.lastrowid

            # 3. Création Devis
            cursor.execute("""
                INSERT INTO devis (client_id, total_estime) VALUES (?, ?)
            """, (client_id, total_estime))
            devis_id = cursor.lastrowid

            # 4. Liaison Options
            for nom_opt, _ in liste_options:
                cursor.execute("SELECT id FROM option WHERE nom = ?", (nom_opt,))
                opt_res = cursor.fetchone()
                if opt_res:
                    cursor.execute("INSERT INTO ligne_option_devis VALUES (?, ?)", (devis_id, opt_res[0]))

            conn.commit()
            print(f"✅ Devis N°{devis_id} sauvegardé en BDD.")
            return devis_id

        except Exception as e:
            conn.rollback()
            print(f"❌ Erreur SQL : {e}")
            return None
        finally:
            conn.close()
    
    def get_historique_devis(self):
        """
        Récupère la liste des devis avec les noms des clients et produits
        via des jointures SQL (nouveau schéma avec affaires).
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                d.id, 
                d.date_creation, 
                COALESCE(c.nom_societe, 'N/A') as client,
                a.numero_affaire || ' V' || d.version as reference,
                d.total_estime 
            FROM devis d
            LEFT JOIN affaire a ON d.affaire_id = a.id
            LEFT JOIN client c ON a.client_id = c.id
            ORDER BY d.date_creation DESC
        """
        
        cursor.execute(query)
        resultats = cursor.fetchall()
        conn.close()
        return resultats