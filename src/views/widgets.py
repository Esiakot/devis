# ──────────────────────────────────────────────────────────────────────────────
# src/views/widgets.py — Widgets réutilisables
# ──────────────────────────────────────────────────────────────────────────────
# Contient les composants d'interface partagés. ProduitConfigWidget est le
# widget principal : il permet de sélectionner un modèle de produit, d'en
# choisir la quantité, de cocher des options standard, d'ajouter des options
# personnalisées, et d'afficher une barre de poids avec contrôle de la
# charge maximale. Utilisé dans le formulaire de devis côté client.
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
                             QLineEdit, QProgressBar)
from src.constants import POIDS_LIMITE_POURCENTAGE
from src.views.theme import S


class ProduitConfigWidget(QFrame):
    """Widget pour configurer un produit avec ses options."""

    def __init__(self, controller, index, on_change_callback, on_remove_callback):
        super().__init__()
        self.controller = controller
        self.index = index
        self.on_change = on_change_callback
        self.on_remove = on_remove_callback
        self.checkboxes = []
        self.options_perso_widgets = []

        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet(S.WIDGET_PRODUCT)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QHBoxLayout()
        self.lbl_title = QLabel(f"Produit #{index + 1}")
        self.lbl_title.setStyleSheet(S.LBL_BOLD_BLUE)
        header.addWidget(self.lbl_title)
        header.addStretch()

        self.btn_remove = QPushButton("X")
        self.btn_remove.setFixedSize(30, 30)
        self.btn_remove.setStyleSheet(S.BTN_REMOVE)
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
        self.lbl_poids = QLabel("Charge: 0 / 0 kg (0%)")
        self.lbl_poids.setStyleSheet(S.LBL_BOLD)
        poids_header.addWidget(self.lbl_poids)
        poids_header.addStretch()
        self.lbl_poids_warning = QLabel("")
        poids_header.addWidget(self.lbl_poids_warning)
        poids_layout.addLayout(poids_header)

        self.progress_poids = QProgressBar()
        self.progress_poids.setMaximum(100)
        self.progress_poids.setValue(0)
        self.progress_poids.setStyleSheet(S.PROGRESS_OK)
        poids_layout.addWidget(self.progress_poids)
        layout.addLayout(poids_layout)

        # Options standard
        self.group_options = QGroupBox("Options catalogue")
        self.layout_options = QVBoxLayout()
        self.group_options.setLayout(self.layout_options)
        layout.addWidget(self.group_options)

        # Options personnalisées
        self.group_options_perso = QGroupBox("Options personnalisées (demandes spéciales)")
        self.layout_options_perso = QVBoxLayout()
        self.group_options_perso.setLayout(self.layout_options_perso)

        btn_add_perso = QPushButton("Ajouter une demande spéciale")
        btn_add_perso.setStyleSheet(S.BTN_ADD_PERSO)
        btn_add_perso.clicked.connect(self.ajouter_option_perso)
        self.layout_options_perso.addWidget(btn_add_perso)
        layout.addWidget(self.group_options_perso)

        # Sous-total
        self.lbl_subtotal = QLabel("Sous-total: 0.00 €")
        self.lbl_subtotal.setStyleSheet(S.LBL_SUBTOTAL)
        layout.addWidget(self.lbl_subtotal)

        self.charger_modeles()

    def on_modele_change(self):
        prod_data = self.combo_modele.currentData()
        if prod_data:
            self.charger_options_pour_produit(prod_data[0])
        self.update_options_disponibles()
        self.on_change()

    def update_options_disponibles(self):
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return

        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite = charge_max * POIDS_LIMITE_POURCENTAGE
        poids_actuel = self.calculer_poids_total()

        for cb in self.checkboxes:
            opt = cb.property("option_data")
            opt_poids = opt[3] if len(opt) > 3 and opt[3] else 0

            if not cb.isChecked():
                if poids_actuel + opt_poids > limite:
                    cb.setEnabled(False)
                    cb.setStyleSheet(S.CB_UNAVAILABLE)
                else:
                    cb.setEnabled(True)
                    cb.setStyleSheet(S.CB_AVAILABLE)
            else:
                cb.setEnabled(True)
                cb.setStyleSheet(S.CB_AVAILABLE)

    def ajouter_option_perso(self):
        frame = QFrame()
        frame.setStyleSheet(S.FRAME_PERSO)
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

        btn_del = QPushButton("X")
        btn_del.setFixedSize(30, 30)
        btn_del.clicked.connect(lambda: self.supprimer_option_perso(frame))
        row.addWidget(btn_del)

        self.layout_options_perso.insertWidget(self.layout_options_perso.count() - 1, frame)
        self.options_perso_widgets.append((frame, input_desc, spin_prix))
        self.on_change()

    def supprimer_option_perso(self, frame):
        for i, item in enumerate(self.options_perso_widgets):
            if item[0] == frame:
                self.options_perso_widgets.pop(i)
                break
        frame.deleteLater()
        self.on_change()

    def charger_modeles(self):
        self.combo_modele.clear()
        produits = self.controller.get_produits()
        for p in produits:
            charge_max = p[3] if len(p) > 3 and p[3] else 0
            self.combo_modele.addItem(f"{p[1]} - {p[2]}€ (charge max: {charge_max}kg)", p)
        if produits:
            self.charger_options_pour_produit(produits[0][0])

    def charger_options_pour_produit(self, produit_id):
        for cb in self.checkboxes:
            cb.deleteLater()
        self.checkboxes.clear()

        options = self.controller.get_options_pour_produit(produit_id)
        for opt in options:
            poids = opt[3] if len(opt) > 3 and opt[3] else 0
            universelle = opt[4] if len(opt) > 4 else 0
            poids_txt = f" | {poids}kg" if poids > 0 else ""
            prefix = "[Univ.] " if universelle else ""
            cb = QCheckBox(f"{prefix}{opt[1]} (+{opt[2]}€{poids_txt})")
            cb.setProperty("option_data", opt)
            cb.stateChanged.connect(self.on_option_change)
            self.layout_options.addWidget(cb)
            self.checkboxes.append(cb)

    def on_option_change(self):
        self.update_options_disponibles()
        self.on_change()

    def get_data(self):
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
        poids = 0
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
        self.update_poids_display()
        return total

    def update_poids_display(self):
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return

        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite = charge_max * POIDS_LIMITE_POURCENTAGE
        poids_actuel = self.calculer_poids_total()
        pourcentage = (poids_actuel / charge_max * 100) if charge_max > 0 else 0

        self.lbl_poids.setText(f"Charge: {poids_actuel:.1f} / {limite:.1f} kg ({pourcentage:.0f}%)")
        self.progress_poids.setValue(min(int(pourcentage), 100))

        pct_limit = POIDS_LIMITE_POURCENTAGE * 100
        if pourcentage > pct_limit:
            self.progress_poids.setStyleSheet(S.PROGRESS_DANGER)
            self.lbl_poids_warning.setText("LIMITE DÉPASSÉE!")
            self.lbl_poids_warning.setStyleSheet(S.bold("#e74c3c"))
        elif pourcentage > 70:
            self.progress_poids.setStyleSheet(S.PROGRESS_WARN)
            self.lbl_poids_warning.setText("Attention")
            self.lbl_poids_warning.setStyleSheet(S.bold("#f39c12"))
        else:
            self.progress_poids.setStyleSheet(S.PROGRESS_OK)
            self.lbl_poids_warning.setText("")

    def is_poids_valide(self):
        prod_data = self.combo_modele.currentData()
        if not prod_data:
            return True
        charge_max = prod_data[3] if len(prod_data) > 3 and prod_data[3] else 1000
        limite = charge_max * POIDS_LIMITE_POURCENTAGE
        return self.calculer_poids_total() <= limite
