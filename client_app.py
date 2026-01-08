"""
Application CLIENT - Configurateur de Devis
Interface dédiée à l'acheteur pour créer et suivre ses demandes de devis.
"""
import sys
import os

# Ajouter le chemin racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QFrame, QScrollArea, QTextEdit, QComboBox, QSpinBox,
                             QLineEdit, QGroupBox, QCheckBox, QMessageBox, QDialog, QFormLayout,
                             QDialogButtonBox, QSplitter, QProgressBar, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont
import datetime
from src.models.db_manager import DatabaseManager
from src.utils.pdf_generator import generer_devis_pdf


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
            QComboBox { color: #dfe6e9; background-color: #636e72; }
            QSpinBox { color: #dfe6e9; background-color: #636e72; }
            QDoubleSpinBox { color: #dfe6e9; background-color: #636e72; }
            QCheckBox { color: #dfe6e9; }
            QGroupBox { color: #74b9ff; font-weight: bold; }
            QLineEdit { color: #dfe6e9; background-color: #636e72; }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
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
        self.combo_modele.currentIndexChanged.connect(self.on_modele_change)
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
        
        # Barre de poids
        poids_layout = QVBoxLayout()
        poids_header = QHBoxLayout()
        self.lbl_poids = QLabel("⚖️ Charge: 0 / 0 kg (0%)")
        self.lbl_poids.setStyleSheet("font-weight: bold;")
        poids_header.addWidget(self.lbl_poids)
        poids_header.addStretch()
        self.lbl_poids_warning = QLabel("")
        poids_header.addWidget(self.lbl_poids_warning)
        poids_layout.addLayout(poids_header)
        
        self.progress_poids = QProgressBar()
        self.progress_poids.setMaximum(100)
        self.progress_poids.setValue(0)
        self.progress_poids.setStyleSheet("""
            QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #27ae60; border-radius: 5px; }
        """)
        poids_layout.addWidget(self.progress_poids)
        layout.addLayout(poids_layout)
        
        # Options standard
        self.group_options = QGroupBox("Options catalogue")
        self.layout_options = QVBoxLayout()
        self.group_options.setLayout(self.layout_options)
        layout.addWidget(self.group_options)
        
        # Options personnalisées
        self.group_options_perso = QGroupBox("🔧 Options personnalisées (demandes spéciales)")
        self.layout_options_perso = QVBoxLayout()
        self.group_options_perso.setLayout(self.layout_options_perso)
        
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
    
    def on_modele_change(self):
        """Appelé quand le modèle change, recharge les options disponibles."""
        prod_data = self.combo_modele.currentData()
        if prod_data:
            self.charger_options_pour_produit(prod_data[0])
        self.update_options_disponibles()
        self.on_change()
    
    def update_options_disponibles(self):
        """Active/désactive les options en fonction du poids disponible."""
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return
        
        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite_85 = charge_max * 0.85
        poids_actuel = self.calculer_poids_total()
        
        # Activer/désactiver les options selon le poids restant
        for cb in self.checkboxes:
            opt = cb.property("option_data")
            opt_poids = opt[3] if len(opt) > 3 and opt[3] else 0
            
            if not cb.isChecked():
                # Si l'option n'est pas cochée, vérifier si on peut l'ajouter
                if poids_actuel + opt_poids > limite_85:
                    cb.setEnabled(False)
                    cb.setStyleSheet("color: #e74c3c;")
                else:
                    cb.setEnabled(True)
                    cb.setStyleSheet("color: #dfe6e9;")
            else:
                cb.setEnabled(True)
                cb.setStyleSheet("color: #dfe6e9;")
    
    def ajouter_option_perso(self):
        """Ajoute un champ pour une option personnalisée (poids défini par le vendeur)."""
        frame = QFrame()
        frame.setStyleSheet("background-color: #636e72; padding: 5px; border-radius: 3px;")
        row = QHBoxLayout()
        frame.setLayout(row)
        
        input_desc = QLineEdit()
        input_desc.setPlaceholderText("Description de l'option souhaitée...")
        input_desc.setMinimumWidth(250)
        row.addWidget(input_desc)
        
        row.addWidget(QLabel("Prix souhaité:"))
        spin_prix = QSpinBox()
        spin_prix.setMaximum(999999)
        spin_prix.setSuffix(" €")
        spin_prix.valueChanged.connect(self.on_change)
        row.addWidget(spin_prix)
        
        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(30, 30)
        btn_del.clicked.connect(lambda: self.supprimer_option_perso(frame))
        row.addWidget(btn_del)
        
        self.layout_options_perso.insertWidget(self.layout_options_perso.count() - 1, frame)
        self.options_perso_widgets.append((frame, input_desc, spin_prix))
        self.on_change()
    
    def supprimer_option_perso(self, frame):
        """Supprime une option personnalisée."""
        for i, item in enumerate(self.options_perso_widgets):
            if item[0] == frame:
                self.options_perso_widgets.pop(i)
                break
        frame.deleteLater()
        self.on_change()
        self.on_change()
    
    def charger_modeles(self):
        self.combo_modele.clear()
        produits = self.db.get_produits()
        for p in produits:
            charge_max = p[3] if len(p) > 3 and p[3] else 0
            self.combo_modele.addItem(f"{p[1]} - {p[2]}€ (charge max: {charge_max}kg)", p)
        # Charger les options pour le premier produit
        if produits:
            self.charger_options_pour_produit(produits[0][0])
    
    def charger_options_pour_produit(self, produit_id):
        """Charge les options disponibles pour un produit spécifique."""
        for cb in self.checkboxes:
            cb.deleteLater()
        self.checkboxes.clear()
        
        options = self.db.get_options_pour_produit(produit_id)
        for opt in options:
            # opt = (id, nom, prix, poids, universelle)
            poids = opt[3] if len(opt) > 3 and opt[3] else 0
            universelle = opt[4] if len(opt) > 4 else 0
            poids_txt = f" | {poids}kg" if poids > 0 else ""
            prefix = "⭐ " if universelle else ""
            cb = QCheckBox(f"{prefix}{opt[1]} (+{opt[2]}€{poids_txt})")
            cb.setProperty("option_data", opt)
            cb.stateChanged.connect(self.on_option_change)
            self.layout_options.addWidget(cb)
            self.checkboxes.append(cb)
    
    def charger_options(self):
        """Méthode legacy - charge les options pour le produit courant."""
        prod_data = self.combo_modele.currentData()
        if prod_data:
            self.charger_options_pour_produit(prod_data[0])
    
    def on_option_change(self):
        """Appelé quand une option est cochée/décochée."""
        self.update_options_disponibles()
        self.on_change()
    
    def get_data(self):
        """Retourne les données de configuration."""
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return None
        
        options_ids = []
        for cb in self.checkboxes:
            if cb.isChecked():
                opt = cb.property("option_data")
                options_ids.append(opt[0])
        
        options_perso = []
        for item in self.options_perso_widgets:
            frame, input_desc, spin_prix = item
            desc = input_desc.text().strip()
            if desc:
                options_perso.append({
                    'description': desc,
                    'prix': spin_prix.value() if spin_prix.value() > 0 else None
                })
        
        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        
        return {
            'produit_id': prod_data[0],
            'nom': prod_data[1],
            'prix': prod_data[2],
            'charge_max': charge_max,
            'quantite': self.spin_quantite.value(),
            'options_ids': options_ids,
            'options_perso': options_perso
        }
    
    def calculer_poids_total(self):
        """Calcule le poids total des options standard sélectionnées.
        Note: Les options personnalisées n'ont pas de poids tant que le vendeur ne l'a pas défini.
        """
        poids = 0
        
        # Options standard uniquement
        for cb in self.checkboxes:
            if cb.isChecked():
                opt = cb.property("option_data")
                opt_poids = opt[3] if len(opt) > 3 and opt[3] else 0
                poids += opt_poids
        
        return poids
    
    def calculer_sous_total(self):
        data = self.get_data()
        if not data:
            return 0
        
        total = data['prix'] * data['quantite']
        for cb in self.checkboxes:
            if cb.isChecked():
                opt = cb.property("option_data")
                total += opt[2] * data['quantite']
        
        for item in self.options_perso_widgets:
            spin_prix = item[2]
            if spin_prix.value() > 0:
                total += spin_prix.value() * data['quantite']
        
        self.lbl_subtotal.setText(f"Sous-total: {total:.2f} €")
        
        # Mettre à jour la barre de poids
        self.update_poids_display()
        
        return total
    
    def update_poids_display(self):
        """Met à jour l'affichage du poids."""
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return
        
        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite_85 = charge_max * 0.85
        poids_actuel = self.calculer_poids_total()
        
        pourcentage = (poids_actuel / charge_max * 100) if charge_max > 0 else 0
        
        self.lbl_poids.setText(f"⚖️ Charge: {poids_actuel:.1f} / {limite_85:.1f} kg ({pourcentage:.0f}%)")
        self.progress_poids.setValue(min(int(pourcentage), 100))
        
        # Couleurs selon le niveau
        if pourcentage > 85:
            self.progress_poids.setStyleSheet("""
                QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #e74c3c; border-radius: 5px; }
            """)
            self.lbl_poids_warning.setText("⚠️ LIMITE DÉPASSÉE!")
            self.lbl_poids_warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif pourcentage > 70:
            self.progress_poids.setStyleSheet("""
                QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #f39c12; border-radius: 5px; }
            """)
            self.lbl_poids_warning.setText("⚠️ Attention")
            self.lbl_poids_warning.setStyleSheet("color: #f39c12;")
        else:
            self.progress_poids.setStyleSheet("""
                QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #27ae60; border-radius: 5px; }
            """)
            self.lbl_poids_warning.setText("")
    
    def is_poids_valide(self):
        """Vérifie si le poids est dans les limites (85% max)."""
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return True
        
        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite_85 = charge_max * 0.85
        poids_actuel = self.calculer_poids_total()
        
        return poids_actuel <= limite_85


class NouvelleAffaireDialog(QDialog):
    """Dialog pour créer une nouvelle affaire."""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_client_id = None
        self.setWindowTitle("📁 Nouvelle Affaire")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Section client existant ou nouveau
        group_client = QGroupBox("👤 Client")
        client_layout = QVBoxLayout()
        group_client.setLayout(client_layout)
        
        # Menu déroulant clients existants
        client_select_layout = QHBoxLayout()
        client_select_layout.addWidget(QLabel("Client existant:"))
        self.combo_clients = QComboBox()
        self.combo_clients.addItem("-- Nouveau client --", None)
        self.charger_clients()
        self.combo_clients.currentIndexChanged.connect(self.on_client_change)
        client_select_layout.addWidget(self.combo_clients, 1)
        client_layout.addLayout(client_select_layout)
        
        # Formulaire nouveau client
        self.frame_nouveau_client = QFrame()
        form_layout = QFormLayout()
        self.frame_nouveau_client.setLayout(form_layout)
        
        self.input_societe = QLineEdit()
        self.input_societe.setPlaceholderText("Nom de votre société")
        form_layout.addRow("Société:", self.input_societe)
        
        self.input_contact = QLineEdit()
        self.input_contact.setPlaceholderText("Votre nom")
        form_layout.addRow("Contact:", self.input_contact)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.input_email)
        
        self.input_tel = QLineEdit()
        self.input_tel.setPlaceholderText("+33 1 23 45 67 89")
        form_layout.addRow("Téléphone:", self.input_tel)
        
        client_layout.addWidget(self.frame_nouveau_client)
        layout.addWidget(group_client)
        
        # Section projet
        group_projet = QGroupBox("📋 Projet")
        projet_layout = QFormLayout()
        group_projet.setLayout(projet_layout)
        
        self.input_titre = QLineEdit()
        self.input_titre.setPlaceholderText("Titre du projet")
        projet_layout.addRow("Projet:", self.input_titre)
        
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Description du besoin...")
        self.input_description.setMaximumHeight(100)
        projet_layout.addRow("Description:", self.input_description)
        
        layout.addWidget(group_projet)
        
        # Boutons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def charger_clients(self):
        """Charge la liste des clients existants."""
        clients = self.db.get_tous_clients()
        for client in clients:
            # client = (id, nom_societe, contact_nom, contact_email, contact_tel)
            display = f"{client[1]}"
            if client[2]:
                display += f" ({client[2]})"
            self.combo_clients.addItem(display, client)
    
    def on_client_change(self, index):
        """Appelé quand on change de client dans le menu déroulant."""
        client_data = self.combo_clients.currentData()
        
        if client_data is None:
            # Nouveau client - afficher le formulaire vide
            self.frame_nouveau_client.setEnabled(True)
            self.input_societe.clear()
            self.input_contact.clear()
            self.input_email.clear()
            self.input_tel.clear()
            self.selected_client_id = None
        else:
            # Client existant - pré-remplir et désactiver
            self.frame_nouveau_client.setEnabled(False)
            self.input_societe.setText(client_data[1] or "")
            self.input_contact.setText(client_data[2] or "")
            self.input_email.setText(client_data[3] or "")
            self.input_tel.setText(client_data[4] or "")
            self.selected_client_id = client_data[0]
    
    def get_data(self):
        return {
            'client_id': self.selected_client_id,
            'societe': self.input_societe.text().strip(),
            'contact': self.input_contact.text().strip(),
            'email': self.input_email.text().strip(),
            'tel': self.input_tel.text().strip(),
            'titre': self.input_titre.text().strip(),
            'description': self.input_description.toPlainText().strip()
        }


class ReponseAcheteurDialog(QDialog):
    """Dialog pour que l'acheteur réponde aux propositions du vendeur."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        self.reponses = []  # Options avec contre-proposition (modifiables)
        self.auto_adoptes = []  # Options acceptées/refusées par vendeur (non modifiables)
        
        self.setWindowTitle("✅ Répondre aux propositions du vendeur")
        self.setMinimumSize(850, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Vérifier si l'affaire est clôturée
        devis_info = self.db.get_devis_info(devis_id)
        affaire_id = devis_info[1] if devis_info else None
        self.affaire_cloturee, self.statut_cloture = self.db.is_affaire_cloturee(affaire_id) if affaire_id else (False, None)
        
        # Header
        lbl = QLabel("✅ Accepter ou refuser les propositions du vendeur")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #00b894;")
        layout.addWidget(lbl)
        
        # Message si affaire clôturée
        if self.affaire_cloturee:
            statut_texte = {"gagne": "✅ GAGNÉE", "perdu": "❌ PERDUE", "annule": "🚫 ANNULÉE"}.get(self.statut_cloture, self.statut_cloture)
            lbl_cloture = QLabel(f"⚠️ Cette affaire est clôturée ({statut_texte}). Aucune modification n'est possible.")
            lbl_cloture.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px; background-color: #2d3436; border-radius: 5px;")
            layout.addWidget(lbl_cloture)
        else:
            lbl_info = QLabel("Une nouvelle version du devis sera créée avec vos réponses.")
            lbl_info.setStyleSheet("color: #f39c12; font-style: italic;")
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
        
        btn_save = QPushButton("💾 Valider et créer nouvelle version")
        btn_save.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
        btn_save.clicked.connect(self.sauvegarder_reponses)
        btns.addWidget(btn_save)
        
        btn_cancel = QPushButton("Fermer" if self.affaire_cloturee else "Annuler")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        
        # Désactiver les boutons si l'affaire est clôturée
        if self.affaire_cloturee:
            btn_accept_all.setEnabled(False)
            btn_save.setEnabled(False)
            btn_accept_all.setStyleSheet("background-color: #636e72; color: #b2bec3; padding: 10px;")
            btn_save.setStyleSheet("background-color: #636e72; color: #b2bec3; padding: 10px;")
        
        layout.addLayout(btns)
    
    def charger_options(self):
        data = self.db.get_options_devis_detail(self.devis_id)
        has_vendeur_response = False
        
        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl_prod = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']}")
            lbl_prod.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl_prod)
            
            for opt in prod_data['options_standard']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    has_vendeur_response = True
                    self.ajouter_ligne_reponse(frame_layout, opt, 'standard')
            
            for opt in prod_data['options_perso']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    has_vendeur_response = True
                    self.ajouter_ligne_reponse(frame_layout, opt, 'perso')
            
            self.main_layout.addWidget(frame)
        
        if not has_vendeur_response:
            lbl_no = QLabel("⏳ Le vendeur n'a pas encore répondu à ce devis.")
            lbl_no.setStyleSheet("color: #f39c12; font-size: 14px;")
            self.main_layout.addWidget(lbl_no)
        
        self.main_layout.addStretch()
    
    def ajouter_ligne_reponse(self, layout, opt, type_opt):
        row = QFrame()
        row.setStyleSheet("background-color: #636e72; padding: 8px; margin: 3px; border-radius: 5px;")
        row_layout = QVBoxLayout()
        row.setLayout(row_layout)
        
        # Info option
        if type_opt == 'standard':
            lbl_nom = QLabel(f"📦 {opt['nom']} - Prix catalogue: {opt['prix']} €")
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "À définir"
            lbl_nom = QLabel(f"🔧 {opt['description']} - Demandé: {prix_txt}")
        lbl_nom.setStyleSheet("color: #dfe6e9; font-weight: bold;")
        row_layout.addWidget(lbl_nom)
        
        # Réponse vendeur
        statut_v = opt.get('statut_vendeur', 'en_attente')
        prix_v = opt.get('prix_propose')
        comm_v = opt.get('commentaire_vendeur', '')
        poids_v = opt.get('poids', 0) if type_opt == 'perso' else None
        
        colors = {'accepte': '#27ae60', 'refuse': '#e74c3c', 'contre_proposition': '#f39c12'}
        color = colors.get(statut_v, '#95a5a6')
        
        vendeur_layout = QHBoxLayout()
        lbl_v = QLabel(f"↳ Vendeur: {statut_v.upper()}")
        lbl_v.setStyleSheet(f"color: {color}; font-weight: bold;")
        vendeur_layout.addWidget(lbl_v)
        
        if prix_v:
            vendeur_layout.addWidget(QLabel(f"💰 {prix_v} €"))
        if poids_v and poids_v > 0:
            vendeur_layout.addWidget(QLabel(f"⚖️ {poids_v} kg"))
        if comm_v:
            vendeur_layout.addWidget(QLabel(f"💬 \"{comm_v}\""))
        vendeur_layout.addStretch()
        row_layout.addLayout(vendeur_layout)
        
        # Comportement selon le statut vendeur
        if statut_v == 'contre_proposition':
            # Contre-proposition: le client peut accepter ou refuser
            reponse_layout = QHBoxLayout()
            reponse_layout.addWidget(QLabel("Ma réponse:"))
            
            combo = QComboBox()
            combo.addItems(["en_attente", "accepte", "refuse"])
            combo.setCurrentText(opt.get('statut_acheteur', 'en_attente'))
            reponse_layout.addWidget(combo)
            
            input_comm = QLineEdit()
            input_comm.setPlaceholderText("Commentaire...")
            if opt.get('commentaire_acheteur'):
                input_comm.setText(opt['commentaire_acheteur'])
            reponse_layout.addWidget(input_comm)
            reponse_layout.addStretch()
            row_layout.addLayout(reponse_layout)
            
            # Ajouter aux réponses modifiables
            self.reponses.append({'type': type_opt, 'id': opt['id'], 'combo': combo, 'input_comm': input_comm, 'statut_vendeur': statut_v})
        else:
            # Accepté ou refusé par le vendeur: décision finale, non modifiable
            statut_final = "✅ ADOPTÉ" if statut_v == 'accepte' else "❌ REFUSÉ"
            color_final = "#27ae60" if statut_v == 'accepte' else "#e74c3c"
            
            lbl_final = QLabel(f"→ Décision vendeur: {statut_final} (non modifiable)")
            lbl_final.setStyleSheet(f"color: {color_final}; font-style: italic;")
            row_layout.addWidget(lbl_final)
            
            # Marquer comme auto-adopté (pas dans self.reponses car pas modifiable)
            self.auto_adoptes.append({'type': type_opt, 'id': opt['id'], 'statut_vendeur': statut_v})
        
        layout.addWidget(row)
    
    def tout_accepter(self):
        """Accepte toutes les contre-propositions."""
        for rep in self.reponses:
            rep['combo'].setCurrentText('accepte')
    
    def sauvegarder_reponses(self):
        # Les options acceptées/refusées par le vendeur sont automatiquement adoptées
        # On enregistre leur statut comme "accepte" côté acheteur
        for auto in self.auto_adoptes:
            statut_final = 'accepte'  # Le client accepte la décision du vendeur
            if auto['type'] == 'standard':
                self.db.repondre_option_standard_acheteur(auto['id'], statut_final, "")
            else:
                self.db.repondre_option_perso_acheteur(auto['id'], statut_final, "")
        
        # Traiter les contre-propositions (seules options modifiables par le client)
        toutes_decidees = True  # Toutes les contre-propositions ont une réponse (accepte ou refuse)
        
        for rep in self.reponses:
            statut = rep['combo'].currentText()
            commentaire = rep['input_comm'].text().strip()
            if rep['type'] == 'standard':
                self.db.repondre_option_standard_acheteur(rep['id'], statut, commentaire)
            else:
                self.db.repondre_option_perso_acheteur(rep['id'], statut, commentaire)
            
            # Vérifier si une contre-proposition est encore en attente
            if statut == 'en_attente':
                toutes_decidees = False
        
        # Clôturer si toutes les contre-propositions sont décidées (acceptées OU refusées)
        # OU s'il n'y a pas de contre-proposition (tout était accepté/refusé par vendeur)
        if toutes_decidees:
            devis_info = self.db.get_devis_info(self.devis_id)
            affaire_id = devis_info[1] if devis_info else None
            
            if affaire_id:
                # Créer une version finale du devis avec les prix définitifs
                final_id, final_version = self.db.creer_nouvelle_version_devis(self.devis_id, 'FINAL')
                
                # Clôturer l'affaire
                self.db.cloturer_affaire(affaire_id, 'gagne')
                
                # Afficher le devis final
                if final_id:
                    QMessageBox.information(self, "🎉 Affaire Conclue", 
                        f"Toutes les options ont été traitées.\n"
                        f"L'affaire a été clôturée avec succès !\n\n"
                        f"Devis final: V{final_version}\n\n"
                        f"Merci pour votre confiance.")
                    
                    # Ouvrir le détail du devis final
                    dialog = DetailDevisDialog(self.db, final_id, self)
                    dialog.exec()
                else:
                    QMessageBox.information(self, "🎉 Affaire Conclue", 
                        "Toutes les options ont été traitées.\n"
                        "L'affaire a été clôturée avec succès !\n\n"
                        "Merci pour votre confiance.")
                
                self.accept()
                return
        
        # Sinon, créer une nouvelle version du devis pour continuer la négociation
        new_id, new_version = self.db.creer_nouvelle_version_devis(self.devis_id, 'acheteur')
        
        if new_id:
            QMessageBox.information(self, "Succès", 
                f"Vos réponses ont été enregistrées.\nNouvelle version V{new_version} créée !")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de la création de la nouvelle version.")


class DetailDevisDialog(QDialog):
    """Dialog pour voir le détail d'un devis."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        
        info = self.db.get_devis_info(devis_id)
        version = info[2] if info else "?"
        numero = info[5] if info else "?"
        
        self.setWindowTitle(f"📋 Détail - {numero}-{version}")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        lbl = QLabel(f"📋 Devis {numero} - Version {version}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #74b9ff;")
        layout.addWidget(lbl)
        
        # Légende
        legende = QHBoxLayout()
        for txt, color in [("En attente", "#95a5a6"), ("Accepté", "#27ae60"), 
                           ("Refusé", "#e74c3c"), ("Contre-proposition", "#f39c12")]:
            lbl = QLabel(f"● {txt}")
            lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            legende.addWidget(lbl)
        legende.addStretch()
        layout.addLayout(legende)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.main_layout = QVBoxLayout()
        container.setLayout(self.main_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        self.charger_detail()
        
        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
    
    def get_emoji(self, statut):
        return {'en_attente': '⏳', 'accepte': '✅', 'refuse': '❌', 'contre_proposition': '💬'}.get(statut, '⏳')
    
    def get_color(self, statut):
        return {'en_attente': '#95a5a6', 'accepte': '#27ae60', 'refuse': '#e74c3c', 'contre_proposition': '#f39c12'}.get(statut, '#95a5a6')
    
    def charger_detail(self):
        data = self.db.get_options_devis_detail(self.devis_id)
        
        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl)
            
            if prod_data['options_standard'] or prod_data['options_perso']:
                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels(["Option", "Prix", "Vendeur", "Acheteur", "Commentaires"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
                all_opts = [(t, o) for t, o in [('std', x) for x in prod_data['options_standard']] + 
                            [('perso', x) for x in prod_data['options_perso']]]
                table.setRowCount(len(all_opts))
                
                for row, (t, opt) in enumerate(all_opts):
                    nom = opt['nom'] if t == 'std' else f"🔧 {opt['description']}"
                    prix = f"{opt['prix']} €" if t == 'std' else f"{opt.get('prix_demande', '-')} €"
                    
                    table.setItem(row, 0, QTableWidgetItem(nom))
                    table.setItem(row, 1, QTableWidgetItem(prix))
                    
                    st_v = opt.get('statut_vendeur') or 'en_attente'
                    item_v = QTableWidgetItem(f"{self.get_emoji(st_v)} {st_v}")
                    item_v.setForeground(QColor(self.get_color(st_v)))
                    table.setItem(row, 2, item_v)
                    
                    st_a = opt.get('statut_acheteur') or 'en_attente'
                    item_a = QTableWidgetItem(f"{self.get_emoji(st_a)} {st_a}")
                    item_a.setForeground(QColor(self.get_color(st_a)))
                    table.setItem(row, 3, item_a)
                    
                    comm = f"[V]{opt.get('commentaire_vendeur', '')} [A]{opt.get('commentaire_acheteur', '')}"
                    table.setItem(row, 4, QTableWidgetItem(comm.strip()))
                
                frame_layout.addWidget(table)
            
            self.main_layout.addWidget(frame)
        self.main_layout.addStretch()


class ClientWindow(QMainWindow):
    """Fenêtre principale pour le CLIENT."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 CLIENT - Configurateur de Devis")
        self.setGeometry(50, 50, 1100, 750)
        
        self.db = DatabaseManager()
        self.produit_widgets = []
        self.current_affaire_id = None
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        
        # Header
        header = QLabel("🛒 INTERFACE CLIENT - Demandes de devis")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00b894; padding: 10px;")
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_affaires = QWidget()
        self.tab_detail = QWidget()
        self.tab_nouveau = QWidget()
        
        self.tabs.addTab(self.tab_affaires, "📁 Mes Affaires")
        self.tabs.addTab(self.tab_detail, "📋 Détail Affaire")
        self.tabs.addTab(self.tab_nouveau, "➕ Nouveau Devis")
        
        self.setup_affaires_tab()
        self.setup_detail_tab()
        self.setup_nouveau_tab()
        
        self.charger_affaires()
        
        # Auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000)  # Refresh toutes les 10 secondes
    
    def auto_refresh(self):
        if self.current_affaire_id:
            self.charger_devis_affaire()
    
    def setup_affaires_tab(self):
        layout = QVBoxLayout()
        self.tab_affaires.setLayout(layout)
        
        # Bouton nouvelle affaire
        btn_new = QPushButton("📁 Nouvelle Affaire")
        btn_new.setStyleSheet("background-color: #00b894; color: white; padding: 10px; font-size: 14px;")
        btn_new.clicked.connect(self.nouvelle_affaire)
        layout.addWidget(btn_new)
        
        # Table des affaires
        self.table_affaires = QTableWidget()
        self.table_affaires.setColumnCount(4)
        self.table_affaires.setHorizontalHeaderLabels(["N° Affaire", "Client", "Titre", "Date"])
        self.table_affaires.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_affaires.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_affaires.doubleClicked.connect(self.ouvrir_affaire)
        layout.addWidget(self.table_affaires)
        
        btn_open = QPushButton("📂 Ouvrir l'affaire sélectionnée")
        btn_open.clicked.connect(self.ouvrir_affaire)
        layout.addWidget(btn_open)
    
    def setup_detail_tab(self):
        layout = QVBoxLayout()
        self.tab_detail.setLayout(layout)
        
        self.lbl_affaire_titre = QLabel("Sélectionnez une affaire")
        self.lbl_affaire_titre.setStyleSheet("font-size: 16px; font-weight: bold; color: #74b9ff;")
        layout.addWidget(self.lbl_affaire_titre)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Liste des devis
        left = QWidget()
        left_layout = QVBoxLayout()
        left.setLayout(left_layout)
        
        left_layout.addWidget(QLabel("📄 Versions du devis:"))
        self.table_devis = QTableWidget()
        self.table_devis.setColumnCount(3)
        self.table_devis.setHorizontalHeaderLabels(["Version", "Date", "Total"])
        self.table_devis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devis.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.table_devis)
        
        btns = QHBoxLayout()
        btn_voir = QPushButton("👁️ Voir détail")
        btn_voir.clicked.connect(self.voir_detail)
        btns.addWidget(btn_voir)
        
        btn_repondre = QPushButton("✅ Répondre au vendeur")
        btn_repondre.setStyleSheet("background-color: #27ae60; color: white;")
        btn_repondre.clicked.connect(self.repondre_vendeur)
        btns.addWidget(btn_repondre)
        
        btn_pdf = QPushButton("📄 Générer PDF")
        btn_pdf.setStyleSheet("background-color: #3498db; color: white;")
        btn_pdf.clicked.connect(self.generer_pdf)
        btns.addWidget(btn_pdf)
        left_layout.addLayout(btns)
        
        btn_nouveau = QPushButton("➕ Nouveau devis")
        btn_nouveau.setStyleSheet("background-color: #9b59b6; color: white;")
        btn_nouveau.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        left_layout.addWidget(btn_nouveau)
        
        splitter.addWidget(left)
        
        # Zone commentaires
        right = QWidget()
        right_layout = QVBoxLayout()
        right.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("💬 Échanges avec le vendeur:"))
        self.txt_commentaires = QTextEdit()
        self.txt_commentaires.setReadOnly(True)
        right_layout.addWidget(self.txt_commentaires)
        
        self.input_commentaire = QLineEdit()
        self.input_commentaire.setPlaceholderText("Écrire un message...")
        right_layout.addWidget(self.input_commentaire)
        
        btn_send = QPushButton("📤 Envoyer")
        btn_send.clicked.connect(self.envoyer_commentaire)
        right_layout.addWidget(btn_send)
        
        splitter.addWidget(right)
    
    def setup_nouveau_tab(self):
        layout = QVBoxLayout()
        self.tab_nouveau.setLayout(layout)
        
        self.lbl_devis_ref = QLabel("Affaire: Aucune sélectionnée")
        self.lbl_devis_ref.setStyleSheet("color: #b2bec3;")
        layout.addWidget(self.lbl_devis_ref)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.container_hex = QWidget()
        self.layout_hex = QVBoxLayout()
        self.container_hex.setLayout(self.layout_hex)
        scroll.setWidget(self.container_hex)
        layout.addWidget(scroll)
        
        btn_add = QPushButton("➕ Ajouter un Produit")
        btn_add.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px;")
        btn_add.clicked.connect(self.ajouter_produit)
        layout.addWidget(btn_add)
        
        # Total
        self.lbl_total = QLabel("TOTAL: 0.00 €")
        self.lbl_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #00b894;")
        layout.addWidget(self.lbl_total)
        
        # Commentaire client
        group_commentaire = QGroupBox("💬 Commentaire / Notes pour le vendeur")
        comm_layout = QVBoxLayout()
        group_commentaire.setLayout(comm_layout)
        self.input_commentaire_devis = QTextEdit()
        self.input_commentaire_devis.setPlaceholderText("Ajoutez vos remarques, contraintes particulières, délais souhaités, questions...")
        self.input_commentaire_devis.setMaximumHeight(100)
        comm_layout.addWidget(self.input_commentaire_devis)
        layout.addWidget(group_commentaire)
        
        btn_submit = QPushButton("📤 Soumettre le devis")
        btn_submit.setStyleSheet("background-color: #3498db; color: white; padding: 15px; font-size: 16px;")
        btn_submit.clicked.connect(self.soumettre_devis)
        layout.addWidget(btn_submit)
    
    def nouvelle_affaire(self):
        dialog = NouvelleAffaireDialog(self.db, self)
        if dialog.exec():
            data = dialog.get_data()
            if not data['titre']:
                QMessageBox.warning(self, "Erreur", "Le titre du projet est requis.")
                return
            
            # Utiliser le client existant ou en créer un nouveau
            if data['client_id']:
                client_id = data['client_id']
            else:
                if not data['societe']:
                    QMessageBox.warning(self, "Erreur", "Le nom de société est requis pour un nouveau client.")
                    return
                client_id = self.db.creer_ou_obtenir_client(
                    data['societe'], data['contact'], data['email'], data['tel'])
            
            affaire_id, numero = self.db.creer_affaire(client_id, data['titre'], data['description'])
            
            if affaire_id:
                QMessageBox.information(self, "Succès", f"Affaire {numero} créée !")
                self.charger_affaires()
    
    def charger_affaires(self):
        affaires = self.db.get_liste_affaires()
        self.table_affaires.setRowCount(len(affaires))
        
        for row, aff in enumerate(affaires):
            self.table_affaires.setItem(row, 0, QTableWidgetItem(aff[1]))
            self.table_affaires.item(row, 0).setData(Qt.ItemDataRole.UserRole, aff[0])
            self.table_affaires.setItem(row, 1, QTableWidgetItem(aff[2] or ""))
            self.table_affaires.setItem(row, 2, QTableWidgetItem(aff[3] or ""))
            self.table_affaires.setItem(row, 3, QTableWidgetItem(aff[4] or ""))
    
    def ouvrir_affaire(self):
        selected = self.table_affaires.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        self.current_affaire_id = self.table_affaires.item(row, 0).data(Qt.ItemDataRole.UserRole)
        numero = self.table_affaires.item(row, 0).text()
        titre = self.table_affaires.item(row, 2).text()
        
        self.lbl_affaire_titre.setText(f"📁 {numero} - {titre}")
        self.lbl_devis_ref.setText(f"Affaire: {numero}")
        
        self.charger_devis_affaire()
        self.charger_commentaires()
        self.tabs.setCurrentIndex(1)
    
    def charger_devis_affaire(self):
        if not self.current_affaire_id:
            return
        
        devis = self.db.get_devis_affaire(self.current_affaire_id)
        self.table_devis.setRowCount(len(devis))
        
        for row, d in enumerate(devis):
            item_v = QTableWidgetItem(f"V{d[1]}")
            item_v.setData(Qt.ItemDataRole.UserRole, d[0])
            self.table_devis.setItem(row, 0, item_v)
            self.table_devis.setItem(row, 1, QTableWidgetItem(d[2] or ""))
            self.table_devis.setItem(row, 2, QTableWidgetItem(f"{d[3]} €" if d[3] else "-"))
    
    def charger_commentaires(self):
        if not self.current_affaire_id:
            return
        
        comments = self.db.get_commentaires_affaire(self.current_affaire_id)
        html = ""
        for c in comments:
            role = c[2]
            color = "#00b894" if role == "acheteur" else "#e74c3c"
            html += f"<p style='color:{color};'><b>[{role.upper()}] {c[1]}</b> - {c[4]}<br/>{c[3]}</p>"
        
        self.txt_commentaires.setHtml(html)
    
    def envoyer_commentaire(self):
        if not self.current_affaire_id:
            return
        
        contenu = self.input_commentaire.text().strip()
        if contenu:
            self.db.ajouter_commentaire(self.current_affaire_id, "Client", "acheteur", contenu)
            self.input_commentaire.clear()
            self.charger_commentaires()
    
    def voir_detail(self):
        selected = self.table_devis.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        
        devis_id = self.table_devis.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = DetailDevisDialog(self.db, devis_id, self)
        dialog.exec()
    
    def repondre_vendeur(self):
        selected = self.table_devis.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        
        devis_id = self.table_devis.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = ReponseAcheteurDialog(self.db, devis_id, self)
        if dialog.exec():
            self.charger_devis_affaire()
    
    def generer_pdf(self):
        """Génère un PDF professionnel du devis sélectionné."""
        selected = self.table_devis.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        
        devis_id = self.table_devis.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        
        # Générer le PDF avec le nouveau générateur professionnel
        output_dir = os.path.join(os.path.dirname(__file__), "generated_devis")
        filepath = generer_devis_pdf(
            self.db, 
            devis_id, 
            client_nom=self.current_affaire_client if hasattr(self, 'current_affaire_client') else "",
            output_dir=output_dir
        )
        
        if filepath:
            QMessageBox.information(self, "✅ PDF Généré", 
                f"Le devis professionnel a été créé:\n\n{filepath}")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de générer le PDF.")
    
    def ajouter_produit(self):
        widget = ProduitConfigWidget(self.db, len(self.produit_widgets), 
                                       self.recalculer_total, self.supprimer_produit)
        self.produit_widgets.append(widget)
        self.layout_hex.addWidget(widget)
        self.recalculer_total()
    
    def supprimer_produit(self, widget):
        self.produit_widgets.remove(widget)
        widget.deleteLater()
        for i, w in enumerate(self.produit_widgets):
            w.index = i
            w.lbl_title.setText(f"🔷 Produit #{i + 1}")
        self.recalculer_total()
    
    def recalculer_total(self):
        total = sum(w.calculer_sous_total() for w in self.produit_widgets)
        self.lbl_total.setText(f"TOTAL: {total:.2f} €")
    
    def soumettre_devis(self):
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Erreur", "Sélectionnez d'abord une affaire.")
            return
        
        if not self.produit_widgets:
            QMessageBox.warning(self, "Erreur", "Ajoutez au moins un produit.")
            return
        
        # Vérifier les limites de poids pour chaque produit
        for i, w in enumerate(self.produit_widgets):
            if not w.is_poids_valide():
                prod_data = w.combo_modele.currentData()
                nom = prod_data[1] if prod_data else f"Produit #{i+1}"
                charge_max = prod_data[3] if prod_data and len(prod_data) > 3 else 1000
                poids_actuel = w.calculer_poids_total()
                limite = charge_max * 0.85
                
                QMessageBox.warning(self, "⚠️ Limite de poids dépassée", 
                    f"Le produit '{nom}' dépasse la limite de charge autorisée.\n\n"
                    f"Charge actuelle: {poids_actuel:.1f} kg\n"
                    f"Limite (85%): {limite:.1f} kg\n"
                    f"Charge max: {charge_max:.1f} kg\n\n"
                    f"Veuillez retirer des options pour respecter la limite.")
                return
        
        produits_data = []
        for w in self.produit_widgets:
            data = w.get_data()
            if data:
                produits_data.append((
                    data['produit_id'], data['quantite'], data['prix'],
                    data['options_ids'], data['options_perso']
                ))
        
        # Récupérer le commentaire client
        commentaire_client = self.input_commentaire_devis.toPlainText().strip()
        
        devis_id, version = self.db.creer_devis_pour_affaire(self.current_affaire_id, produits_data, notes=commentaire_client)
        
        if devis_id:
            QMessageBox.information(self, "Succès", f"Devis V{version} soumis !")
            self.charger_devis_affaire()
            for w in self.produit_widgets[:]:
                self.supprimer_produit(w)
            self.input_commentaire_devis.clear()
            self.tabs.setCurrentIndex(1)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Thème sombre élégant
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 35, 40))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 30, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 45, 50))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Button, QColor(52, 73, 94))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(52, 152, 219))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 240, 241))
    app.setPalette(palette)
    
    # Styles CSS globaux pour une interface plus belle
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e2328;
        }
        QTabWidget::pane {
            border: 1px solid #34495e;
            border-radius: 5px;
            background-color: #1e2328;
        }
        QTabBar::tab {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        QTabBar::tab:hover:!selected {
            background-color: #34495e;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #21618c;
        }
        QPushButton:disabled {
            background-color: #5d6d7e;
            color: #aeb6bf;
        }
        QTableWidget {
            background-color: #1e2328;
            alternate-background-color: #252a30;
            gridline-color: #34495e;
            border: 1px solid #34495e;
            border-radius: 5px;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        QHeaderView::section {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 4px;
            padding: 6px;
        }
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 2px solid #3498db;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #34495e;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #3498db;
        }
        QScrollBar:vertical {
            background-color: #1e2328;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #34495e;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #3498db;
        }
        QFrame#produit_frame {
            background-color: #252a30;
            border: 1px solid #34495e;
            border-radius: 8px;
        }
        QLabel#title_label {
            color: #3498db;
            font-size: 14px;
            font-weight: bold;
        }
        QLabel#total_label {
            color: #2ecc71;
            font-size: 18px;
            font-weight: bold;
        }
        QProgressBar {
            border: 1px solid #34495e;
            border-radius: 4px;
            text-align: center;
            background-color: #2c3e50;
        }
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 3px;
        }
    """)
    
    window = ClientWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
