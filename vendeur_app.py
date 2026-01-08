"""
Application VENDEUR - Configurateur de Devis
Interface dédiée au vendeur pour répondre aux demandes de devis.
"""
import sys
import os

# Ajouter le chemin racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QFrame, QScrollArea, QTextEdit, QComboBox, QSpinBox,
                             QLineEdit, QGroupBox, QMessageBox, QDialog, QSplitter,
                             QDialogButtonBox, QFormLayout, QRadioButton, QButtonGroup,
                             QDoubleSpinBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor
import datetime
from src.models.db_manager import DatabaseManager
from src.utils.pdf_generator import generer_devis_pdf


class ClotureAffaireDialog(QDialog):
    """Dialog pour clôturer une affaire."""
    
    def __init__(self, affaire_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏁 Clôturer l'affaire")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Info affaire
        lbl_info = QLabel(f"Clôturer l'affaire: {affaire_info}")
        lbl_info.setStyleSheet("font-weight: bold; color: #74b9ff;")
        layout.addWidget(lbl_info)
        
        layout.addSpacing(15)
        
        # Résultat
        group = QGroupBox("Résultat de l'affaire")
        group_layout = QVBoxLayout()
        group.setLayout(group_layout)
        
        self.btn_group = QButtonGroup()
        
        self.radio_gagne = QRadioButton("✅ GAGNÉ - Le client a accepté")
        self.radio_gagne.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.btn_group.addButton(self.radio_gagne)
        group_layout.addWidget(self.radio_gagne)
        
        self.radio_perdu = QRadioButton("❌ PERDU - Le client a refusé")
        self.radio_perdu.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.btn_group.addButton(self.radio_perdu)
        group_layout.addWidget(self.radio_perdu)
        
        self.radio_annule = QRadioButton("⚪ ANNULÉ - Affaire sans suite")
        self.radio_annule.setStyleSheet("color: #95a5a6; font-weight: bold;")
        self.btn_group.addButton(self.radio_annule)
        group_layout.addWidget(self.radio_annule)
        
        layout.addWidget(group)
        
        # Commentaire
        layout.addWidget(QLabel("Commentaire de clôture:"))
        self.input_commentaire = QTextEdit()
        self.input_commentaire.setPlaceholderText("Raison, notes finales...")
        self.input_commentaire.setMaximumHeight(80)
        layout.addWidget(self.input_commentaire)
        
        # Boutons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.valider)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
    
    def valider(self):
        if not self.btn_group.checkedButton():
            QMessageBox.warning(self, "Attention", "Sélectionnez un résultat.")
            return
        self.accept()
    
    def get_data(self):
        if self.radio_gagne.isChecked():
            resultat = "gagne"
        elif self.radio_perdu.isChecked():
            resultat = "perdu"
        else:
            resultat = "annule"
        
        return {
            'resultat': resultat,
            'commentaire': self.input_commentaire.toPlainText().strip()
        }


class ReponseVendeurDialog(QDialog):
    """Dialog pour que le vendeur réponde aux options d'un devis."""
    
    def __init__(self, db, devis_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.devis_id = devis_id
        self.reponses = []  # Options modifiables
        self.options_finalisees = []  # Options avec décision finale du client
        
        info = self.db.get_devis_info(devis_id)
        version = info[2] if info else "?"
        numero = info[5] if info else "?"
        affaire_id = info[1] if info else None
        
        # Vérifier si l'affaire est clôturée
        self.affaire_cloturee, self.statut_cloture = self.db.is_affaire_cloturee(affaire_id) if affaire_id else (False, None)
        
        self.setWindowTitle(f"📝 Répondre au devis {numero}-{version}")
        self.setMinimumSize(850, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        lbl = QLabel("📝 Évaluer et répondre aux demandes du client")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
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
        btn_save.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
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
        
        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet("background-color: #2d3436; padding: 10px; border-radius: 5px;")
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)
            
            lbl = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #74b9ff;")
            frame_layout.addWidget(lbl)
            
            if prod_data['options_standard']:
                frame_layout.addWidget(QLabel("📦 Options catalogue demandées:"))
                for opt in prod_data['options_standard']:
                    self.ajouter_ligne(frame_layout, opt, 'standard')
            
            if prod_data['options_perso']:
                frame_layout.addWidget(QLabel("🔧 Demandes spéciales:"))
                for opt in prod_data['options_perso']:
                    self.ajouter_ligne(frame_layout, opt, 'perso')
            
            self.main_layout.addWidget(frame)
        
        self.main_layout.addStretch()
    
    def ajouter_ligne(self, layout, opt, type_opt):
        row = QFrame()
        row.setStyleSheet("background-color: #636e72; padding: 8px; margin: 3px; border-radius: 5px;")
        row_layout = QVBoxLayout()
        row.setLayout(row_layout)
        
        # Info
        if type_opt == 'standard':
            poids_opt = opt.get('poids', 0)
            poids_txt = f" | {poids_opt} kg" if poids_opt else ""
            lbl = QLabel(f"• {opt['nom']} - Prix catalogue: {opt['prix']} €{poids_txt}")
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "Prix à définir"
            lbl = QLabel(f"• {opt['description']} - Demandé: {prix_txt}")
        lbl.setStyleSheet("color: #dfe6e9; font-weight: bold;")
        row_layout.addWidget(lbl)
        
        # Réponse acheteur s'il y en a une
        statut_acheteur = opt.get('statut_acheteur', 'en_attente')
        if statut_acheteur and statut_acheteur != 'en_attente':
            colors = {'accepte': '#27ae60', 'refuse': '#e74c3c'}
            color = colors.get(statut_acheteur, '#95a5a6')
            lbl_a = QLabel(f"↳ Réponse client: {statut_acheteur.upper()} {opt.get('commentaire_acheteur', '')}")
            lbl_a.setStyleSheet(f"color: {color};")
            row_layout.addWidget(lbl_a)
        
        # Si le client a REFUSÉ une contre-proposition, c'est final - non modifiable
        if statut_acheteur == 'refuse':
            lbl_final = QLabel("→ Le client a refusé cette option. Décision FINALE (non modifiable)")
            lbl_final.setStyleSheet("color: #e74c3c; font-style: italic; font-weight: bold;")
            row_layout.addWidget(lbl_final)
            
            # Stocker comme option finalisée (pas dans self.reponses)
            self.options_finalisees.append({'type': type_opt, 'id': opt['id'], 'statut': 'refuse'})
            layout.addWidget(row)
            return
        
        # Si le client a ACCEPTÉ, c'est aussi final
        if statut_acheteur == 'accepte':
            lbl_final = QLabel("→ Le client a accepté cette option. Décision FINALE (non modifiable)")
            lbl_final.setStyleSheet("color: #27ae60; font-style: italic; font-weight: bold;")
            row_layout.addWidget(lbl_final)
            
            self.options_finalisees.append({'type': type_opt, 'id': opt['id'], 'statut': 'accepte'})
            layout.addWidget(row)
            return
        
        # Ligne réponse vendeur (seulement si pas encore de décision finale du client)
        resp_layout = QHBoxLayout()
        resp_layout.addWidget(QLabel("Ma réponse:"))
        
        combo = QComboBox()
        combo.addItems(["en_attente", "accepte", "refuse", "contre_proposition"])
        combo.setCurrentText(opt.get('statut_vendeur', 'en_attente'))
        resp_layout.addWidget(combo)
        
        # Prix (modifiable UNIQUEMENT pour contre-proposition)
        resp_layout.addWidget(QLabel("Prix:"))
        spin_prix = QSpinBox()
        spin_prix.setMaximum(999999)
        spin_prix.setSuffix(" €")
        if type_opt == 'standard':
            spin_prix.setValue(int(opt['prix']))
        elif opt.get('prix_propose'):
            spin_prix.setValue(int(opt['prix_propose']))
        elif opt.get('prix_demande'):
            spin_prix.setValue(int(opt['prix_demande']))
        resp_layout.addWidget(spin_prix)
        
        # Fonction pour activer/désactiver le prix selon le statut
        def update_prix_enabled():
            is_contre_prop = combo.currentText() == 'contre_proposition'
            spin_prix.setEnabled(is_contre_prop)
            if is_contre_prop:
                spin_prix.setStyleSheet("background-color: #f39c12; color: black;")
            else:
                spin_prix.setStyleSheet("background-color: #636e72; color: #b2bec3;")
        
        combo.currentTextChanged.connect(update_prix_enabled)
        update_prix_enabled()  # Appliquer l'état initial
        
        # Champ poids pour les options personnalisées (défini par le vendeur)
        spin_poids = None
        if type_opt == 'perso':
            resp_layout.addWidget(QLabel("⚖️ Poids:"))
            spin_poids = QDoubleSpinBox()
            spin_poids.setMaximum(9999)
            spin_poids.setDecimals(1)
            spin_poids.setSuffix(" kg")
            if opt.get('poids'):
                spin_poids.setValue(float(opt['poids']))
            resp_layout.addWidget(spin_poids)
        
        input_comm = QLineEdit()
        input_comm.setPlaceholderText("Commentaire...")
        if opt.get('commentaire_vendeur'):
            input_comm.setText(opt['commentaire_vendeur'])
        resp_layout.addWidget(input_comm)
        
        row_layout.addLayout(resp_layout)
        layout.addWidget(row)
        
        # Stocker le prix original pour les options standard
        prix_original = opt['prix'] if type_opt == 'standard' else opt.get('prix_demande')
        
        self.reponses.append({
            'type': type_opt, 'id': opt['id'],
            'combo': combo, 'spin_prix': spin_prix, 'input_comm': input_comm,
            'spin_poids': spin_poids, 'prix_original': prix_original
        })
    
    def tout_accepter(self):
        for rep in self.reponses:
            rep['combo'].setCurrentText('accepte')
    
    def sauvegarder_reponses(self):
        for rep in self.reponses:
            statut = rep['combo'].currentText()
            commentaire = rep['input_comm'].text().strip()
            
            # Le prix proposé n'est utilisé que pour les contre-propositions
            if statut == 'contre_proposition':
                prix = rep['spin_prix'].value() if rep['spin_prix'].value() > 0 else None
            else:
                # Pour accepte/refuse, pas de prix proposé (on garde le prix original)
                prix = None
            
            if rep['type'] == 'standard':
                self.db.repondre_option_standard(rep['id'], statut, prix, commentaire)
            else:
                # Pour les options perso, récupérer aussi le poids défini par le vendeur
                poids = rep['spin_poids'].value() if rep['spin_poids'] else 0
                self.db.repondre_option_perso(rep['id'], statut, prix, commentaire, poids)
        
        # Créer nouvelle version
        new_id, new_version = self.db.creer_nouvelle_version_devis(self.devis_id, 'vendeur')
        
        if new_id:
            QMessageBox.information(self, "Succès", 
                f"Réponses enregistrées.\nNouvelle version V{new_version} créée !")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de la création de la version.")


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
            l = QLabel(f"● {txt}")
            l.setStyleSheet(f"color: {color}; font-weight: bold;")
            legende.addWidget(l)
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
        
        btn = QPushButton("Fermer")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
    
    def get_emoji(self, s):
        return {'en_attente': '⏳', 'accepte': '✅', 'refuse': '❌', 'contre_proposition': '💬'}.get(s, '⏳')
    
    def get_color(self, s):
        return {'en_attente': '#95a5a6', 'accepte': '#27ae60', 'refuse': '#e74c3c', 'contre_proposition': '#f39c12'}.get(s, '#95a5a6')
    
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
                table.setHorizontalHeaderLabels(["Option", "Prix", "Vendeur", "Client", "Commentaires"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                
                all_opts = [('std', o) for o in prod_data['options_standard']] + [('perso', o) for o in prod_data['options_perso']]
                table.setRowCount(len(all_opts))
                
                for row, (t, opt) in enumerate(all_opts):
                    nom = opt['nom'] if t == 'std' else f"🔧 {opt['description']}"
                    prix = f"{opt['prix']} €" if t == 'std' else f"{opt.get('prix_demande', '-')} €"
                    
                    table.setItem(row, 0, QTableWidgetItem(nom))
                    table.setItem(row, 1, QTableWidgetItem(prix))
                    
                    sv = opt.get('statut_vendeur') or 'en_attente'
                    iv = QTableWidgetItem(f"{self.get_emoji(sv)} {sv}")
                    iv.setForeground(QColor(self.get_color(sv)))
                    table.setItem(row, 2, iv)
                    
                    sa = opt.get('statut_acheteur') or 'en_attente'
                    ia = QTableWidgetItem(f"{self.get_emoji(sa)} {sa}")
                    ia.setForeground(QColor(self.get_color(sa)))
                    table.setItem(row, 3, ia)
                    
                    comm = f"[V]{opt.get('commentaire_vendeur', '')} [A]{opt.get('commentaire_acheteur', '')}"
                    table.setItem(row, 4, QTableWidgetItem(comm.strip()))
                
                frame_layout.addWidget(table)
            
            self.main_layout.addWidget(frame)
        self.main_layout.addStretch()


class VendeurWindow(QMainWindow):
    """Fenêtre principale pour le VENDEUR."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏭 VENDEUR - Configurateur de Devis")
        self.setGeometry(600, 50, 1100, 750)
        
        self.db = DatabaseManager()
        self.current_affaire_id = None
        self.current_affaire_numero = ""
        self.current_affaire_client = ""
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        
        # Header
        header = QLabel("🏭 INTERFACE VENDEUR - Gestion des devis")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #e74c3c; padding: 10px;")
        main_layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.tab_affaires = QWidget()
        self.tab_detail = QWidget()
        
        self.tabs.addTab(self.tab_affaires, "📁 Toutes les Affaires")
        self.tabs.addTab(self.tab_detail, "📋 Détail & Réponse")
        
        self.setup_affaires_tab()
        self.setup_detail_tab()
        
        self.charger_affaires()
        
        # Auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(10000)
    
    def auto_refresh(self):
        self.charger_affaires()
        if self.current_affaire_id:
            self.charger_devis_affaire()
    
    def setup_affaires_tab(self):
        layout = QVBoxLayout()
        self.tab_affaires.setLayout(layout)
        
        layout.addWidget(QLabel("📁 Liste des affaires clients:"))
        
        self.table_affaires = QTableWidget()
        self.table_affaires.setColumnCount(5)
        self.table_affaires.setHorizontalHeaderLabels(["N° Affaire", "Client", "Titre", "Date", "Nb Devis"])
        self.table_affaires.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_affaires.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_affaires.doubleClicked.connect(self.ouvrir_affaire)
        layout.addWidget(self.table_affaires)
        
        btn = QPushButton("📂 Ouvrir l'affaire")
        btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        btn.clicked.connect(self.ouvrir_affaire)
        layout.addWidget(btn)
    
    def setup_detail_tab(self):
        layout = QVBoxLayout()
        self.tab_detail.setLayout(layout)
        
        # Header avec statut
        header_layout = QHBoxLayout()
        self.lbl_affaire = QLabel("Sélectionnez une affaire")
        self.lbl_affaire.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        header_layout.addWidget(self.lbl_affaire)
        
        header_layout.addStretch()
        
        self.lbl_statut = QLabel("")
        self.lbl_statut.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px 10px; border-radius: 5px;")
        header_layout.addWidget(self.lbl_statut)
        
        self.btn_cloturer = QPushButton("🏁 Clôturer l'affaire")
        self.btn_cloturer.setStyleSheet("background-color: #8e44ad; color: white; padding: 8px;")
        self.btn_cloturer.clicked.connect(self.cloturer_affaire)
        header_layout.addWidget(self.btn_cloturer)
        
        layout.addLayout(header_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Liste devis
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
        
        btn_repondre = QPushButton("📝 Répondre au client")
        btn_repondre.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_repondre.clicked.connect(self.repondre_client)
        btns.addWidget(btn_repondre)
        
        btn_pdf = QPushButton("📄 Générer PDF")
        btn_pdf.setStyleSheet("background-color: #3498db; color: white;")
        btn_pdf.clicked.connect(self.generer_pdf)
        btns.addWidget(btn_pdf)
        left_layout.addLayout(btns)
        
        splitter.addWidget(left)
        
        # Commentaires
        right = QWidget()
        right_layout = QVBoxLayout()
        right.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("💬 Échanges avec le client:"))
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
    
    def charger_affaires(self):
        affaires = self.db.get_liste_affaires()
        self.table_affaires.setRowCount(len(affaires))
        
        for row, aff in enumerate(affaires):
            item = QTableWidgetItem(aff[1])
            item.setData(Qt.ItemDataRole.UserRole, aff[0])
            self.table_affaires.setItem(row, 0, item)
            self.table_affaires.setItem(row, 1, QTableWidgetItem(aff[2] or ""))
            self.table_affaires.setItem(row, 2, QTableWidgetItem(aff[3] or ""))
            self.table_affaires.setItem(row, 3, QTableWidgetItem(aff[4] or ""))
            
            # Compter les devis
            devis = self.db.get_devis_affaire(aff[0])
            self.table_affaires.setItem(row, 4, QTableWidgetItem(str(len(devis))))
    
    def ouvrir_affaire(self):
        selected = self.table_affaires.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        self.current_affaire_id = self.table_affaires.item(row, 0).data(Qt.ItemDataRole.UserRole)
        numero = self.table_affaires.item(row, 0).text()
        client = self.table_affaires.item(row, 1).text()
        titre = self.table_affaires.item(row, 2).text()
        statut = self.table_affaires.item(row, 3).text()
        
        self.current_affaire_numero = numero
        self.current_affaire_client = client
        
        self.lbl_affaire.setText(f"📁 {numero} - {client} - {titre}")
        
        # Afficher le statut avec couleur
        self.update_statut_label(statut)
        
        self.charger_devis_affaire()
        self.charger_commentaires()
        self.tabs.setCurrentIndex(1)
    
    def update_statut_label(self, statut):
        """Met à jour l'affichage du statut et le bouton clôturer."""
        statut_styles = {
            'en_cours': ('🔄 En cours', '#3498db'),
            'gagne': ('✅ GAGNÉ', '#27ae60'),
            'perdu': ('❌ PERDU', '#e74c3c'),
            'annule': ('⚪ Annulé', '#95a5a6')
        }
        txt, color = statut_styles.get(statut, ('🔄 En cours', '#3498db'))
        self.lbl_statut.setText(txt)
        self.lbl_statut.setStyleSheet(f"font-size: 14px; font-weight: bold; padding: 5px 10px; border-radius: 5px; background-color: {color}; color: white;")
        
        # Désactiver le bouton clôturer si l'affaire est déjà clôturée
        if statut in ('gagne', 'perdu', 'annule'):
            self.btn_cloturer.setEnabled(False)
            self.btn_cloturer.setStyleSheet("background-color: #636e72; color: #b2bec3; padding: 8px;")
            self.btn_cloturer.setText("🔒 Affaire clôturée")
        else:
            self.btn_cloturer.setEnabled(True)
            self.btn_cloturer.setStyleSheet("background-color: #8e44ad; color: white; padding: 8px;")
            self.btn_cloturer.setText("🏁 Clôturer l'affaire")
    
    def cloturer_affaire(self):
        """Ouvre le dialog pour clôturer l'affaire."""
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez une affaire.")
            return
        
        # Vérifier si l'affaire est déjà clôturée
        est_cloturee, statut = self.db.is_affaire_cloturee(self.current_affaire_id)
        if est_cloturee:
            QMessageBox.warning(self, "Affaire clôturée", 
                f"Cette affaire est déjà clôturée ({statut.upper()}).\nAucune modification n'est possible.")
            return
        
        affaire_info = f"{self.current_affaire_numero} - {self.current_affaire_client}"
        dialog = ClotureAffaireDialog(affaire_info, self)
        
        if dialog.exec():
            data = dialog.get_data()
            
            # Si gagnée, créer une version finale du devis avant clôture
            final_id = None
            final_version = None
            if data['resultat'] == 'gagne':
                # Trouver le dernier devis de l'affaire
                devis_list = self.db.get_devis_affaire(self.current_affaire_id)
                if devis_list:
                    dernier_devis_id = devis_list[-1][0]  # Dernier devis (plus grande version)
                    final_id, final_version = self.db.creer_nouvelle_version_devis(dernier_devis_id, 'FINAL')
            
            if self.db.cloturer_affaire(self.current_affaire_id, data['resultat'], data['commentaire']):
                msg = f"Affaire clôturée: {data['resultat'].upper()}"
                if final_id and final_version:
                    msg += f"\n\nDevis final: V{final_version}"
                    # Afficher le détail du devis final
                    detail_dialog = DetailDevisDialog(self.db, final_id, self)
                    QMessageBox.information(self, "Succès", msg)
                    detail_dialog.exec()
                else:
                    QMessageBox.information(self, "Succès", msg)
                
                self.update_statut_label(data['resultat'])
                self.charger_affaires()
                self.charger_commentaires()
    
    def charger_devis_affaire(self):
        if not self.current_affaire_id:
            return
        
        devis = self.db.get_devis_affaire(self.current_affaire_id)
        self.table_devis.setRowCount(len(devis))
        
        for row, d in enumerate(devis):
            item = QTableWidgetItem(f"V{d[1]}")
            item.setData(Qt.ItemDataRole.UserRole, d[0])
            self.table_devis.setItem(row, 0, item)
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
            self.db.ajouter_commentaire(self.current_affaire_id, "Vendeur", "vendeur", contenu)
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
    
    def repondre_client(self):
        selected = self.table_devis.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        
        devis_id = self.table_devis.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = ReponseVendeurDialog(self.db, devis_id, self)
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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Thème sombre élégant (rouge pour vendeur)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 35, 40))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 30, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 45, 50))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Button, QColor(94, 52, 52))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(231, 76, 60))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(231, 76, 60))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 240, 241))
    app.setPalette(palette)
    
    # Styles CSS globaux pour une interface plus belle (thème rouge vendeur)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e2328;
        }
        QTabWidget::pane {
            border: 1px solid #5e3434;
            border-radius: 5px;
            background-color: #1e2328;
        }
        QTabBar::tab {
            background-color: #4a2c2c;
            color: #ecf0f1;
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        QTabBar::tab:selected {
            background-color: #e74c3c;
            color: white;
        }
        QTabBar::tab:hover:!selected {
            background-color: #5e3434;
        }
        QPushButton {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
        QPushButton:pressed {
            background-color: #922b21;
        }
        QPushButton:disabled {
            background-color: #5d6d7e;
            color: #aeb6bf;
        }
        QTableWidget {
            background-color: #1e2328;
            alternate-background-color: #252a30;
            gridline-color: #5e3434;
            border: 1px solid #5e3434;
            border-radius: 5px;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QTableWidget::item:selected {
            background-color: #e74c3c;
            color: white;
        }
        QHeaderView::section {
            background-color: #4a2c2c;
            color: #ecf0f1;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #5e3434;
            border-radius: 4px;
            padding: 6px;
        }
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 2px solid #e74c3c;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #5e3434;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #e74c3c;
        }
        QScrollBar:vertical {
            background-color: #1e2328;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #5e3434;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #e74c3c;
        }
        QFrame#produit_frame {
            background-color: #252a30;
            border: 1px solid #5e3434;
            border-radius: 8px;
        }
        QLabel#title_label {
            color: #e74c3c;
            font-size: 14px;
            font-weight: bold;
        }
        QLabel#total_label {
            color: #2ecc71;
            font-size: 18px;
            font-weight: bold;
        }
        QProgressBar {
            border: 1px solid #5e3434;
            border-radius: 4px;
            text-align: center;
            background-color: #2c3e50;
        }
        QProgressBar::chunk {
            background-color: #e74c3c;
            border-radius: 3px;
        }
    """)
    
    window = VendeurWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
