# ──────────────────────────────────────────────────────────────────────────────
# vendeur_app.py — Application VENDEUR du Configurateur de Devis
# ──────────────────────────────────────────────────────────────────────────────
# Interface dédiée au vendeur. Permet de consulter les demandes de devis
# soumises par les clients, d'y répondre en acceptant, refusant ou faisant
# des contre-propositions sur chaque option, et de clôturer les affaires
# (gagnée, perdue, annulée). Contient la fenêtre principale VendeurWindow
# qui hérite de BaseAffaireWindow.
# ──────────────────────────────────────────────────────────────────────────────
import sys
import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidgetItem, QTabWidget,
                             QMessageBox)

from src.controllers.vendeur_controller import VendeurController
from src.models.db_manager import DatabaseManager
from src.views.base_window import BaseAffaireWindow
from src.views.vendeur_dialogs import ClotureAffaireDialog, ReponseVendeurDialog
from src.views.theme import S
from src.utils.session import sauvegarder_session, supprimer_session


class VendeurWindow(BaseAffaireWindow):
    """Fenêtre principale pour le VENDEUR."""

    ROLE = "vendeur"

    def __init__(self, controller, vendeur_info):
        super().__init__()
        self.controller = controller
        self.vendeur_info = vendeur_info
        self.AUTEUR = f"{vendeur_info['prenom']} {vendeur_info['nom']}"

        self.setWindowTitle("VENDEUR - Configurateur de Devis")
        self.setGeometry(600, 50, 1100, 750)
        self.current_affaire_numero = ""

        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout()
        central.setLayout(ml)

        # ─── Barre du haut : info compte + déconnexion ───────────
        top_bar = QHBoxLayout()

        header = QLabel("INTERFACE VENDEUR")
        header.setStyleSheet(S.HEADER_VENDEUR)
        top_bar.addWidget(header)

        top_bar.addStretch()

        info_lbl = QLabel(
            f"{vendeur_info['prenom']} {vendeur_info['nom']}")
        info_lbl.setStyleSheet("color: #b2bec3; font-size: 12px;")
        top_bar.addWidget(info_lbl)

        btn_logout = QPushButton("Déconnexion")
        btn_logout.setStyleSheet(
            "background-color: #636e72; color: white; padding: 6px 12px; border-radius: 4px;")
        btn_logout.clicked.connect(self._deconnexion)
        top_bar.addWidget(btn_logout)

        ml.addLayout(top_bar)

        self.tabs = QTabWidget()
        ml.addWidget(self.tabs)

        self.tabs.addTab(self._build_tab_affaires(), "Toutes les Affaires")
        self.tabs.addTab(self._build_tab_detail(), "Détail & Réponse")

        self.charger_affaires()
        self._start_auto_refresh()

    def _deconnexion(self):
        reply = QMessageBox.question(
            self, "Déconnexion",
            "Voulez-vous vous déconnecter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            supprimer_session("vendeur")
            QMessageBox.information(self, "Déconnexion", "Vous avez été déconnecté.")
            self.close()

    def _on_auto_refresh(self):
        self.charger_affaires()
        if self.current_affaire_id:
            self._charger_devis_affaire()

    # ─── Construction des onglets ─────────────────────────────────
    def _build_tab_affaires(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        layout.addWidget(QLabel("Liste des affaires clients:"))

        self.table_affaires = self._create_affaires_table(
            ["N° Affaire", "Client", "Titre", "Date", "Nb Devis"])
        layout.addWidget(self.table_affaires)

        btn = QPushButton("Ouvrir l'affaire")
        btn.setStyleSheet(S.BTN_DANGER + S.BTN_ACTION)
        btn.clicked.connect(self._ouvrir_affaire)
        layout.addWidget(btn)
        return tab

    def _build_tab_detail(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Header avec statut + clôture
        hl = QHBoxLayout()
        self.lbl_affaire = QLabel("Sélectionnez une affaire")
        self.lbl_affaire.setStyleSheet(S.TITLE_VENDEUR)
        hl.addWidget(self.lbl_affaire)
        hl.addStretch()
        self.lbl_statut = QLabel("")
        hl.addWidget(self.lbl_statut)
        self.btn_cloturer = QPushButton("Clôturer l'affaire")
        self.btn_cloturer.setStyleSheet(S.BTN_CLOTURE)
        self.btn_cloturer.clicked.connect(self._cloturer_affaire)
        hl.addWidget(self.btn_cloturer)
        layout.addLayout(hl)

        splitter, _ = self._build_detail_splitter([
            ("Voir détail", None, self._voir_detail),
            ("Répondre au client", S.BTN_DANGER, self._repondre_client),
            ("Générer PDF", S.BTN_PRIMARY, self._generer_pdf),
        ])
        layout.addWidget(splitter)
        return tab

    # ─── Hooks base class ─────────────────────────────────────────
    def _fill_extra_columns(self, row, aff):
        devis = self.controller.get_devis(aff[0])
        self.table_affaires.setItem(row, 4, QTableWidgetItem(str(len(devis))))

    def _on_affaire_opened(self, extras):
        self.current_affaire_numero = extras['numero']
        self.lbl_affaire.setText(
            f"{extras['numero']} - {self.current_affaire_client} - {extras['titre']}")
        self._update_statut_label(extras['statut'])

    # ─── Statut ───────────────────────────────────────────────────
    def _update_statut_label(self, statut):
        styles = {
            'en_cours': ('En cours', '#3498db'),
            'gagne': ('GAGNÉ', '#27ae60'),
            'perdu': ('PERDU', '#e74c3c'),
            'annule': ('Annulé', '#95a5a6'),
        }
        txt, color = styles.get(statut, ('En cours', '#3498db'))
        self.lbl_statut.setText(txt)
        self.lbl_statut.setStyleSheet(S.badge(color))

        if statut in ('gagne', 'perdu', 'annule'):
            self.btn_cloturer.setEnabled(False)
            self.btn_cloturer.setStyleSheet(S.BTN_DISABLED)
            self.btn_cloturer.setText("Affaire clôturée")
        else:
            self.btn_cloturer.setEnabled(True)
            self.btn_cloturer.setStyleSheet(S.BTN_CLOTURE)
            self.btn_cloturer.setText("Clôturer l'affaire")

    # ─── Actions ──────────────────────────────────────────────────
    def _cloturer_affaire(self):
        if not self.current_affaire_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez une affaire.")
            return
        est_cloturee, statut = self.controller.is_affaire_cloturee(self.current_affaire_id)
        if est_cloturee:
            QMessageBox.warning(self, "Affaire clôturée",
                f"Déjà clôturée ({statut.upper()}). Aucune modification possible.")
            return

        info = f"{self.current_affaire_numero} - {self.current_affaire_client}"
        dialog = ClotureAffaireDialog(info, self)
        if dialog.exec():
            data = dialog.get_data()
            result = self.controller.cloturer_affaire(
                self.current_affaire_id, data['resultat'], data['commentaire'])
            if result['success']:
                msg = f"Affaire clôturée: {data['resultat'].upper()}"
                if result.get('final_id'):
                    msg += f"\n\nDevis final: V{result['final_version']}"
                    QMessageBox.information(self, "Succès", msg)
                    from src.views.dialogs import DetailDevisDialog
                    DetailDevisDialog(self.controller, result['final_id'], self).exec()
                else:
                    QMessageBox.information(self, "Succès", msg)
                self._update_statut_label(data['resultat'])
                self.charger_affaires()
                self._charger_commentaires()

    def _repondre_client(self):
        devis_id = self._get_selected_devis_id()
        if not devis_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        if ReponseVendeurDialog(self.controller, devis_id, self).exec():
            self._charger_devis_affaire()


def main():
    from PyQt6.QtWidgets import QApplication
    from src.views.theme import create_dark_palette, get_stylesheet
    from src.views.auth_dialogs import ConnexionVendeurDialog
    from src.utils.session import charger_session, sauvegarder_session

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(create_dark_palette('red'))
    app.setStyleSheet(get_stylesheet('vendeur'))

    db = DatabaseManager()
    controller = VendeurController(db)

    # Tenter de restaurer la session précédente
    session = charger_session("vendeur")
    if session and session.get("vendeur_id"):
        info = controller.get_vendeur_par_id(session["vendeur_id"])
        if info:
            window = VendeurWindow(controller, info)
            window.show()
            return sys.exit(app.exec())

    # Pas de session valide → dialogue de connexion
    dialog = ConnexionVendeurDialog(controller)
    if not dialog.exec():
        sys.exit(0)

    # Sauvegarder la session
    sauvegarder_session("vendeur", {"vendeur_id": dialog.vendeur_info["id"]})

    window = VendeurWindow(controller, dialog.vendeur_info)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
