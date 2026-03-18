# ──────────────────────────────────────────────────────────────────────────────
# src/models/database.py — Connexion SQLite, schéma et données de démo
# ──────────────────────────────────────────────────────────────────────────────
# Gère la connexion à la base SQLite (data/devis_database.db), la création
# automatique de toutes les tables au démarrage (produits, options, clients,
# affaires, devis, commentaires…) et l'insertion de données de démonstration
# pour permettre un test immédiat de l'application.
# ──────────────────────────────────────────────────────────────────────────────
import sqlite3
import os


class Database:
    """Connexion SQLite + création des tables + données de démo."""

    def __init__(self, db_name="devis_database.db"):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.db_path = os.path.join(base_dir, "data", db_name)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()
        self.add_demo_data()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    # ──────────────────────────────────────────────────────────────
    # Schéma
    # ──────────────────────────────────────────────────────────────
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                charge_max REAL,
                prix_base REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prix REAL,
                poids REAL DEFAULT 0,
                universelle INTEGER DEFAULT 0
            )
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_societe TEXT NOT NULL,
                siret TEXT UNIQUE,
                contact_nom TEXT,
                contact_prenom TEXT,
                contact_service TEXT,
                contact_email TEXT,
                contact_telephone TEXT,
                indicatif_tel TEXT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendeur (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nom TEXT,
                prenom TEXT,
                email TEXT,
                date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        self._migrate_schema()
        print("✅ Base de données vérifiée.")

    # ──────────────────────────────────────────────────────────────
    # Migration progressive (colonnes manquantes)
    # ──────────────────────────────────────────────────────────────
    def _migrate_schema(self):
        """Ajoute les colonnes manquantes aux tables existantes."""
        conn = self.get_connection()
        cursor = conn.cursor()
        for col, typedef in [
            ('siret', 'TEXT'),
            ('contact_prenom', 'TEXT'),
            ('contact_service', 'TEXT'),
            ('password_hash', 'TEXT'),
            ('username', 'TEXT'),
            ('indicatif_tel', 'TEXT'),
        ]:
            try:
                cursor.execute(f"ALTER TABLE client ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass  # Colonne existe déjà
        for col, typedef in [
            ('email', 'TEXT'),
        ]:
            try:
                cursor.execute(f"ALTER TABLE vendeur ADD COLUMN {col} {typedef}")
            except sqlite3.OperationalError:
                pass
        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────────────────────
    # Données de démonstration
    # ──────────────────────────────────────────────────────────────
    def add_demo_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT count(*) FROM produit")
        if cursor.fetchone()[0] == 0:
            print("⚠️ Ajout des données de démonstration...")

            produits = [
                ("Bras Robotique 6 axes", 50.0, 25000.0),
                ("Table Vibrante Industrielle", 500.0, 45000.0),
                ("Banc d'Essai Hydraulique", 1000.0, 75000.0),
                ("Plateforme de Simulation", 200.0, 35000.0),
                ("Système de Positionnement", 100.0, 18000.0),
            ]
            cursor.executemany(
                "INSERT INTO produit (nom, charge_max, prix_base) VALUES (?, ?, ?)", produits)

            options_universelles = [
                ("Extension de garantie 3 ans", 4000.0, 0, 1),
                ("Formation opérateur (2 jours)", 2500.0, 0, 1),
                ("Caisse de transport renforcée", 1200.0, 15.0, 1),
                ("Logiciel de pilotage avancé", 6000.0, 0, 1),
            ]
            cursor.executemany(
                "INSERT INTO option (nom, prix, poids, universelle) VALUES (?, ?, ?, ?)",
                options_universelles)

            options_specifiques = [
                ("Pince de préhension pneumatique", 3500.0, 4.0, 0),
                ("Capteur de couple intégré", 4200.0, 1.5, 0),
                ("Vision industrielle 2D", 8500.0, 2.0, 0),
                ("Interface ROS2", 3000.0, 0, 0),
                ("Amplificateur de puissance 5kN", 12000.0, 35.0, 0),
                ("Accéléromètres triaxiaux", 2800.0, 0.5, 0),
                ("Système de refroidissement actif", 5500.0, 18.0, 0),
                ("Plateau aluminium usiné", 4500.0, 25.0, 0),
                ("Groupe hydraulique haute pression", 18000.0, 120.0, 0),
                ("Capteurs de pression 0-500 bar", 3200.0, 2.0, 0),
                ("Vérins servo-hydrauliques", 9500.0, 45.0, 0),
                ("Circuit de filtration", 2800.0, 15.0, 0),
                ("Système 6 DDL complet", 25000.0, 80.0, 0),
                ("Interface de réalité virtuelle", 7500.0, 3.0, 0),
                ("Siège dynamique intégré", 8000.0, 35.0, 0),
                ("Écrans immersifs 180°", 15000.0, 50.0, 0),
                ("Encodeurs absolus haute résolution", 4500.0, 1.0, 0),
                ("Contrôleur multi-axes", 6500.0, 5.0, 0),
                ("Interface EtherCAT", 2200.0, 0.5, 0),
                ("Règles optiques nanométriques", 12000.0, 3.0, 0),
            ]
            cursor.executemany(
                "INSERT INTO option (nom, prix, poids, universelle) VALUES (?, ?, ?, ?)",
                options_specifiques)

            cursor.execute("SELECT id, nom FROM produit")
            produits_db = {nom: id for id, nom in cursor.fetchall()}

            cursor.execute("SELECT id, nom FROM option WHERE universelle = 0")
            options_db = {nom: id for id, nom in cursor.fetchall()}

            liaisons = [
                (produits_db["Bras Robotique 6 axes"], options_db["Pince de préhension pneumatique"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Capteur de couple intégré"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Vision industrielle 2D"]),
                (produits_db["Bras Robotique 6 axes"], options_db["Interface ROS2"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Amplificateur de puissance 5kN"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Accéléromètres triaxiaux"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Système de refroidissement actif"]),
                (produits_db["Table Vibrante Industrielle"], options_db["Plateau aluminium usiné"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Groupe hydraulique haute pression"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Capteurs de pression 0-500 bar"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Vérins servo-hydrauliques"]),
                (produits_db["Banc d'Essai Hydraulique"], options_db["Circuit de filtration"]),
                (produits_db["Plateforme de Simulation"], options_db["Système 6 DDL complet"]),
                (produits_db["Plateforme de Simulation"], options_db["Interface de réalité virtuelle"]),
                (produits_db["Plateforme de Simulation"], options_db["Siège dynamique intégré"]),
                (produits_db["Plateforme de Simulation"], options_db["Écrans immersifs 180°"]),
                (produits_db["Système de Positionnement"], options_db["Encodeurs absolus haute résolution"]),
                (produits_db["Système de Positionnement"], options_db["Contrôleur multi-axes"]),
                (produits_db["Système de Positionnement"], options_db["Interface EtherCAT"]),
                (produits_db["Système de Positionnement"], options_db["Règles optiques nanométriques"]),
            ]
            cursor.executemany(
                "INSERT INTO produit_option (produit_id, option_id) VALUES (?, ?)", liaisons)

            conn.commit()

        # Compte vendeur par défaut
        cursor.execute("SELECT count(*) FROM vendeur")
        if cursor.fetchone()[0] == 0:
            from src.utils.auth import hash_password
            cursor.execute("""
                INSERT INTO vendeur (username, password_hash, nom, prenom)
                VALUES (?, ?, ?, ?)
            """, ("admin", hash_password("admin"), "Administrateur", "Système"))
            conn.commit()
            print("⚠️ Compte vendeur par défaut créé (admin/admin).")

        conn.close()
