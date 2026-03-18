# ──────────────────────────────────────────────────────────────────────────────
# src/views/dialogs.py — Dialogues partagés client / vendeur
# ──────────────────────────────────────────────────────────────────────────────
# Contient les boîtes de dialogue utilisées par les deux interfaces.
# Notamment DetailDevisDialog qui affiche le détail complet d'un devis
# (produits, options standard et personnalisées, statuts avec indicateurs
# colorés, prix, commentaires) dans une fenêtre scrollable.
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QScrollArea, QWidget, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt6.QtGui import QColor
from src.constants import STATUT_COLORS, get_statut_emoji, get_statut_color
from src.views.theme import S


class DetailDevisDialog(QDialog):
    """Dialog pour voir le détail d'un devis (partagé client/vendeur)."""

    def __init__(self, controller, devis_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.devis_id = devis_id

        info = self.controller.get_devis_info(devis_id)
        version = info[2] if info else "?"
        numero = info[5] if info else "?"

        self.setWindowTitle(f"📋 Détail - {numero}-{version}")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl = QLabel(f"📋 Devis {numero} - Version {version}")
        lbl.setStyleSheet(S.TITLE)
        layout.addWidget(lbl)

        # Légende
        legende = QHBoxLayout()
        for txt, color in [("En attente", STATUT_COLORS['en_attente']),
                           ("Accepté", STATUT_COLORS['accepte']),
                           ("Refusé", STATUT_COLORS['refuse']),
                           ("Contre-proposition", STATUT_COLORS['contre_proposition'])]:
            l = QLabel(f"● {txt}")
            l.setStyleSheet(S.bold(color))
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

        btn_close = QPushButton("Fermer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def charger_detail(self):
        data = self.controller.get_devis_detail(self.devis_id)

        for prod_data in data['produits']:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame.setStyleSheet(S.FRAME_DARK)
            frame_layout = QVBoxLayout()
            frame.setLayout(frame_layout)

            lbl = QLabel(f"🔷 {prod_data['nom']} x{prod_data['quantite']} - {prod_data['prix_unitaire']} €/u")
            lbl.setStyleSheet(S.LBL_PRODUCT)
            frame_layout.addWidget(lbl)

            if prod_data['options_standard'] or prod_data['options_perso']:
                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels(["Option", "Prix", "Vendeur", "Client", "Commentaires"])
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

                all_opts = ([('std', o) for o in prod_data['options_standard']]
                            + [('perso', o) for o in prod_data['options_perso']])
                table.setRowCount(len(all_opts))

                for row, (t, opt) in enumerate(all_opts):
                    nom = opt['nom'] if t == 'std' else f"🔧 {opt['description']}"
                    prix = f"{opt['prix']} €" if t == 'std' else f"{opt.get('prix_demande', '-')} €"

                    table.setItem(row, 0, QTableWidgetItem(nom))
                    table.setItem(row, 1, QTableWidgetItem(prix))

                    sv = opt.get('statut_vendeur') or 'en_attente'
                    iv = QTableWidgetItem(f"{get_statut_emoji(sv)} {sv}")
                    iv.setForeground(QColor(get_statut_color(sv)))
                    table.setItem(row, 2, iv)

                    sa = opt.get('statut_acheteur') or 'en_attente'
                    ia = QTableWidgetItem(f"{get_statut_emoji(sa)} {sa}")
                    ia.setForeground(QColor(get_statut_color(sa)))
                    table.setItem(row, 3, ia)

                    comm = f"[V]{opt.get('commentaire_vendeur', '')} [A]{opt.get('commentaire_acheteur', '')}"
                    table.setItem(row, 4, QTableWidgetItem(comm.strip()))

                frame_layout.addWidget(table)

            self.main_layout.addWidget(frame)
        self.main_layout.addStretch()
