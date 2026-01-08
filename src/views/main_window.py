import os
import datetime
from PyQt6.QtWidgets import (QMainWindow, QLabel, QWidget, QComboBox, 
                             QFormLayout, QCheckBox, QGroupBox, QVBoxLayout, 
                             QPushButton, QMessageBox, QLineEdit, QHBoxLayout,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTextEdit, QSpinBox, QScrollArea, QFrame, QSplitter,
                             QListWidget, QListWidgetItem, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from fpdf import FPDF
from src.models.db_manager import DatabaseManager


class ProduitConfigWidget(QFrame):
    """Widget pour configurer un produit avec ses options."""
    
    def __init__(self, db, index, on_change_callback, on_remove_callback):
        super().__init__()
        self.db = db
        self.index = index
        self.on_change = on_change_callback
        self.on_remove = on_remove_callback
        self.checkboxes = []
        self.options_perso_widgets = []
        
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame { background-color: #2d3436; border-radius: 5px; padding: 10px; }
            QLabel { color: #dfe6e9; }
            QComboBox { color: #dfe6e9; background-color: #636e72; border: 1px solid #636e72; }
            QSpinBox { color: #dfe6e9; background-color: #636e72; border: 1px solid #636e72; }
            QCheckBox { color: #dfe6e9; }
            QGroupBox { color: #74b9ff; font-weight: bold; }
            QLineEdit { color: #dfe6e9; background-color: #636e72; border: 1px solid #636e72; }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header avec bouton supprimer
        header = QHBoxLayout()
        self.lbl_title = QLabel(f"🔷 Produit #{index + 1}")
        self.lbl_title.setStyleSheet("font-weight: bold; color: #74b9ff;")
        header.addWidget(self.lbl_title)
        header.addStretch()
        
        self.btn_remove = QPushButton("❌")
        self.btn_remove.setFixedSize(30, 30)
        self.btn_remove.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 5px;")
        self.btn_remove.clicked.connect(lambda: self.on_remove(self))
        header.addWidget(self.btn_remove)
        layout.addLayout(header)
        
        # Sélection modèle et quantité
        model_layout = QHBoxLayout()
        
        self.combo_modele = QComboBox()
        self.combo_modele.currentIndexChanged.connect(self.on_change)
        model_layout.addWidget(QLabel("Modèle:"))
        model_layout.addWidget(self.combo_modele, 2)
        
        model_layout.addWidget(QLabel("Qté:"))
        self.spin_quantite = QSpinBox()
        self.spin_quantite.setMinimum(1)
        self.spin_quantite.setMaximum(99)
        self.spin_quantite.setValue(1)
        self.spin_quantite.valueChanged.connect(self.on_change)
        model_layout.addWidget(self.spin_quantite)
        
        layout.addLayout(model_layout)
        
        # Options standard
        self.group_options = QGroupBox("Options catalogue")
        self.layout_options = QVBoxLayout()
        self.group_options.setLayout(self.layout_options)
        layout.addWidget(self.group_options)
        
        # Options personnalisées (demandes spéciales)
        self.group_options_perso = QGroupBox("🔧 Options personnalisées (demandes spéciales)")
        self.layout_options_perso = QVBoxLayout()
        self.group_options_perso.setLayout(self.layout_options_perso)
        
        # Bouton pour ajouter une option perso
        btn_add_perso = QPushButton("➕ Ajouter une demande spéciale")
        btn_add_perso.setStyleSheet("background-color: #8e44ad; color: white; padding: 5px;")
        btn_add_perso.clicked.connect(self.ajouter_option_perso)
        self.layout_options_perso.addWidget(btn_add_perso)
        
        layout.addWidget(self.group_options_perso)
        
        # Sous-total
        self.lbl_subtotal = QLabel("Sous-total: 0.00 €")
        self.lbl_subtotal.setStyleSheet("font-weight: bold; color: #00b894;")
        layout.addWidget(self.lbl_subtotal)
        
        self.charger_modeles()
        self.charger_options()
    
    def ajouter_option_perso(self):
        """Ajoute un champ pour une option personnalisée."""
        container = QFrame()
        container.setStyleSheet("background-color: #6c5ce7; border-radius: 3px; padding: 5px;")
        h_layout = QHBoxLayout()
        container.setLayout(h_layout)
        
        input_desc = QLineEdit()
        input_desc.setPlaceholderText("Description de l'option souhaitée...")
        input_desc.textChanged.connect(self.on_change)
        h_layout.addWidget(input_desc, 3)
        
        h_layout.addWidget(QLabel("Prix souhaité:"))
        input_prix = QSpinBox()
        input_prix.setMaximum(999999)
        input_prix.setSuffix(" €")
        input_prix.valueChanged.connect(self.on_change)
        h_layout.addWidget(input_prix)
        
        btn_suppr = QPushButton("🗑️")
        btn_suppr.setFixedSize(30, 30)
        btn_suppr.clicked.connect(lambda: self.supprimer_option_perso(container))
        h_layout.addWidget(btn_suppr)
        
        # Insérer avant le bouton "Ajouter"
        self.layout_options_perso.insertWidget(self.layout_options_perso.count() - 1, container)
        self.options_perso_widgets.append((container, input_desc, input_prix))
        self.on_change()
    
    def supprimer_option_perso(self, container):
        """Supprime une option personnalisée."""
        for item in self.options_perso_widgets:
            if item[0] == container:
                self.options_perso_widgets.remove(item)
                break
        self.layout_options_perso.removeWidget(container)
        container.deleteLater()
        self.on_change()
    
    def charger_modeles(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix_base FROM produit")
        for id_prod, nom, prix in cursor.fetchall():
            self.combo_modele.addItem(f"{nom} ({prix} €)", (id_prod, prix))
        conn.close()
    
    def charger_options(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix FROM option")
        for id_opt, nom, prix in cursor.fetchall():
            chk = QCheckBox(f"{nom} (+{prix} €)")
            chk.setProperty("option_id", id_opt)
            chk.setProperty("prix_option", prix)
            chk.toggled.connect(self.on_change)
            self.layout_options.addWidget(chk)
            self.checkboxes.append(chk)
        conn.close()
    
    def get_data(self):
        """Retourne (produit_id, quantite, prix_unitaire, [option_ids], [(desc, prix)])"""
        data = self.combo_modele.currentData()
        if not data:
            return None
        prod_id, prix_base = data
        quantite = self.spin_quantite.value()
        options_ids = [chk.property("option_id") for chk in self.checkboxes if chk.isChecked()]
        
        # Options personnalisées
        options_perso = []
        for container, input_desc, input_prix in self.options_perso_widgets:
            desc = input_desc.text().strip()
            prix = input_prix.value()
            if desc:  # Seulement si description renseignée
                options_perso.append((desc, prix if prix > 0 else None))
        
        return (prod_id, quantite, prix_base, options_ids, options_perso)
    
    def calculer_subtotal(self):
        data = self.combo_modele.currentData()
        if not data:
            return 0
        _, prix_base = data
        qte = self.spin_quantite.value()
        prix_options = sum(chk.property("prix_option") for chk in self.checkboxes if chk.isChecked())
        
        # Ajouter les options personnalisées avec prix
        prix_options_perso = 0
        for container, input_desc, input_prix in self.options_perso_widgets:
            if input_desc.text().strip():
                prix_options_perso += input_prix.value()
        
        subtotal = (prix_base + prix_options + prix_options_perso) * qte
        self.lbl_subtotal.setText(f"Sous-total: {subtotal:,.2f} €".replace(",", " "))
        return subtotal


class CommentaireWidget(QFrame):
    """Widget pour afficher un commentaire."""
    
    def __init__(self, auteur, role, contenu, date):
        super().__init__()
        
        is_vendeur = role == 'vendeur'
        bg_color = "#00b894" if is_vendeur else "#0984e3"
        text_color = "#ffffff"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 8px;
                margin: 2px;
            }}
            QLabel {{
                color: {text_color};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        # Header
        header = QLabel(f"<b>{auteur}</b> ({role}) - {date[:16]}")
        header.setStyleSheet(f"font-size: 10px; color: rgba(255,255,255,0.8);")
        layout.addWidget(header)
        
        # Contenu
        content = QLabel(contenu)
        content.setWordWrap(True)
        content.setStyleSheet(f"color: {text_color};")
        layout.addWidget(content)


class NouvelleAffaireDialog(QDialog):
    """Dialog pour créer une nouvelle affaire."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle Affaire")
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Client
        self.input_client = QLineEdit()
        self.input_client.setPlaceholderText("Ex: CNRS, Airbus...")
        layout.addRow("Client :", self.input_client)
        
        self.input_contact = QLineEdit()
        self.input_contact.setPlaceholderText("Nom du contact")
        layout.addRow("Contact :", self.input_contact)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("email@example.com")
        layout.addRow("Email :", self.input_email)
        
        # Affaire
        self.input_titre = QLineEdit()
        self.input_titre.setPlaceholderText("Ex: Commande équipement pour projet industriel")
        layout.addRow("Titre affaire :", self.input_titre)
        
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Description détaillée...")
        self.input_description.setMaximumHeight(100)
        layout.addRow("Description :", self.input_description)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_data(self):
        return {
            'client': self.input_client.text().strip(),
            'contact': self.input_contact.text().strip(),
            'email': self.input_email.text().strip(),
            'titre': self.input_titre.text().strip(),
            'description': self.input_description.toPlainText().strip()
        }


class ReponseVendeurDialog(QDialog):
    """Dialog pour que le vendeur réponde aux options d'un devis."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        self.reponses = []  # Liste des réponses à sauvegarder
        
        self.setWindowTitle("Réponse Vendeur - Évaluation du devis")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        lbl = QLabel("🔍 Évaluer les options demandées par le client")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #74b9ff;")
        layout.addWidget(lbl)
        
        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        self.main_layout = QVBoxLayout()
        container.setLayout(self.main_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Charger les données
        self.charger_options()
        
        # Boutons
        btns = QHBoxLayout()
        btn_save = QPushButton("💾 Sauvegarder les réponses")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_save.clicked.connect(self.sauvegarder_reponses)
        btns.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        
        layout.addLayout(btns)
    
    def charger_options(self):
        """Charge toutes les options du devis."""
        data = self.db.get_options_devis_detail(self.devis_id)
        
        for prod_data in data['produits']:
            # Frame pour chaque produit
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px; border: 1px solid #636e72;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl_prod = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl_prod.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl_prod)
            
            # Options standard
            if prod_data['options_standard']:
                frame_layout.addWidget(QLabel("📦 Options catalogue:"))
                for opt in prod_data['options_standard']:
                    self.ajouter_ligne_option(frame_layout, opt, 'standard')
            
            # Options personnalisées
            if prod_data['options_perso']:
                frame_layout.addWidget(QLabel("🔧 Demandes spéciales:"))
                for opt in prod_data['options_perso']:
                    self.ajouter_ligne_option(frame_layout, opt, 'perso')
            
            self.main_layout.addWidget(frame)
        
        self.main_layout.addStretch()
    
    def ajouter_ligne_option(self, layout, opt, type_opt):
        """Ajoute une ligne pour répondre à une option."""
        row = QFrame()
        row.setStyleSheet("background-color: #636e72; padding: 5px; margin: 2px; border-radius: 3px;")
        row_layout = QHBoxLayout()
        row.setLayout(row_layout)
        
        # Info option
        if type_opt == 'standard':
            lbl = QLabel(f"• {opt['nom']} - {opt['prix']} €")
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "Prix à définir"
            lbl = QLabel(f"• {opt['description']} - {prix_txt}")
        lbl.setMinimumWidth(250)
        lbl.setStyleSheet("color: #dfe6e9;")
        row_layout.addWidget(lbl)
        
        # Statut actuel
        statut = opt['statut_vendeur'] or 'en_attente'
        
        # ComboBox statut
        combo = QComboBox()
        combo.addItems(["en_attente", "accepte", "refuse", "contre_proposition"])
        combo.setCurrentText(statut)
        combo.setStyleSheet("min-width: 120px;")
        row_layout.addWidget(combo)
        
        # Prix proposé
        row_layout.addWidget(QLabel("Prix:"))
        spin_prix = QSpinBox()
        spin_prix.setMaximum(999999)
        spin_prix.setSuffix(" €")
        if opt['prix_propose']:
            spin_prix.setValue(int(opt['prix_propose']))
        elif type_opt == 'standard':
            spin_prix.setValue(int(opt['prix']))
        elif opt['prix_demande']:
            spin_prix.setValue(int(opt['prix_demande']))
        row_layout.addWidget(spin_prix)
        
        # Commentaire
        input_comm = QLineEdit()
        input_comm.setPlaceholderText("Commentaire...")
        if opt['commentaire_vendeur']:
            input_comm.setText(opt['commentaire_vendeur'])
        input_comm.setMinimumWidth(150)
        row_layout.addWidget(input_comm)
        
        layout.addWidget(row)
        
        # Stocker la référence pour sauvegarde
        self.reponses.append({
            'type': type_opt,
            'id': opt['id'],
            'combo': combo,
            'spin_prix': spin_prix,
            'input_comm': input_comm
        })
    
    def sauvegarder_reponses(self):
        """Sauvegarde toutes les réponses du vendeur."""
        for rep in self.reponses:
            statut = rep['combo'].currentText()
            prix = rep['spin_prix'].value() if rep['spin_prix'].value() > 0 else None
            commentaire = rep['input_comm'].text().strip()
            
            if rep['type'] == 'standard':
                self.db.repondre_option_standard(rep['id'], statut, prix, commentaire)
            else:
                self.db.repondre_option_perso(rep['id'], statut, prix, commentaire)
        
        QMessageBox.information(self, "Succès", "Réponses sauvegardées !")
        self.accept()


class DetailDevisDialog(QDialog):
    """Dialog pour afficher le détail d'un devis avec les réponses vendeur et acheteur."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        
        self.setWindowTitle(f"📋 Détail du devis #{devis_id}")
        self.setMinimumSize(900, 650)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        lbl = QLabel("📋 Récapitulatif du devis avec réponses vendeur/acheteur")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #74b9ff;")
        layout.addWidget(lbl)
        
        # Légende
        legende = QHBoxLayout()
        legende.addWidget(QLabel("Légende: "))
        for txt, color in [("En attente", "#95a5a6"), ("Accepté", "#27ae60"), 
                           ("Refusé", "#e74c3c"), ("Contre-proposition", "#f39c12")]:
            lbl = QLabel(f"● {txt}")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            legende.addWidget(lbl)
        legende.addStretch()
        layout.addLayout(legende)
        
        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        self.main_layout = QVBoxLayout()
        container.setLayout(self.main_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.charger_detail()
        
        # Bouton fermer
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
    
    def get_status_color(self, statut):
        """Retourne la couleur selon le statut."""
        colors = {
            'en_attente': '#95a5a6',
            'accepte': '#27ae60',
            'refuse': '#e74c3c',
            'contre_proposition': '#f39c12'
        }
        return colors.get(statut, '#95a5a6')
    
    def get_status_emoji(self, statut):
        """Retourne l'emoji selon le statut."""
        emojis = {
            'en_attente': '⏳',
            'accepte': '✅',
            'refuse': '❌',
            'contre_proposition': '💬'
        }
        return emojis.get(statut, '⏳')
    
    def charger_detail(self):
        """Charge le détail du devis."""
        data = self.db.get_options_devis_detail(self.devis_id)
        
        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px; border: 1px solid #636e72;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl_prod = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl_prod.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl_prod)
            
            # Créer un tableau pour afficher les options
            if prod_data['options_standard'] or prod_data['options_perso']:
                table = QTableWidget()
                table.setColumnCount(6)
                table.setHorizontalHeaderLabels(["Option", "Prix demandé", "Réponse Vendeur", "Prix vendeur", "Réponse Acheteur", "Commentaires"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setStyleSheet("""
                    QTableWidget { background-color: #2d3436; color: #dfe6e9; gridline-color: #636e72; }
                    QHeaderView::section { background-color: #636e72; color: #dfe6e9; font-weight: bold; }
                """)
                
                all_opts = []
                for opt in prod_data['options_standard']:
                    all_opts.append(('standard', opt))
                for opt in prod_data['options_perso']:
                    all_opts.append(('perso', opt))
                
                table.setRowCount(len(all_opts))
                
                for row, (type_opt, opt) in enumerate(all_opts):
                    # Nom option
                    if type_opt == 'standard':
                        nom = opt['nom']
                        prix_demande = f"{opt['prix']} €"
                    else:
                        nom = f"🔧 {opt['description']}"
                        prix_demande = f"{opt['prix_demande']} €" if opt['prix_demande'] else "-"
                    
                    table.setItem(row, 0, QTableWidgetItem(nom))
                    table.setItem(row, 1, QTableWidgetItem(prix_demande))
                    
                    # Réponse vendeur
                    statut_v = opt.get('statut_vendeur') or 'en_attente'
                    item_v = QTableWidgetItem(f"{self.get_status_emoji(statut_v)} {statut_v}")
                    item_v.setForeground(QColor(self.get_status_color(statut_v)))
                    table.setItem(row, 2, item_v)
                    
                    # Prix vendeur
                    prix_v = opt.get('prix_propose')
                    table.setItem(row, 3, QTableWidgetItem(f"{prix_v} €" if prix_v else "-"))
                    
                    # Réponse acheteur
                    statut_a = opt.get('statut_acheteur') or 'en_attente'
                    item_a = QTableWidgetItem(f"{self.get_status_emoji(statut_a)} {statut_a}")
                    item_a.setForeground(QColor(self.get_status_color(statut_a)))
                    table.setItem(row, 4, item_a)
                    
                    # Commentaires
                    comm_v = opt.get('commentaire_vendeur') or ""
                    comm_a = opt.get('commentaire_acheteur') or ""
                    comm_txt = ""
                    if comm_v:
                        comm_txt += f"[V] {comm_v} "
                    if comm_a:
                        comm_txt += f"[A] {comm_a}"
                    table.setItem(row, 5, QTableWidgetItem(comm_txt.strip()))
                
                frame_layout.addWidget(table)
            
            self.main_layout.addWidget(frame)
        
        self.main_layout.addStretch()


class ReponseAcheteurDialog(QDialog):
    """Dialog pour que l'acheteur réponde aux propositions du vendeur."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        self.reponses = []
        
        self.setWindowTitle("✅ Réponse Acheteur - Accepter/Refuser les propositions")
        self.setMinimumSize(850, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        lbl = QLabel("✅ Répondre aux propositions du vendeur")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #00b894;")
        layout.addWidget(lbl)
        
        lbl_info = QLabel("Acceptez ou refusez chaque proposition du vendeur.")
        lbl_info.setStyleSheet("color: #b2bec3; font-style: italic;")
        layout.addWidget(lbl_info)
        
        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        self.main_layout = QVBoxLayout()
        container.setLayout(self.main_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.charger_options()
        
        # Boutons
        btns = QHBoxLayout()
        btn_accept_all = QPushButton("✅ Tout accepter")
        btn_accept_all.setStyleSheet("background-color: #27ae60; color: white; padding: 10px;")
        btn_accept_all.clicked.connect(self.tout_accepter)
        btns.addWidget(btn_accept_all)
        
        btn_save = QPushButton("💾 Sauvegarder mes réponses")
        btn_save.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        btn_save.clicked.connect(self.sauvegarder_reponses)
        btns.addWidget(btn_save)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        
        layout.addLayout(btns)
    
    def charger_options(self):
        """Charge les options avec les propositions du vendeur."""
        data = self.db.get_options_devis_detail(self.devis_id)
        
        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px; border: 1px solid #636e72;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl_prod = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl_prod.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl_prod)
            
            # Options standard
            for opt in prod_data['options_standard']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    self.ajouter_ligne_reponse(frame_layout, opt, 'standard')
            
            # Options perso
            for opt in prod_data['options_perso']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    self.ajouter_ligne_reponse(frame_layout, opt, 'perso')
            
            self.main_layout.addWidget(frame)
        
        self.main_layout.addStretch()
    
    def ajouter_ligne_reponse(self, layout, opt, type_opt):
        """Ajoute une ligne pour que l'acheteur réponde."""
        row = QFrame()
        row.setStyleSheet("background-color: #636e72; padding: 8px; margin: 3px; border-radius: 5px;")
        row_layout = QVBoxLayout()
        row.setLayout(row_layout)
        
        # Ligne 1: Info option et réponse vendeur
        info_layout = QHBoxLayout()
        
        if type_opt == 'standard':
            lbl_nom = QLabel(f"📦 {opt['nom']} - Prix catalogue: {opt['prix']} €")
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "À définir"
            lbl_nom = QLabel(f"🔧 {opt['description']} - Demandé: {prix_txt}")
        lbl_nom.setStyleSheet("color: #dfe6e9; font-weight: bold;")
        info_layout.addWidget(lbl_nom)
        row_layout.addLayout(info_layout)
        
        # Ligne 2: Réponse du vendeur
        vendeur_layout = QHBoxLayout()
        statut_v = opt.get('statut_vendeur', 'en_attente')
        prix_v = opt.get('prix_propose')
        comm_v = opt.get('commentaire_vendeur', '')
        
        statut_colors = {
            'accepte': '#27ae60',
            'refuse': '#e74c3c',
            'contre_proposition': '#f39c12',
            'en_attente': '#95a5a6'
        }
        color = statut_colors.get(statut_v, '#95a5a6')
        
        lbl_vendeur = QLabel(f"↳ Réponse vendeur: {statut_v.upper()}")
        lbl_vendeur.setStyleSheet(f"color: {color}; font-weight: bold;")
        vendeur_layout.addWidget(lbl_vendeur)
        
        if prix_v:
            lbl_prix_v = QLabel(f"💰 Prix proposé: {prix_v} €")
            lbl_prix_v.setStyleSheet("color: #f1c40f;")
            vendeur_layout.addWidget(lbl_prix_v)
        
        if comm_v:
            lbl_comm_v = QLabel(f"💬 \"{comm_v}\"")
            lbl_comm_v.setStyleSheet("color: #b2bec3; font-style: italic;")
            vendeur_layout.addWidget(lbl_comm_v)
        
        vendeur_layout.addStretch()
        row_layout.addLayout(vendeur_layout)
        
        # Ligne 3: Réponse acheteur
        reponse_layout = QHBoxLayout()
        reponse_layout.addWidget(QLabel("Ma réponse:"))
        
        combo = QComboBox()
        combo.addItems(["en_attente", "accepte", "refuse"])
        statut_a = opt.get('statut_acheteur', 'en_attente')
        combo.setCurrentText(statut_a)
        combo.setStyleSheet("min-width: 100px;")
        reponse_layout.addWidget(combo)
        
        reponse_layout.addWidget(QLabel("Commentaire:"))
        input_comm = QLineEdit()
        input_comm.setPlaceholderText("Commentaire optionnel...")
        if opt.get('commentaire_acheteur'):
            input_comm.setText(opt['commentaire_acheteur'])
        input_comm.setMinimumWidth(200)
        reponse_layout.addWidget(input_comm)
        
        reponse_layout.addStretch()
        row_layout.addLayout(reponse_layout)
        
        layout.addWidget(row)
        
        self.reponses.append({
            'type': type_opt,
            'id': opt['id'],
            'combo': combo,
            'input_comm': input_comm
        })
    
    def tout_accepter(self):
        """Met toutes les réponses sur Accepter."""
        for rep in self.reponses:
            rep['combo'].setCurrentText('accepte')
    
    def sauvegarder_reponses(self):
        """Sauvegarde les réponses de l'acheteur."""
        for rep in self.reponses:
            statut = rep['combo'].currentText()
            commentaire = rep['input_comm'].text().strip()
            
            if rep['type'] == 'standard':
                self.db.repondre_option_standard_acheteur(rep['id'], statut, commentaire)
            else:
                self.db.repondre_option_perso_acheteur(rep['id'], statut, commentaire)
        
        QMessageBox.information(self, "Succès", "Vos réponses ont été enregistrées !")
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Configurateur de Devis")
        self.setGeometry(100, 100, 1200, 800)
        
        self.db = DatabaseManager()
        self.produit_widgets = []
        self.current_affaire_id = None

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # --- CRÉATION DES ONGLETS ---
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Onglet 1 : Liste des Affaires
        self.tab_affaires = QWidget()
        self.setup_affaires_tab()
        self.tabs.addTab(self.tab_affaires, "📋 Affaires")

        # Onglet 2 : Détail Affaire (avec commentaires)
        self.tab_detail = QWidget()
        self.setup_detail_tab()
        self.tabs.addTab(self.tab_detail, "📝 Détail Affaire")
        
        # Onglet 3 : Nouveau Devis
        self.tab_form = QWidget()
        self.setup_form_tab()
        self.tabs.addTab(self.tab_form, "➕ Nouveau Devis")

        # Onglet 4 : Historique (ancien)
        self.tab_history = QWidget()
        self.setup_history_tab()
        self.tabs.addTab(self.tab_history, "📜 Historique")
        
        # Connexion : Quand on change d'onglet
        self.tabs.currentChanged.connect(self.on_tab_change)

        # Chargement initial
        self.charger_affaires()

    # ============ ONGLET AFFAIRES ============
    def setup_affaires_tab(self):
        """Liste des affaires avec numérotation."""
        layout = QVBoxLayout()
        self.tab_affaires.setLayout(layout)
        
        # Header
        header = QHBoxLayout()
        lbl = QLabel("📋 Gestion des Affaires")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #dfe6e9;")
        header.addWidget(lbl)
        header.addStretch()
        
        btn_nouvelle = QPushButton("➕ Nouvelle Affaire")
        btn_nouvelle.setStyleSheet("background-color: #3498db; color: white; padding: 10px 20px;")
        btn_nouvelle.clicked.connect(self.nouvelle_affaire)
        header.addWidget(btn_nouvelle)
        
        layout.addLayout(header)
        
        # Table des affaires
        self.table_affaires = QTableWidget()
        self.table_affaires.setColumnCount(6)
        self.table_affaires.setHorizontalHeaderLabels(["N° Affaire", "Client", "Titre", "Statut", "Devis", "Date"])
        self.table_affaires.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_affaires.setAlternatingRowColors(True)
        self.table_affaires.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_affaires.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_affaires.doubleClicked.connect(self.ouvrir_affaire)
        layout.addWidget(self.table_affaires)
        
        # Boutons actions
        actions = QHBoxLayout()
        btn_ouvrir = QPushButton("📂 Ouvrir")
        btn_ouvrir.clicked.connect(self.ouvrir_affaire_selectionnee)
        actions.addWidget(btn_ouvrir)
        
        btn_refresh = QPushButton("🔄 Rafraîchir")
        btn_refresh.clicked.connect(self.charger_affaires)
        actions.addWidget(btn_refresh)
        actions.addStretch()
        
        layout.addLayout(actions)

    def charger_affaires(self):
        """Charge la liste des affaires."""
        data = self.db.get_liste_affaires()
        self.table_affaires.setRowCount(0)
        
        for row_idx, row_data in enumerate(data):
            self.table_affaires.insertRow(row_idx)
            # id, numero_affaire, client, titre, statut, date_creation, date_modif, nb_devis
            self.table_affaires.setItem(row_idx, 0, QTableWidgetItem(str(row_data[1])))  # N° Affaire
            self.table_affaires.setItem(row_idx, 1, QTableWidgetItem(row_data[2] or ""))  # Client
            self.table_affaires.setItem(row_idx, 2, QTableWidgetItem(row_data[3]))  # Titre
            
            # Statut avec couleur
            statut_item = QTableWidgetItem(row_data[4])
            if row_data[4] == 'en_cours':
                statut_item.setBackground(QColor("#fff3cd"))
            elif row_data[4] == 'gagne':
                statut_item.setBackground(QColor("#d4edda"))
            elif row_data[4] == 'perdu':
                statut_item.setBackground(QColor("#f8d7da"))
            self.table_affaires.setItem(row_idx, 3, statut_item)
            
            self.table_affaires.setItem(row_idx, 4, QTableWidgetItem(str(row_data[7])))  # Nb devis
            self.table_affaires.setItem(row_idx, 5, QTableWidgetItem(str(row_data[5])[:10]))  # Date
            
            # Stocker l'ID dans la première colonne
            self.table_affaires.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, row_data[0])

    def nouvelle_affaire(self):
        """Crée une nouvelle affaire."""
        dialog = NouvelleAffaireDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            if not data['client'] or not data['titre']:
                QMessageBox.warning(self, "Attention", "Client et Titre sont obligatoires.")
                return
            
            # Créer le client
            client_id = self.db.creer_ou_obtenir_client(
                data['client'], data['contact'], data['email']
            )
            
            # Créer l'affaire
            affaire_id, numero = self.db.creer_affaire(
                client_id, data['titre'], data['description']
            )
            
            if affaire_id:
                QMessageBox.information(self, "Succès", f"Affaire N°{numero} créée !")
                self.charger_affaires()
                self.current_affaire_id = affaire_id
                self.tabs.setCurrentIndex(1)  # Aller au détail
                self.charger_detail_affaire()

    def ouvrir_affaire(self):
        """Ouvre l'affaire sélectionnée via double-clic."""
        self.ouvrir_affaire_selectionnee()

    def ouvrir_affaire_selectionnee(self):
        """Ouvre l'affaire sélectionnée."""
        selected = self.table_affaires.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez une affaire.")
            return
        
        row = selected[0].row()
        affaire_id = self.table_affaires.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.current_affaire_id = affaire_id
        self.tabs.setCurrentIndex(1)
        self.charger_detail_affaire()

    # ============ ONGLET DETAIL AFFAIRE ============
    def setup_detail_tab(self):
        """Détail d'une affaire avec zone de commentaires."""
        layout = QHBoxLayout()
        self.tab_detail.setLayout(layout)
        
        # Splitter pour séparer contenu et commentaires
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # === Partie gauche : Infos et Devis ===
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Header affaire
        self.lbl_affaire_header = QLabel("Sélectionnez une affaire")
        self.lbl_affaire_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #74b9ff;")
        left_layout.addWidget(self.lbl_affaire_header)
        
        # Infos client
        self.lbl_client_info = QLabel("")
        self.lbl_client_info.setStyleSheet("color: #b2bec3;")
        left_layout.addWidget(self.lbl_client_info)
        
        # Statut
        statut_layout = QHBoxLayout()
        statut_layout.addWidget(QLabel("Statut:"))
        self.combo_statut = QComboBox()
        self.combo_statut.addItems(["en_cours", "gagne", "perdu", "suspendu"])
        self.combo_statut.currentTextChanged.connect(self.changer_statut_affaire)
        statut_layout.addWidget(self.combo_statut)
        statut_layout.addStretch()
        left_layout.addLayout(statut_layout)
        
        # Liste des devis
        left_layout.addWidget(QLabel("📑 Devis de cette affaire:"))
        self.table_devis_affaire = QTableWidget()
        self.table_devis_affaire.setColumnCount(5)
        self.table_devis_affaire.setHorizontalHeaderLabels(["Version", "Date", "Total", "Statut", "Notes"])
        self.table_devis_affaire.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devis_affaire.setMaximumHeight(200)
        self.table_devis_affaire.doubleClicked.connect(self.voir_detail_devis)
        left_layout.addWidget(self.table_devis_affaire)
        
        # Boutons
        btns_layout = QHBoxLayout()
        btn_nouveau_devis = QPushButton("➕ Nouveau Devis")
        btn_nouveau_devis.setStyleSheet("background-color: #27ae60; color: white;")
        btn_nouveau_devis.clicked.connect(self.aller_nouveau_devis)
        btns_layout.addWidget(btn_nouveau_devis)
        
        btn_voir_detail = QPushButton("👁️ Voir Détail")
        btn_voir_detail.setStyleSheet("background-color: #3498db; color: white;")
        btn_voir_detail.clicked.connect(self.voir_detail_devis)
        btns_layout.addWidget(btn_voir_detail)
        
        btn_repondre = QPushButton("✍️ Répondre (Vendeur)")
        btn_repondre.setStyleSheet("background-color: #e67e22; color: white;")
        btn_repondre.clicked.connect(self.ouvrir_reponse_vendeur)
        btns_layout.addWidget(btn_repondre)
        
        btn_repondre_acheteur = QPushButton("✅ Répondre (Acheteur)")
        btn_repondre_acheteur.setStyleSheet("background-color: #9b59b6; color: white;")
        btn_repondre_acheteur.clicked.connect(self.ouvrir_reponse_acheteur)
        btns_layout.addWidget(btn_repondre_acheteur)
        
        btns_layout.addStretch()
        left_layout.addLayout(btns_layout)
        
        # Bouton PDF sur une nouvelle ligne
        btns_layout2 = QHBoxLayout()
        btn_generer_pdf = QPushButton("📄 Générer PDF")
        btn_generer_pdf.clicked.connect(self.generer_pdf_affaire)
        btns_layout2.addWidget(btn_generer_pdf)
        btns_layout2.addStretch()
        left_layout.addLayout(btns_layout2)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # === Partie droite : Commentaires ===
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        lbl_comm = QLabel("💬 Échanges Acheteur / Vendeur")
        lbl_comm.setStyleSheet("font-size: 14px; font-weight: bold; color: #dfe6e9;")
        right_layout.addWidget(lbl_comm)
        
        # Zone de scroll pour les commentaires
        self.scroll_commentaires = QScrollArea()
        self.scroll_commentaires.setWidgetResizable(True)
        self.scroll_commentaires.setStyleSheet("background-color: #2d3436;")
        
        self.widget_commentaires = QWidget()
        self.layout_commentaires = QVBoxLayout()
        self.layout_commentaires.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.widget_commentaires.setLayout(self.layout_commentaires)
        self.scroll_commentaires.setWidget(self.widget_commentaires)
        right_layout.addWidget(self.scroll_commentaires)
        
        # Zone d'ajout de commentaire
        add_comm_layout = QVBoxLayout()
        
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("En tant que:"))
        self.combo_role = QComboBox()
        self.combo_role.addItems(["vendeur", "acheteur"])
        role_layout.addWidget(self.combo_role)
        
        self.input_auteur = QLineEdit()
        self.input_auteur.setPlaceholderText("Votre nom")
        role_layout.addWidget(self.input_auteur)
        add_comm_layout.addLayout(role_layout)
        
        self.input_commentaire = QTextEdit()
        self.input_commentaire.setPlaceholderText("Écrivez votre commentaire...")
        self.input_commentaire.setMaximumHeight(80)
        add_comm_layout.addWidget(self.input_commentaire)
        
        btn_envoyer = QPushButton("📤 Envoyer")
        btn_envoyer.setStyleSheet("background-color: #3498db; color: white;")
        btn_envoyer.clicked.connect(self.envoyer_commentaire)
        add_comm_layout.addWidget(btn_envoyer)
        
        right_layout.addLayout(add_comm_layout)
        splitter.addWidget(right_widget)
        
        # Proportions du splitter
        splitter.setSizes([600, 400])

    def charger_detail_affaire(self):
        """Charge les détails de l'affaire courante."""
        if not self.current_affaire_id:
            return
        
        details = self.db.get_affaire_details(self.current_affaire_id)
        if not details:
            return
        
        # id, numero, client, contact, email, titre, description, statut, date
        self.lbl_affaire_header.setText(f"📋 Affaire N°{details[1]} - {details[5]}")
        
        client_info = f"Client: {details[2] or 'N/A'}"
        if details[3]:
            client_info += f" | Contact: {details[3]}"
        if details[4]:
            client_info += f" | {details[4]}"
        self.lbl_client_info.setText(client_info)
        
        # Statut
        index = self.combo_statut.findText(details[7])
        if index >= 0:
            self.combo_statut.blockSignals(True)
            self.combo_statut.setCurrentIndex(index)
            self.combo_statut.blockSignals(False)
        
        # Charger les devis
        self.charger_devis_affaire()
        
        # Charger les commentaires
        self.charger_commentaires()

    def charger_devis_affaire(self):
        """Charge les devis de l'affaire courante."""
        if not self.current_affaire_id:
            return
        
        devis = self.db.get_devis_affaire(self.current_affaire_id)
        self.table_devis_affaire.setRowCount(0)
        
        for row_idx, d in enumerate(devis):
            self.table_devis_affaire.insertRow(row_idx)
            # id, version, date, total, statut, notes
            self.table_devis_affaire.setItem(row_idx, 0, QTableWidgetItem(f"V{d[1]}"))
            self.table_devis_affaire.setItem(row_idx, 1, QTableWidgetItem(str(d[2])[:10]))
            self.table_devis_affaire.setItem(row_idx, 2, QTableWidgetItem(f"{d[3]:.2f} €"))
            self.table_devis_affaire.setItem(row_idx, 3, QTableWidgetItem(d[4]))
            self.table_devis_affaire.setItem(row_idx, 4, QTableWidgetItem(d[5] or ""))
            
            # Stocker l'ID
            self.table_devis_affaire.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, d[0])

    def charger_commentaires(self):
        """Charge et affiche les commentaires."""
        # Nettoyer
        while self.layout_commentaires.count():
            child = self.layout_commentaires.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.current_affaire_id:
            return
        
        commentaires = self.db.get_commentaires_affaire(self.current_affaire_id)
        
        for c in commentaires:
            # id, auteur, role, contenu, date
            widget = CommentaireWidget(c[1], c[2], c[3], c[4])
            self.layout_commentaires.addWidget(widget)
        
        # Scroller en bas
        self.scroll_commentaires.verticalScrollBar().setValue(
            self.scroll_commentaires.verticalScrollBar().maximum()
        )

    def envoyer_commentaire(self):
        """Envoie un nouveau commentaire."""
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Attention", "Aucune affaire sélectionnée.")
            return
        
        auteur = self.input_auteur.text().strip()
        contenu = self.input_commentaire.toPlainText().strip()
        role = self.combo_role.currentText()
        
        if not auteur or not contenu:
            QMessageBox.warning(self, "Attention", "Nom et commentaire requis.")
            return
        
        self.db.ajouter_commentaire(self.current_affaire_id, auteur, role, contenu)
        self.input_commentaire.clear()
        self.charger_commentaires()

    def changer_statut_affaire(self, nouveau_statut):
        """Change le statut de l'affaire."""
        if self.current_affaire_id:
            self.db.mettre_a_jour_statut_affaire(self.current_affaire_id, nouveau_statut)

    def aller_nouveau_devis(self):
        """Passe à l'onglet de création de devis."""
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord une affaire.")
            return
        self.tabs.setCurrentIndex(2)

    def ouvrir_reponse_vendeur(self):
        """Ouvre le dialog pour que le vendeur réponde aux options."""
        selected = self.table_devis_affaire.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis dans la liste.")
            return
        
        row = selected[0].row()
        devis_id = self.table_devis_affaire.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = ReponseVendeurDialog(self.db, devis_id, self)
        dialog.exec()

    def voir_detail_devis(self):
        """Ouvre le dialog pour voir le détail d'un devis avec toutes les réponses."""
        selected = self.table_devis_affaire.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis dans la liste.")
            return
        
        row = selected[0].row()
        devis_id = self.table_devis_affaire.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = DetailDevisDialog(self.db, devis_id, self)
        dialog.exec()

    def ouvrir_reponse_acheteur(self):
        """Ouvre le dialog pour que l'acheteur réponde aux propositions du vendeur."""
        selected = self.table_devis_affaire.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis dans la liste.")
            return
        
        row = selected[0].row()
        devis_id = self.table_devis_affaire.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        dialog = ReponseAcheteurDialog(self.db, devis_id, self)
        if dialog.exec():
            # Recharger les données si des modifications ont été faites
            self.charger_devis_affaire()

    # ============ ONGLET NOUVEAU DEVIS (multi-produits) ============
    def setup_form_tab(self):
        """Formulaire de création de devis avec multi-produits."""
        layout = QVBoxLayout()
        self.tab_form.setLayout(layout)
        
        # Header
        self.lbl_devis_header = QLabel("➕ Nouveau Devis")
        self.lbl_devis_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #74b9ff;")
        layout.addWidget(self.lbl_devis_header)
        
        self.lbl_affaire_ref = QLabel("Affaire: Aucune sélectionnée")
        self.lbl_affaire_ref.setStyleSheet("color: #b2bec3;")
        layout.addWidget(self.lbl_affaire_ref)
        
        # Zone scrollable pour les produits
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.container_produits = QWidget()
        self.layout_produits = QVBoxLayout()
        self.container_produits.setLayout(self.layout_produits)
        scroll.setWidget(self.container_produits)
        layout.addWidget(scroll)
        
        # Bouton ajouter produit
        btn_add_prod = QPushButton("➕ Ajouter un Produit")
        btn_add_prod.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px;")
        btn_add_prod.clicked.connect(self.ajouter_produit)
        layout.addWidget(btn_add_prod)
        
        # Notes
        layout.addWidget(QLabel("Notes:"))
        self.input_notes = QTextEdit()
        self.input_notes.setMaximumHeight(60)
        self.input_notes.setPlaceholderText("Notes internes pour ce devis...")
        layout.addWidget(self.input_notes)
        
        # Total
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("TOTAL ESTIMÉ:"))
        self.lbl_total = QLabel("0.00 €")
        self.lbl_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
        total_layout.addWidget(self.lbl_total)
        layout.addLayout(total_layout)
        
        # Bouton valider
        self.btn_valider = QPushButton("💾 Valider et Créer le Devis")
        self.btn_valider.setStyleSheet("background-color: #27ae60; color: white; padding: 15px; font-size: 16px;")
        self.btn_valider.clicked.connect(self.creer_devis)
        layout.addWidget(self.btn_valider)
        
        # Ajouter un premier produit par défaut
        self.ajouter_produit()

    def ajouter_produit(self):
        """Ajoute un widget produit au formulaire."""
        widget = ProduitConfigWidget(
            self.db, 
            len(self.produit_widgets),
            self.calculer_total,
            self.supprimer_produit
        )
        self.produit_widgets.append(widget)
        self.layout_produits.addWidget(widget)
        self.calculer_total()

    def supprimer_produit(self, widget):
        """Supprime un produit du formulaire."""
        if len(self.produit_widgets) <= 1:
            QMessageBox.warning(self, "Attention", "Il faut au moins un produit.")
            return
        
        self.produit_widgets.remove(widget)
        self.layout_produits.removeWidget(widget)
        widget.deleteLater()
        
        # Renuméroter
        for i, w in enumerate(self.produit_widgets):
            w.index = i
            w.lbl_title.setText(f"🔷 Produit #{i + 1}")
        
        self.calculer_total()

    def calculer_total(self):
        """Calcule le total de tous les produits."""
        total = sum(w.calculer_subtotal() for w in self.produit_widgets)
        self.lbl_total.setText(f"{total:,.2f} €".replace(",", " "))
        return total

    def creer_devis(self):
        """Crée le devis avec tous les produits."""
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord sélectionner une affaire dans l'onglet 'Affaires'.")
            return
        
        # Collecter les données des produits
        produits_data = []
        for widget in self.produit_widgets:
            data = widget.get_data()
            if data:
                produits_data.append(data)
        
        if not produits_data:
            QMessageBox.warning(self, "Attention", "Ajoutez au moins un produit.")
            return
        
        notes = self.input_notes.toPlainText().strip()
        
        devis_id, version = self.db.creer_devis_pour_affaire(
            self.current_affaire_id, produits_data, notes
        )
        
        if devis_id:
            # Récupérer les infos pour le message
            details = self.db.get_affaire_details(self.current_affaire_id)
            total = self.calculer_total()
            
            QMessageBox.information(
                self, "Succès", 
                f"Devis V{version} créé pour l'affaire N°{details[1]} !\n"
                f"Total: {total:,.2f} €"
            )
            
            # Générer PDF automatiquement
            self.generer_pdf_devis(devis_id)
            
            # Rafraîchir
            self.charger_detail_affaire()
            self.tabs.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "Erreur", "Échec de la création du devis.")

    def generer_pdf_devis(self, devis_id):
        """Génère un PDF pour un devis spécifique."""
        # Récupérer les infos
        details = self.db.get_affaire_details(self.current_affaire_id)
        produits = self.db.get_produits_devis(devis_id)
        devis_info = None
        for d in self.db.get_devis_affaire(self.current_affaire_id):
            if d[0] == devis_id:
                devis_info = d
                break
        
        if not details or not devis_info:
            return
        
        # Création PDF
        pdf = FPDF()
        pdf.add_page()
        
        # Logo
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "logo.png")
        if os.path.exists(logo_path):
            pdf.image(logo_path, 10, 8, 33)
            pdf.ln(20)
        
        # En-tête
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "DEVIS", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Affaire N : {details[1]}", ln=True)
        pdf.cell(0, 8, f"Devis Version : V{devis_info[1]}", ln=True)
        pdf.cell(0, 8, f"Date : {datetime.datetime.now().strftime('%d/%m/%Y')}", ln=True)
        pdf.cell(0, 8, f"Client : {details[2]}", ln=True)
        if details[3]:
            pdf.cell(0, 8, f"Contact : {details[3]}", ln=True)
        pdf.ln(10)
        
        # Tableau
        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 8, "Description", border=1)
        pdf.cell(30, 8, "Qte", border=1, align="C")
        pdf.cell(40, 8, "Prix Unit.", border=1, align="R")
        pdf.cell(40, 8, "Total", border=1, ln=True, align="R")
        
        pdf.set_font("Arial", "", 10)
        grand_total = 0
        
        for pd_id, nom, qte, prix_unit, options in produits:
            # Ligne produit
            subtotal_prod = prix_unit * qte
            pdf.cell(80, 8, f"Produit {nom}", border=1)
            pdf.cell(30, 8, str(qte), border=1, align="C")
            pdf.cell(40, 8, f"{prix_unit:.2f} E", border=1, align="R")
            pdf.cell(40, 8, f"{subtotal_prod:.2f} E", border=1, ln=True, align="R")
            grand_total += subtotal_prod
            
            # Options
            for opt_nom, opt_prix in options:
                subtotal_opt = opt_prix * qte
                pdf.cell(80, 8, f"  + {opt_nom}", border=1)
                pdf.cell(30, 8, str(qte), border=1, align="C")
                pdf.cell(40, 8, f"{opt_prix:.2f} E", border=1, align="R")
                pdf.cell(40, 8, f"{subtotal_opt:.2f} E", border=1, ln=True, align="R")
                grand_total += subtotal_opt
        
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(150, 10, "TOTAL HT", align="R")
        pdf.cell(40, 10, f"{grand_total:.2f} E", border=1, align="R")
        
        # Sauvegarde
        output_dir = os.path.join(base_dir, "generated_devis")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"Affaire_{details[1]}_V{devis_info[1]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        full_path = os.path.join(output_dir, filename)
        
        try:
            pdf.output(full_path)
            print(f"✅ PDF généré : {full_path}")
        except Exception as e:
            print(f"❌ Erreur PDF : {e}")

    def generer_pdf_affaire(self):
        """Génère le PDF du dernier devis de l'affaire."""
        selected = self.table_devis_affaire.selectedItems()
        if selected:
            row = selected[0].row()
            devis_id = self.table_devis_affaire.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.generer_pdf_devis(devis_id)
            QMessageBox.information(self, "Succès", "PDF généré dans le dossier generated_devis/")
        else:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis dans la liste.")

    # ============ ONGLET HISTORIQUE (ancien) ============
    def setup_history_tab(self):
        """Construit l'interface du tableau d'historique."""
        layout = QVBoxLayout()
        self.tab_history.setLayout(layout)
        
        lbl = QLabel("📜 Historique des devis générés")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl)
        
        # Configuration du tableau
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels(["ID", "Date", "Client", "Référence", "Total (€)"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table_history)
        
        btn_refresh = QPushButton("Rafraîchir la liste")
        btn_refresh.clicked.connect(self.charger_historique)
        layout.addWidget(btn_refresh)

    def on_tab_change(self, index):
        """Appelé quand on clique sur un onglet."""
        if index == 0:
            self.charger_affaires()
        elif index == 1:
            self.charger_detail_affaire()
        elif index == 2:
            # Mettre à jour le header du devis avec l'affaire courante
            if self.current_affaire_id:
                details = self.db.get_affaire_details(self.current_affaire_id)
                if details:
                    self.lbl_affaire_ref.setText(f"Affaire: N°{details[1]} - {details[5]}")
            else:
                self.lbl_affaire_ref.setText("Affaire: Aucune sélectionnée (créez-en une d'abord)")
        elif index == 3:
            self.charger_historique()

    def charger_historique(self):
        """Récupère les données BDD et remplit le tableau (ancien système)."""
        data = self.db.get_historique_devis()
        
        self.table_history.setRowCount(0)
        
        for row_idx, row_data in enumerate(data):
            self.table_history.insertRow(row_idx)
            self.table_history.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            self.table_history.setItem(row_idx, 1, QTableWidgetItem(str(row_data[1])[:16]))
            self.table_history.setItem(row_idx, 2, QTableWidgetItem(row_data[2]))
            self.table_history.setItem(row_idx, 3, QTableWidgetItem(row_data[3]))
            prix_fmt = f"{row_data[4]:.2f} €"
            self.table_history.setItem(row_idx, 4, QTableWidgetItem(prix_fmt))


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Initialisation BDD
    db = DatabaseManager()
    db.create_tables()
    db.add_demo_data()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
