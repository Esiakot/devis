# ──────────────────────────────────────────────────────────────────────────────
# src/views/base_window.py — Fenêtre de base partagée
# ──────────────────────────────────────────────────────────────────────────────
# Classe abstraite BaseAffaireWindow dont héritent ClientWindow et VendeurWindow.
# Implémente la logique d'affichage commune : table des affaires, table des
# devis, zone de commentaires, boutons de détail/PDF, rafraîchissement
# automatique. Les vues n'accèdent aux données que via self.controller (MVC).
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QPushButton, QTextEdit, QLineEdit,
                             QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QTimer

from src.constants import AUTO_REFRESH_MS, ROLE_COLORS


class BaseAffaireWindow(QMainWindow):
    """Fournit la logique partagée : affaires, devis, commentaires, PDF, détail.

    IMPORTANT : les vues n'accèdent aux données QUE via self.controller (MVC).
    """

    ROLE = ""       # 'acheteur' ou 'vendeur'
    AUTEUR = ""     # 'Client' ou 'Vendeur'

    def __init__(self):
        super().__init__()
        self.controller = None          # Initialisé par la sous-classe
        self.current_affaire_id = None
        self.current_affaire_client = ""

        self.tabs = None
        self.table_affaires = None
        self.table_devis = None
        self.txt_commentaires = None
        self.input_commentaire = None

    def _start_auto_refresh(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_auto_refresh)
        self.timer.start(AUTO_REFRESH_MS)

    def _on_auto_refresh(self):
        """Override dans la sous-classe."""

    # ─── Table affaires ───────────────────────────────────────────
    def _create_affaires_table(self, columns):
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.doubleClicked.connect(self._ouvrir_affaire)
        return table

    def charger_affaires(self):
        affaires = self.controller.get_affaires()
        self.table_affaires.setRowCount(len(affaires))
        for row, aff in enumerate(affaires):
            item = QTableWidgetItem(aff[1])
            item.setData(Qt.ItemDataRole.UserRole, aff[0])
            self.table_affaires.setItem(row, 0, item)
            self.table_affaires.setItem(row, 1, QTableWidgetItem(aff[2] or ""))
            self.table_affaires.setItem(row, 2, QTableWidgetItem(aff[3] or ""))
            self.table_affaires.setItem(row, 3, QTableWidgetItem(aff[4] or ""))
            self._fill_extra_columns(row, aff)

    def _fill_extra_columns(self, row, aff):
        """Hook — vendeur ajoute la colonne Nb Devis."""

    def _ouvrir_affaire(self):
        selected = self.table_affaires.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        self.current_affaire_id = self.table_affaires.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.current_affaire_client = self.table_affaires.item(row, 1).text()
        extras = {
            'numero': self.table_affaires.item(row, 0).text(),
            'titre': self.table_affaires.item(row, 2).text(),
            'statut': self.table_affaires.item(row, 3).text(),
        }
        self._on_affaire_opened(extras)
        self._charger_devis_affaire()
        self._charger_commentaires()
        self.tabs.setCurrentIndex(1)

    def _on_affaire_opened(self, extras):
        """Hook pour mise à jour des labels dans la sous-classe."""

    # ─── Splitter détail (devis table + commentaires) ─────────────
    def _build_detail_splitter(self, action_buttons):
        """Construit le splitter standard : devis table + boutons | commentaires.
        action_buttons: list of (text, style_or_None, callback)
        Retourne (splitter, left_layout).
        """
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Gauche : devis
        left = QWidget()
        ll = QVBoxLayout()
        left.setLayout(ll)
        ll.addWidget(QLabel("📄 Versions du devis:"))

        self.table_devis = QTableWidget()
        self.table_devis.setColumnCount(3)
        self.table_devis.setHorizontalHeaderLabels(["Version", "Date", "Total"])
        self.table_devis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_devis.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        ll.addWidget(self.table_devis)

        btns = QHBoxLayout()
        for text, style, callback in action_buttons:
            btn = QPushButton(text)
            if style:
                btn.setStyleSheet(style)
            btn.clicked.connect(callback)
            btns.addWidget(btn)
        ll.addLayout(btns)
        splitter.addWidget(left)

        # Droite : commentaires
        peer = "vendeur" if self.ROLE == "acheteur" else "client"
        right = QWidget()
        rl = QVBoxLayout()
        right.setLayout(rl)
        rl.addWidget(QLabel(f"💬 Échanges avec le {peer}:"))
        self.txt_commentaires = QTextEdit()
        self.txt_commentaires.setReadOnly(True)
        rl.addWidget(self.txt_commentaires)
        self.input_commentaire = QLineEdit()
        self.input_commentaire.setPlaceholderText("Écrire un message...")
        rl.addWidget(self.input_commentaire)
        btn_send = QPushButton("📤 Envoyer")
        btn_send.clicked.connect(self._envoyer_commentaire)
        rl.addWidget(btn_send)
        splitter.addWidget(right)

        return splitter, ll

    # ─── Helpers ──────────────────────────────────────────────────
    def _get_selected_devis_id(self):
        selected = self.table_devis.selectedItems()
        if not selected:
            return None
        return self.table_devis.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    # ─── Chargement devis ─────────────────────────────────────────
    def _charger_devis_affaire(self):
        if not self.current_affaire_id:
            return
        devis = self.controller.get_devis(self.current_affaire_id)
        self.table_devis.setRowCount(len(devis))
        for row, d in enumerate(devis):
            item = QTableWidgetItem(f"V{d[1]}")
            item.setData(Qt.ItemDataRole.UserRole, d[0])
            self.table_devis.setItem(row, 0, item)
            self.table_devis.setItem(row, 1, QTableWidgetItem(d[2] or ""))
            self.table_devis.setItem(row, 2, QTableWidgetItem(f"{d[3]} €" if d[3] else "-"))

    # ─── Commentaires ─────────────────────────────────────────────
    def _charger_commentaires(self):
        if not self.current_affaire_id:
            return
        comments = self.controller.get_commentaires(self.current_affaire_id)
        html = ""
        for c in comments:
            role = c[2]
            color = ROLE_COLORS.get(role, '#95a5a6')
            html += f"<p style='color:{color};'><b>[{role.upper()}] {c[1]}</b> - {c[4]}<br/>{c[3]}</p>"
        self.txt_commentaires.setHtml(html)

    def _envoyer_commentaire(self):
        if not self.current_affaire_id or not self.input_commentaire.text().strip():
            return
        self.controller.envoyer_commentaire(
            self.current_affaire_id, self.AUTEUR, self.ROLE,
            self.input_commentaire.text().strip())
        self.input_commentaire.clear()
        self._charger_commentaires()

    # ─── Voir détail ──────────────────────────────────────────────
    def _voir_detail(self):
        from src.views.dialogs import DetailDevisDialog
        devis_id = self._get_selected_devis_id()
        if not devis_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        DetailDevisDialog(self.controller, devis_id, self).exec()

    # ─── Générer PDF ──────────────────────────────────────────────
    def _generer_pdf(self):
        devis_id = self._get_selected_devis_id()
        if not devis_id:
            QMessageBox.warning(self, "Attention", "Sélectionnez un devis.")
            return
        filepath = self.controller.generer_pdf(devis_id, self.current_affaire_client)
        if filepath:
            QMessageBox.information(self, "PDF Généré", f"PDF sauvegardé:\n{filepath}")
