# ──────────────────────────────────────────────────────────────────────────────
# client_app.py — Application CLIENT du Configurateur de Devis
# ──────────────────────────────────────────────────────────────────────────────
# Interface dédiée à l'acheteur. Permet de créer de nouvelles affaires, de
# composer des demandes de devis en configurant des produits et leurs options,
# de suivre l'avancement des négociations avec le vendeur (versions successives),
# et de répondre aux contre-propositions. Contient la fenêtre principale
# ClientWindow qui hérite de BaseAffaireWindow.
# ──────────────────────────────────────────────────────────────────────────────
import sys
import os

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt

from src.controllers.client_controller import ClientController
from src.models.db_manager import DatabaseManager
from src.views.base_window import BaseAffaireWindow
from src.views.client_dialogs import NouvelleAffaireDialog, ReponseAcheteurDialog
from src.views.devis_form import DevisFormWidget
from src.views.theme import S
from src.utils.session import sauvegarder_session, supprimer_session


class ClientWindow(BaseAffaireWindow):
    """Fenêtre principale pour le CLIENT."""

    ROLE = "acheteur"

    def __init__(self, controller, client_info):
        super().__init__()
        self.controller = controller
        self.client_id = controller.client_id
        self.client_info = client_info
        self.AUTEUR = f"{client_info['prenom']} {client_info['nom']}"

        self.setWindowTitle("CLIENT - Configurateur de Devis")
        self.setGeometry(50, 50, 1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        ml = QVBoxLayout()
        central.setLayout(ml)

        # ─── Barre du haut : info compte + déconnexion ───────────
        top_bar = QHBoxLayout()

        header = QLabel("INTERFACE CLIENT")
        header.setStyleSheet(S.HEADER_CLIENT)
        top_bar.addWidget(header)

        top_bar.addStretch()

        info_lbl = QLabel(
            f"{client_info['prenom']} {client_info['nom']}  |  "
            f"{client_info.get('societe', '')}  |  "
            f"SIRET: {client_info.get('siret', '')}")
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

        self.devis_form = DevisFormWidget(self.controller, self._soumettre_devis)

        self.tabs.addTab(self._build_tab_affaires(), "Mes Affaires")
        self.tabs.addTab(self._build_tab_detail(), "Détail Affaire")
        self.tabs.addTab(self.devis_form, "Nouveau Devis")

        self.charger_affaires()
        self._start_auto_refresh()

    def _deconnexion(self):
        reply = QMessageBox.question(
            self, "Déconnexion",
            "Voulez-vous vous déconnecter ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            supprimer_session("client")
            QMessageBox.information(self, "Déconnexion", "Vous avez été déconnecté.")
            self.close()

    def _on_auto_refresh(self):
        if self.current_affaire_id:
            self._charger_devis_affaire()

    # ─── Construction des onglets ─────────────────────────────────
    def _build_tab_affaires(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        btn_new = QPushButton("Nouvelle Affaire")
        btn_new.setStyleSheet(S.BTN_HIGHLIGHT)
        btn_new.clicked.connect(self._nouvelle_affaire)
        layout.addWidget(btn_new)

        self.table_affaires = self._create_affaires_table(
            ["N° Affaire", "Client", "Titre", "Date"])
        layout.addWidget(self.table_affaires)

        btn_open = QPushButton("Ouvrir l'affaire sélectionnée")
        btn_open.clicked.connect(self._ouvrir_affaire)
        layout.addWidget(btn_open)
        return tab

    def _build_tab_detail(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        self.lbl_affaire_titre = QLabel("Sélectionnez une affaire")
        self.lbl_affaire_titre.setStyleSheet(S.TITLE)
        layout.addWidget(self.lbl_affaire_titre)

        splitter, left_layout = self._build_detail_splitter([
            ("Voir détail", None, self._voir_detail),
            ("Répondre au vendeur", S.BTN_SUCCESS, self._repondre_vendeur),
            ("Générer PDF", S.BTN_PRIMARY, self._generer_pdf),
        ])
        btn_nouveau = QPushButton("Nouveau devis")
        btn_nouveau.setStyleSheet(S.BTN_ACCENT)
        btn_nouveau.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        left_layout.addWidget(btn_nouveau)

        layout.addWidget(splitter)
        return tab

    # ─── Hooks base class ─────────────────────────────────────────
    def _on_affaire_opened(self, extras):
        self.lbl_affaire_titre.setText(f"{extras['numero']} - {extras['titre']}")
        self.devis_form.lbl_ref.setText(f"Affaire: {extras['numero']}")

    # ─── Actions ──────────────────────────────────────────────────
    def _nouvelle_affaire(self):
        dialog = NouvelleAffaireDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            data['client_id'] = self.client_id
            affaire_id, numero, error = self.controller.creer_affaire(data)
            if error:
                QMessageBox.warning(self, "Erreur", error)
            elif affaire_id:
                QMessageBox.information(self, "Succès", f"Affaire {numero} créée !")
                self.charger_affaires()

    def _repondre_vendeur(self):
        devis_id = self._get_selected_devis_id()
        if not devis_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        if ReponseAcheteurDialog(self.controller, devis_id, self).exec():
            self._charger_devis_affaire()

    def _soumettre_devis(self):
        result = self.controller.valider_et_soumettre(
            self.current_affaire_id,
            self.devis_form.get_produit_widgets(),
            self.devis_form.get_produits_data(),
            self.devis_form.get_commentaire())

        if result['error']:
            QMessageBox.warning(self, "Erreur", result['error'])
            return

        QMessageBox.information(self, "Succès", f"Devis V{result['version']} soumis !")
        self._charger_devis_affaire()
        self.devis_form.reset()
        self.tabs.setCurrentIndex(1)


def main():
    from PyQt6.QtWidgets import QApplication
    from src.views.theme import create_dark_palette, get_stylesheet
    from src.views.auth_dialogs import InscriptionClientDialog
    from src.utils.session import charger_session, sauvegarder_session

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(create_dark_palette('blue'))
    app.setStyleSheet(get_stylesheet('client'))

    db = DatabaseManager()
    controller = ClientController(db)

    # Tenter de restaurer la session précédente
    session = charger_session("client")
    if session and session.get("client_id"):
        info = controller.get_client_par_id(session["client_id"])
        if info:
            controller.client_id = info["id"]
            client_info = {
                "nom": info["nom"], "prenom": info["prenom"],
                "service": info["service"], "societe": info["nom_societe"],
                "siret": info["siret"],
            }
            window = ClientWindow(controller, client_info)
            window.show()
            return sys.exit(app.exec())

    # Pas de session valide → dialogue de connexion
    dialog = InscriptionClientDialog(controller)
    if not dialog.exec():
        sys.exit(0)

    controller.client_id = dialog.client_id

    # Sauvegarder la session
    sauvegarder_session("client", {"client_id": dialog.client_id})

    window = ClientWindow(controller, dialog.client_info)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
