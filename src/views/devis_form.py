# ──────────────────────────────────────────────────────────────────────────────
# src/views/devis_form.py — Formulaire de création de devis
# ──────────────────────────────────────────────────────────────────────────────
# Widget intégré dans l'onglet « Nouveau Devis » de l'interface client.
# Permet d'ajouter plusieurs produits configurables (via ProduitConfigWidget),
# d'afficher le total estimé en temps réel, de saisir un commentaire
# destiné au vendeur et de soumettre la demande de devis.
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                             QScrollArea, QTextEdit, QGroupBox)

from src.views.widgets import ProduitConfigWidget
from src.views.theme import S


class DevisFormWidget(QWidget):
    """Encapsule la liste de produits, le total, le commentaire et le bouton soumettre."""

    def __init__(self, controller, on_submit):
        super().__init__()
        self.controller = controller
        self._on_submit = on_submit
        self._produit_widgets = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.lbl_ref = QLabel("Affaire: Aucune sélectionnée")
        self.lbl_ref.setStyleSheet(S.LBL_MUTED)
        layout.addWidget(self.lbl_ref)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._products_layout = QVBoxLayout()
        self._container.setLayout(self._products_layout)
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

        btn_add = QPushButton("➕ Ajouter un Produit")
        btn_add.setStyleSheet(S.BTN_ACCENT + S.BTN_ACTION)
        btn_add.clicked.connect(self._ajouter_produit)
        layout.addWidget(btn_add)

        self.lbl_total = QLabel("TOTAL: 0.00 €")
        self.lbl_total.setStyleSheet(S.LBL_TOTAL)
        layout.addWidget(self.lbl_total)

        group = QGroupBox("💬 Commentaire / Notes pour le vendeur")
        gl = QVBoxLayout()
        group.setLayout(gl)
        self.input_commentaire = QTextEdit()
        self.input_commentaire.setPlaceholderText(
            "Ajoutez vos remarques, contraintes particulières, délais souhaités, questions...")
        self.input_commentaire.setMaximumHeight(100)
        gl.addWidget(self.input_commentaire)
        layout.addWidget(group)

        btn_submit = QPushButton("📤 Soumettre le devis")
        btn_submit.setStyleSheet(S.BTN_SUBMIT)
        btn_submit.clicked.connect(self._soumettre)
        layout.addWidget(btn_submit)

    # ─── Produits ─────────────────────────────────────────────────
    def _ajouter_produit(self):
        w = ProduitConfigWidget(self.controller, len(self._produit_widgets),
                                self._recalculer_total, self._supprimer_produit)
        self._produit_widgets.append(w)
        self._products_layout.addWidget(w)
        self._recalculer_total()

    def _supprimer_produit(self, widget):
        self._produit_widgets.remove(widget)
        widget.deleteLater()
        for i, w in enumerate(self._produit_widgets):
            w.index = i
            w.lbl_title.setText(f"🔷 Produit #{i + 1}")
        self._recalculer_total()

    def _recalculer_total(self):
        total = sum(w.calculer_sous_total() for w in self._produit_widgets)
        self.lbl_total.setText(f"TOTAL: {total:.2f} €")

    # ─── Collecte & soumission ────────────────────────────────────
    def get_produits_data(self):
        """Retourne la liste de tuples prêts pour le controller, ou None si vide."""
        result = []
        for w in self._produit_widgets:
            data = w.get_data()
            if data:
                result.append((data['produit_id'], data['quantite'], data['prix'],
                               data['options_ids'], data['options_perso']))
        return result or None

    def get_commentaire(self):
        return self.input_commentaire.toPlainText().strip()

    def get_produit_widgets(self):
        return list(self._produit_widgets)

    def _soumettre(self):
        self._on_submit()

    def reset(self):
        """Vide le formulaire après soumission réussie."""
        for w in self._produit_widgets[:]:
            self._supprimer_produit(w)
        self.input_commentaire.clear()
