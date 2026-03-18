# ──────────────────────────────────────────────────────────────────────────────
# src/views/vendeur_dialogs.py — Dialogues de l'interface VENDEUR
# ──────────────────────────────────────────────────────────────────────────────
# Contient les boîtes de dialogue propres au vendeur : ClotureAffaireDialog
# pour clôturer une affaire (gagnée, perdue, annulée), et ReponseVendeurDialog
# pour répondre option par option à une demande de devis (accepter, refuser,
# ou faire une contre-proposition avec prix et commentaire).
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QWidget, QFrame, QComboBox, QSpinBox,
                             QDoubleSpinBox, QLineEdit, QGroupBox, QMessageBox,
                             QDialogButtonBox, QRadioButton, QButtonGroup, QTextEdit)
from src.constants import STATUT_CLOTURE_LABELS, get_statut_color
from src.views.theme import S


class ClotureAffaireDialog(QDialog):
    """Dialog pour clôturer une affaire (UI pure, pas de logique métier)."""

    def __init__(self, affaire_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🏁 Clôturer l'affaire")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl = QLabel(f"Clôturer l'affaire: {affaire_info}")
        lbl.setStyleSheet(S.LBL_BOLD_BLUE)
        layout.addWidget(lbl)
        layout.addSpacing(15)

        group = QGroupBox("Résultat de l'affaire")
        gl = QVBoxLayout()
        group.setLayout(gl)

        self.btn_group = QButtonGroup()

        self.radio_gagne = QRadioButton("✅ GAGNÉ - Le client a accepté")
        self.radio_gagne.setStyleSheet(S.bold("#27ae60"))
        self.btn_group.addButton(self.radio_gagne)
        gl.addWidget(self.radio_gagne)

        self.radio_perdu = QRadioButton("❌ PERDU - Le client a refusé")
        self.radio_perdu.setStyleSheet(S.bold("#e74c3c"))
        self.btn_group.addButton(self.radio_perdu)
        gl.addWidget(self.radio_perdu)

        self.radio_annule = QRadioButton("⚪ ANNULÉ - Affaire sans suite")
        self.radio_annule.setStyleSheet(S.bold("#95a5a6"))
        self.btn_group.addButton(self.radio_annule)
        gl.addWidget(self.radio_annule)

        layout.addWidget(group)

        layout.addWidget(QLabel("Commentaire de clôture:"))
        self.input_commentaire = QTextEdit()
        self.input_commentaire.setPlaceholderText("Raison, notes finales...")
        self.input_commentaire.setMaximumHeight(80)
        layout.addWidget(self.input_commentaire)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._valider)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _valider(self):
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
            'commentaire': self.input_commentaire.toPlainText().strip(),
        }


class ReponseVendeurDialog(QDialog):
    """Dialog pour que le vendeur réponde aux options d'un devis.
    Reçoit le controller pour la logique métier (sauvegarde, versioning)."""

    def __init__(self, controller, devis_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.devis_id = devis_id
        self._reponse_widgets = []
        self._options_finalisees = []

        info = self.controller.get_devis_info(devis_id)
        version = info[2] if info else "?"
        numero = info[5] if info else "?"
        affaire_id = info[1] if info else None

        self.affaire_cloturee, self.statut_cloture = (
            self.controller.is_affaire_cloturee(affaire_id) if affaire_id else (False, None))

        self.setWindowTitle(f"📝 Répondre au devis {numero}-{version}")
        self.setMinimumSize(850, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl = QLabel("📝 Évaluer et répondre aux demandes du client")
        lbl.setStyleSheet(S.TITLE_VENDEUR)
        layout.addWidget(lbl)

        if self.affaire_cloturee:
            txt = STATUT_CLOTURE_LABELS.get(self.statut_cloture, self.statut_cloture)
            lbl_c = QLabel(f"⚠️ Affaire clôturée ({txt}). Aucune modification possible.")
            lbl_c.setStyleSheet(S.ALERT_ERROR)
            layout.addWidget(lbl_c)
        else:
            lbl_i = QLabel("Une nouvelle version du devis sera créée avec vos réponses.")
            lbl_i.setStyleSheet(S.LBL_INFO)
            layout.addWidget(lbl_i)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.main_layout = QVBoxLayout()
        container.setLayout(self.main_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self._charger_options()

        # --- Boutons ---
        btns = QHBoxLayout()
        btn_all = QPushButton("✅ Tout accepter")
        btn_all.setStyleSheet(S.BTN_SUCCESS + S.BTN_ACTION)
        btn_all.clicked.connect(self._tout_accepter)
        btns.addWidget(btn_all)

        btn_save = QPushButton("💾 Valider et créer nouvelle version")
        btn_save.setStyleSheet(S.BTN_DANGER + S.BTN_ACTION)
        btn_save.clicked.connect(self._sauvegarder)
        btns.addWidget(btn_save)

        btn_cancel = QPushButton("Fermer" if self.affaire_cloturee else "Annuler")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        if self.affaire_cloturee:
            for b in (btn_all, btn_save):
                b.setEnabled(False)
                b.setStyleSheet(S.BTN_DISABLED)

        layout.addLayout(btns)

    def _charger_options(self):
        data = self.controller.get_devis_detail(self.devis_id)

        for prod in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet(S.FRAME_DARK)
            fl = QVBoxLayout()
            frame.setLayout(fl)

            lbl = QLabel(f"🔷 {prod['nom']} x{prod['quantite']} - {prod['prix_unitaire']} €/u")
            lbl.setStyleSheet(S.LBL_PRODUCT)
            fl.addWidget(lbl)

            if prod['options_standard']:
                fl.addWidget(QLabel("📦 Options catalogue demandées:"))
                for opt in prod['options_standard']:
                    self._ajouter_ligne(fl, opt, 'standard')

            if prod['options_perso']:
                fl.addWidget(QLabel("🔧 Demandes spéciales:"))
                for opt in prod['options_perso']:
                    self._ajouter_ligne(fl, opt, 'perso')

            self.main_layout.addWidget(frame)
        self.main_layout.addStretch()

    def _ajouter_ligne(self, layout, opt, type_opt):
        row = QFrame()
        row.setStyleSheet(S.FRAME_OPTION)
        rl = QVBoxLayout()
        row.setLayout(rl)

        # Description de l'option
        if type_opt == 'standard':
            poids = opt.get('poids', 0)
            poids_txt = f" | {poids} kg" if poids else ""
            lbl = QLabel(f"• {opt['nom']} - Prix catalogue: {opt['prix']} €{poids_txt}")
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "Prix à définir"
            lbl = QLabel(f"• {opt['description']} - Demandé: {prix_txt}")
        lbl.setStyleSheet(S.LBL_OPTION)
        rl.addWidget(lbl)

        # Réponse acheteur existante
        sa = opt.get('statut_acheteur', 'en_attente')
        if sa and sa != 'en_attente':
            lbl_a = QLabel(f"↳ Réponse client: {sa.upper()} {opt.get('commentaire_acheteur', '')}")
            lbl_a.setStyleSheet(S.bold(get_statut_color(sa)))
            rl.addWidget(lbl_a)

        # Option finalisée par le client
        if sa == 'refuse':
            lbl_f = QLabel("→ Le client a refusé cette option. Décision FINALE (non modifiable)")
            lbl_f.setStyleSheet(S.bold_italic("#e74c3c"))
            rl.addWidget(lbl_f)
            self._options_finalisees.append({'type': type_opt, 'id': opt['id'], 'statut': 'refuse'})
            layout.addWidget(row)
            return

        if sa == 'accepte':
            lbl_f = QLabel("→ Le client a accepté cette option. Décision FINALE (non modifiable)")
            lbl_f.setStyleSheet(S.bold_italic("#27ae60"))
            rl.addWidget(lbl_f)
            self._options_finalisees.append({'type': type_opt, 'id': opt['id'], 'statut': 'accepte'})
            layout.addWidget(row)
            return

        # Champ de réponse vendeur
        resp = QHBoxLayout()
        resp.addWidget(QLabel("Ma réponse:"))

        combo = QComboBox()
        combo.addItems(["en_attente", "accepte", "refuse", "contre_proposition"])
        combo.setCurrentText(opt.get('statut_vendeur', 'en_attente'))
        resp.addWidget(combo)

        resp.addWidget(QLabel("Prix:"))
        spin_prix = QSpinBox()
        spin_prix.setMaximum(999999)
        spin_prix.setSuffix(" €")
        if type_opt == 'standard':
            spin_prix.setValue(int(opt['prix']))
        elif opt.get('prix_propose'):
            spin_prix.setValue(int(opt['prix_propose']))
        elif opt.get('prix_demande'):
            spin_prix.setValue(int(opt['prix_demande']))
        resp.addWidget(spin_prix)

        def update_prix(c=combo, sp=spin_prix):
            en_cp = c.currentText() == 'contre_proposition'
            sp.setEnabled(en_cp)
            sp.setStyleSheet(S.SPIN_ACTIVE if en_cp else S.SPIN_INACTIVE)

        combo.currentTextChanged.connect(update_prix)
        update_prix()

        spin_poids = None
        if type_opt == 'perso':
            resp.addWidget(QLabel("⚖️ Poids:"))
            spin_poids = QDoubleSpinBox()
            spin_poids.setMaximum(9999)
            spin_poids.setDecimals(1)
            spin_poids.setSuffix(" kg")
            if opt.get('poids'):
                spin_poids.setValue(float(opt['poids']))
            resp.addWidget(spin_poids)

        inp = QLineEdit()
        inp.setPlaceholderText("Commentaire...")
        if opt.get('commentaire_vendeur'):
            inp.setText(opt['commentaire_vendeur'])
        resp.addWidget(inp)

        rl.addLayout(resp)
        layout.addWidget(row)

        self._reponse_widgets.append({
            'type': type_opt, 'id': opt['id'],
            'combo': combo, 'spin_prix': spin_prix, 'input_comm': inp,
            'spin_poids': spin_poids,
        })

    def _tout_accepter(self):
        for r in self._reponse_widgets:
            r['combo'].setCurrentText('accepte')

    def _sauvegarder(self):
        reponses = []
        for r in self._reponse_widgets:
            statut = r['combo'].currentText()
            prix = r['spin_prix'].value() if statut == 'contre_proposition' and r['spin_prix'].value() > 0 else None
            poids = r['spin_poids'].value() if r['spin_poids'] else 0
            reponses.append({
                'type': r['type'], 'id': r['id'],
                'statut': statut, 'commentaire': r['input_comm'].text().strip(),
                'prix': prix, 'poids': poids,
            })

        new_id, new_version = self.controller.sauvegarder_reponses_vendeur(self.devis_id, reponses)
        if new_id:
            QMessageBox.information(self, "Succès",
                f"Réponses enregistrées.\nNouvelle version V{new_version} créée !")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de la création de la version.")
