# ──────────────────────────────────────────────────────────────────────────────
# src/views/client_dialogs.py — Dialogues de l'interface CLIENT
# ──────────────────────────────────────────────────────────────────────────────
# Contient les boîtes de dialogue propres à l'acheteur : NouvelleAffaireDialog
# pour créer une affaire avec sélection ou création de client, et
# ReponseAcheteurDialog pour répondre aux contre-propositions du vendeur
# sur chaque option (accepter, refuser, contre-proposer à nouveau).
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QWidget, QFrame, QComboBox, QLineEdit,
                             QGroupBox, QMessageBox, QFormLayout, QDialogButtonBox,
                             QTextEdit)
from src.views.theme import S
from src.constants import STATUT_CLOTURE_LABELS, get_statut_color


class NouvelleAffaireDialog(QDialog):
    """Formulaire de création d'une nouvelle affaire (projet uniquement,
    le client est déjà identifié via l'inscription)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle Affaire")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Projet ---
        group_projet = QGroupBox("Projet")
        form_p = QFormLayout()
        group_projet.setLayout(form_p)
        self.input_titre = QLineEdit()
        self.input_titre.setPlaceholderText("Titre du projet")
        form_p.addRow("Projet:", self.input_titre)
        self.input_description = QTextEdit()
        self.input_description.setPlaceholderText("Description du besoin...")
        self.input_description.setMaximumHeight(100)
        form_p.addRow("Description:", self.input_description)
        layout.addWidget(group_projet)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            'titre': self.input_titre.text().strip(),
            'description': self.input_description.toPlainText().strip(),
        }


class ReponseAcheteurDialog(QDialog):
    """Dialog pour que l'acheteur réponde aux propositions du vendeur.
    Reçoit le controller pour la logique métier (sauvegarde, conclusion)."""

    def __init__(self, controller, devis_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.devis_id = devis_id
        self._reponse_widgets = []
        self._auto_adoptes = []

        self.setWindowTitle("Répondre aux propositions du vendeur")
        self.setMinimumSize(850, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        devis_info = self.controller.get_devis_info(devis_id)
        affaire_id = devis_info[1] if devis_info else None
        self.affaire_cloturee, self.statut_cloture = (
            self.controller.is_affaire_cloturee(affaire_id) if affaire_id else (False, None))

        lbl = QLabel("Accepter ou refuser les propositions du vendeur")
        lbl.setStyleSheet(S.TITLE_CLIENT)
        layout.addWidget(lbl)

        if self.affaire_cloturee:
            txt = STATUT_CLOTURE_LABELS.get(self.statut_cloture, self.statut_cloture)
            lbl_c = QLabel(f"Affaire clôturée ({txt}). Aucune modification possible.")
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
        btn_all = QPushButton("Tout accepter")
        btn_all.setStyleSheet(S.BTN_SUCCESS + S.BTN_ACTION)
        btn_all.clicked.connect(self._tout_accepter)
        btns.addWidget(btn_all)

        btn_save = QPushButton("Valider et créer nouvelle version")
        btn_save.setStyleSheet(S.BTN_PRIMARY + S.BTN_ACTION)
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
        has_vendeur_response = False

        for prod in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet(S.FRAME_DARK)
            fl = QVBoxLayout()
            frame.setLayout(fl)

            lbl_p = QLabel(f"Produit: {prod['nom']} x{prod['quantite']}")
            lbl_p.setStyleSheet(S.LBL_PRODUCT)
            fl.addWidget(lbl_p)

            for opt in prod['options_standard']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    has_vendeur_response = True
                    self._ajouter_ligne(fl, opt, 'standard')

            for opt in prod['options_perso']:
                if opt.get('statut_vendeur') and opt['statut_vendeur'] != 'en_attente':
                    has_vendeur_response = True
                    self._ajouter_ligne(fl, opt, 'perso')

            self.main_layout.addWidget(frame)

        if not has_vendeur_response:
            lbl = QLabel("Le vendeur n'a pas encore répondu à ce devis.")
            lbl.setStyleSheet(S.LBL_WARNING)
            self.main_layout.addWidget(lbl)

        self.main_layout.addStretch()

    def _ajouter_ligne(self, layout, opt, type_opt):
        row = QFrame()
        row.setStyleSheet(S.FRAME_OPTION)
        rl = QVBoxLayout()
        row.setLayout(rl)

        if type_opt == 'standard':
            nom = f"[Catalogue] {opt['nom']} - Prix catalogue: {opt['prix']} €"
        else:
            prix_txt = f"{opt['prix_demande']} €" if opt['prix_demande'] else "À définir"
            nom = f"[Perso] {opt['description']} - Demandé: {prix_txt}"
        lbl_nom = QLabel(nom)
        lbl_nom.setStyleSheet(S.LBL_OPTION)
        rl.addWidget(lbl_nom)

        # Réponse vendeur
        sv = opt.get('statut_vendeur', 'en_attente')
        vl = QHBoxLayout()
        lbl_v = QLabel(f"↳ Vendeur: {sv.upper()}")
        lbl_v.setStyleSheet(S.bold(get_statut_color(sv)))
        vl.addWidget(lbl_v)
        if opt.get('prix_propose'):
            vl.addWidget(QLabel(f"Prix proposé: {opt['prix_propose']} €"))
        poids_v = opt.get('poids', 0) if type_opt == 'perso' else None
        if poids_v and poids_v > 0:
            vl.addWidget(QLabel(f"Poids: {poids_v} kg"))
        if opt.get('commentaire_vendeur'):
            vl.addWidget(QLabel(f'"{opt["commentaire_vendeur"]}"'))
        vl.addStretch()
        rl.addLayout(vl)

        if sv == 'contre_proposition':
            # Réponse acheteur modifiable
            resp = QHBoxLayout()
            resp.addWidget(QLabel("Ma réponse:"))
            combo = QComboBox()
            combo.addItems(["en_attente", "accepte", "refuse"])
            combo.setCurrentText(opt.get('statut_acheteur', 'en_attente'))
            resp.addWidget(combo)
            inp = QLineEdit()
            inp.setPlaceholderText("Commentaire...")
            if opt.get('commentaire_acheteur'):
                inp.setText(opt['commentaire_acheteur'])
            resp.addWidget(inp)
            resp.addStretch()
            rl.addLayout(resp)
            self._reponse_widgets.append({
                'type': type_opt, 'id': opt['id'], 'combo': combo, 'input_comm': inp,
            })
        else:
            # Décision non modifiable
            statut_txt = "ADOPTÉ" if sv == 'accepte' else "REFUSÉ"
            color = "#27ae60" if sv == 'accepte' else "#e74c3c"
            lbl_f = QLabel(f"Décision vendeur: {statut_txt} (non modifiable)")
            lbl_f.setStyleSheet(S.italic(color))
            rl.addWidget(lbl_f)
            self._auto_adoptes.append({'type': type_opt, 'id': opt['id']})

        layout.addWidget(row)

    def _tout_accepter(self):
        for r in self._reponse_widgets:
            r['combo'].setCurrentText('accepte')

    def _sauvegarder(self):
        reponses = [
            {'type': r['type'], 'id': r['id'],
             'statut': r['combo'].currentText(),
             'commentaire': r['input_comm'].text().strip()}
            for r in self._reponse_widgets
        ]
        auto = [{'type': a['type'], 'id': a['id']} for a in self._auto_adoptes]

        result = self.controller.sauvegarder_reponses_acheteur(self.devis_id, reponses, auto)

        if result.get('concluded'):
            msg = (f"Toutes les options ont été traitées.\n"
                   f"L'affaire a été clôturée avec succès !\n\n"
                   f"Devis final: V{result.get('final_version')}\n\nMerci pour votre confiance.")
            QMessageBox.information(self, "Affaire Conclue", msg)
            fid = result.get('final_id')
            if fid:
                from src.views.dialogs import DetailDevisDialog
                DetailDevisDialog(self.controller, fid, self).exec()
            self.accept()
        elif result.get('new_id'):
            QMessageBox.information(self, "Succès",
                f"Vos réponses ont été enregistrées.\nNouvelle version V{result['new_version']} créée !")
            self.accept()
        else:
            QMessageBox.warning(self, "Erreur", "Erreur lors de la création de la nouvelle version.")
