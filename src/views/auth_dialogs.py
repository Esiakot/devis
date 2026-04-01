# ──────────────────────────────────────────────────────────────────────────────
# src/views/auth_dialogs.py — Dialogues d'authentification
# ──────────────────────────────────────────────────────────────────────────────
# InscriptionClientDialog : création de compte / connexion client avec
# validation SIRET, mot de passe robuste, et téléphone formaté.
# ConnexionVendeurDialog : authentification vendeur avec email @symetrie.fr
# obligatoire à l'inscription et mot de passe robuste.
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QFormLayout,
                             QDialogButtonBox, QMessageBox, QTabWidget, QWidget,
                             QApplication, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator

from src.views.theme import S
from src.utils.siret_validator import valider_siret_complet
from src.utils.auth import (valider_force_mot_de_passe, INDICATIFS_TELEPHONE,
                            formater_telephone, extraire_indicatif_numero)


# ═══════════════════════════════════════════════════════════════════════════════
# Widget téléphone réutilisable : indicatif + 9 chiffres max
# ═══════════════════════════════════════════════════════════════════════════════

class TelephoneWidget(QWidget):
    """Champ téléphone avec liste indicatifs + numéro 9 chiffres max."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.combo_indicatif = QComboBox()
        self.combo_indicatif.setMinimumWidth(120)
        for code, pays in INDICATIFS_TELEPHONE:
            self.combo_indicatif.addItem(f"{code} ({pays})", code)
        layout.addWidget(self.combo_indicatif)

        self.input_numero = QLineEdit()
        self.input_numero.setPlaceholderText("6 11 59 26 46")
        self.input_numero.setMaxLength(14)  # "X XX XX XX XX" = 14 chars
        self.input_numero.textChanged.connect(self._auto_format)
        layout.addWidget(self.input_numero, 1)

    def _auto_format(self, text):
        """Formate automatiquement les chiffres saisis en groupes de 2."""
        import re
        chiffres = re.sub(r"\D", "", text)[:9]
        if not chiffres:
            return
        parts = [chiffres[0]]
        for i in range(1, len(chiffres), 2):
            parts.append(chiffres[i:i+2])
        formatted = " ".join(parts)
        if formatted != text:
            self.input_numero.blockSignals(True)
            self.input_numero.setText(formatted)
            self.input_numero.setCursorPosition(len(formatted))
            self.input_numero.blockSignals(False)

    def get_numero_complet(self) -> str:
        """Retourne le numéro complet formaté (ex: '+33 6 11 59 26 46')."""
        import re
        indicatif = self.combo_indicatif.currentData()
        chiffres = re.sub(r"\D", "", self.input_numero.text())[:9]
        return formater_telephone(indicatif, chiffres)

    def get_indicatif(self) -> str:
        return self.combo_indicatif.currentData()

    def get_numero_brut(self) -> str:
        import re
        return re.sub(r"\D", "", self.input_numero.text())[:9]

    def set_from_telephone(self, telephone: str):
        """Remplit le widget depuis un numéro complet stocké."""
        code, numero = extraire_indicatif_numero(telephone)
        for i in range(self.combo_indicatif.count()):
            if self.combo_indicatif.itemData(i) == code:
                self.combo_indicatif.setCurrentIndex(i)
                break
        if numero:
            parts = [numero[0]]
            for j in range(1, len(numero), 2):
                parts.append(numero[j:j+2])
            self.input_numero.setText(" ".join(parts))


# ═══════════════════════════════════════════════════════════════════════════════
# Indicateur de force mot de passe
# ═══════════════════════════════════════════════════════════════════════════════

class PasswordStrengthLabel(QLabel):
    """Affiche les critères du mot de passe en temps réel."""

    RULES = "Min. 10 car., majuscule, minuscule, chiffre, caractère spécial"

    def __init__(self, parent=None):
        super().__init__(self.RULES, parent)
        self.setWordWrap(True)
        self.setStyleSheet("color: #95a5a6; font-size: 11px;")

    def update_strength(self, password: str):
        ok, msg = valider_force_mot_de_passe(password)
        if ok:
            self.setText("Mot de passe valide")
            self.setStyleSheet("color: #27ae60; font-size: 11px;")
        elif not password:
            self.setText(self.RULES)
            self.setStyleSheet("color: #95a5a6; font-size: 11px;")
        else:
            self.setText(f"{msg}")
            self.setStyleSheet("color: #f39c12; font-size: 11px;")


# ══════════════════════════════════════════════════════════════════════════════
# Client — Connexion / Inscription
# ══════════════════════════════════════════════════════════════════════════════

class InscriptionClientDialog(QDialog):
    """Authentification client : connexion ou création de compte avec SIRET."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.client_id = None
        self.client_info = {}

        self.setWindowTitle("Espace Client")
        self.setMinimumWidth(550)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl = QLabel("Espace Client — Configurateur de Devis")
        lbl.setStyleSheet(S.TITLE_CLIENT)
        layout.addWidget(lbl)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "Connexion")
        self.tabs.addTab(self._build_register_tab(), "Nouveau compte")
        layout.addWidget(self.tabs)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    # ─── Onglet Connexion ─────────────────────────────────────────
    def _build_login_tab(self):
        tab = QWidget()
        form = QFormLayout()
        tab.setLayout(form)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Nom d'utilisateur")
        form.addRow("Identifiant:", self.login_username)

        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Mot de passe")
        form.addRow("Mot de passe:", self.login_password)

        btn = QPushButton("Se connecter")
        btn.setStyleSheet(S.BTN_SUCCESS + S.BTN_ACTION)
        btn.clicked.connect(self._login)
        form.addRow(btn)

        self.login_password.returnPressed.connect(self._login)
        self.login_username.returnPressed.connect(self._login)

        return tab

    # ─── Onglet Inscription ───────────────────────────────────────
    def _build_register_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # --- Compte ---
        group_a = QGroupBox("Compte")
        form_a = QFormLayout()
        group_a.setLayout(form_a)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choisir un identifiant")
        form_a.addRow("Identifiant:", self.reg_username)

        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password.setPlaceholderText("Min. 10 car., Maj, min, chiffre, spécial")
        form_a.addRow("Mot de passe:", self.reg_password)

        self.reg_pwd_strength = PasswordStrengthLabel()
        form_a.addRow("", self.reg_pwd_strength)
        self.reg_password.textChanged.connect(self.reg_pwd_strength.update_strength)

        self.reg_password2 = QLineEdit()
        self.reg_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password2.setPlaceholderText("Confirmer le mot de passe")
        form_a.addRow("Confirmer:", self.reg_password2)

        layout.addWidget(group_a)

        # --- Entreprise ---
        group_e = QGroupBox("Entreprise")
        form_e = QFormLayout()
        group_e.setLayout(form_e)

        siret_row = QHBoxLayout()
        self.reg_siret = QLineEdit()
        self.reg_siret.setPlaceholderText("Ex: 73282932000074 (14 chiffres)")
        self.reg_siret.setMaxLength(20)
        siret_row.addWidget(self.reg_siret)
        btn_verif = QPushButton("Vérifier")
        btn_verif.setStyleSheet(S.BTN_PRIMARY)
        btn_verif.clicked.connect(self._verifier_siret)
        siret_row.addWidget(btn_verif)
        form_e.addRow("N° SIRET:", siret_row)

        self.lbl_siret_status = QLabel("")
        self.lbl_siret_status.setWordWrap(True)
        form_e.addRow("", self.lbl_siret_status)

        self.reg_societe = QLineEdit()
        self.reg_societe.setPlaceholderText("Nom de l'entreprise")
        form_e.addRow("Entreprise:", self.reg_societe)

        layout.addWidget(group_e)

        # --- Contact ---
        group_c = QGroupBox("Personne de contact")
        form_c = QFormLayout()
        group_c.setLayout(form_c)

        self.reg_nom = QLineEdit()
        self.reg_nom.setPlaceholderText("Nom de famille")
        form_c.addRow("Nom:", self.reg_nom)

        self.reg_prenom = QLineEdit()
        self.reg_prenom.setPlaceholderText("Prénom")
        form_c.addRow("Prénom:", self.reg_prenom)

        self.reg_service = QLineEdit()
        self.reg_service.setPlaceholderText("Ex: Service Achats, Direction Technique…")
        form_c.addRow("Service:", self.reg_service)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("email@entreprise.com")
        form_c.addRow("Email:", self.reg_email)

        self.reg_tel = TelephoneWidget()
        form_c.addRow("Téléphone:", self.reg_tel)

        layout.addWidget(group_c)

        # --- Bouton ---
        btn = QPushButton("Créer mon compte")
        btn.setStyleSheet(S.BTN_HIGHLIGHT)
        btn.clicked.connect(self._register)
        layout.addWidget(btn)

        return tab

    # ─── Vérification SIRET ───────────────────────────────────────
    def _verifier_siret(self):
        siret_brut = self.reg_siret.text().strip()
        if not siret_brut:
            self.lbl_siret_status.setText("Veuillez saisir un numéro SIRET.")
            self.lbl_siret_status.setStyleSheet("color: #f39c12;")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        result = valider_siret_complet(siret_brut)
        QApplication.restoreOverrideCursor()

        if not result["valide"]:
            self.lbl_siret_status.setText(f"{result['erreur']}")
            self.lbl_siret_status.setStyleSheet("color: #e74c3c;")
            return

        if self.controller.client_siret_existe(result["siret"]):
            self.lbl_siret_status.setText(
                "Ce SIRET est déjà associé à un compte. Utilisez la connexion.")
            self.lbl_siret_status.setStyleSheet("color: #f39c12;")
            return

        if result.get("nom_entreprise"):
            self.lbl_siret_status.setText(
                f"SIRET valide — Entreprise : {result['nom_entreprise']}")
            self.lbl_siret_status.setStyleSheet("color: #27ae60;")
            if not self.reg_societe.text().strip():
                self.reg_societe.setText(result["nom_entreprise"])
        elif result.get("verification_en_ligne") is None:
            self.lbl_siret_status.setText(
                "SIRET valide (vérification en ligne indisponible)")
            self.lbl_siret_status.setStyleSheet("color: #f39c12;")
        else:
            self.lbl_siret_status.setText("SIRET valide")
            self.lbl_siret_status.setStyleSheet("color: #27ae60;")

    # ─── Connexion ────────────────────────────────────────────────
    def _login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Champs requis",
                                "Veuillez remplir tous les champs.")
            return

        info = self.controller.authentifier_client(username, password)
        if info:
            self.client_id = info["id"]
            self.client_info = {
                "nom": info["nom"],
                "prenom": info["prenom"],
                "service": info["service"],
                "societe": info["nom_societe"],
                "siret": info["siret"],
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Échec d'authentification",
                                "Identifiant ou mot de passe incorrect.")

    # ─── Inscription ──────────────────────────────────────────────
    def _register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        password2 = self.reg_password2.text()
        siret_brut = self.reg_siret.text().strip()
        societe = self.reg_societe.text().strip()
        nom = self.reg_nom.text().strip()
        prenom = self.reg_prenom.text().strip()
        service = self.reg_service.text().strip()
        email = self.reg_email.text().strip()

        # Champs obligatoires
        for val, label in [
            (username, "L'identifiant"),
            (siret_brut, "Le numéro SIRET"),
            (societe, "Le nom de l'entreprise"),
            (nom, "Le nom"),
            (prenom, "Le prénom"),
            (service, "Le service"),
        ]:
            if not val:
                QMessageBox.warning(self, "Champ requis",
                                    f"{label} est obligatoire.")
                return

        # Mot de passe
        pwd_ok, pwd_msg = valider_force_mot_de_passe(password)
        if not pwd_ok:
            QMessageBox.warning(self, "Mot de passe invalide", pwd_msg)
            return
        if password != password2:
            QMessageBox.warning(self, "Mots de passe différents",
                                "Les deux mots de passe ne correspondent pas.")
            return

        # Username unique
        if self.controller.client_username_existe(username):
            QMessageBox.warning(self, "Identifiant déjà pris",
                                "Ce nom d'utilisateur existe déjà.")
            return

        # SIRET
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        result = valider_siret_complet(siret_brut)
        QApplication.restoreOverrideCursor()

        if not result["valide"]:
            QMessageBox.warning(self, "SIRET invalide", result["erreur"])
            return

        siret = result["siret"]

        if self.controller.client_siret_existe(siret):
            QMessageBox.warning(self, "SIRET déjà enregistré",
                                "Ce SIRET est déjà associé à un compte.\n"
                                "Utilisez l'onglet Connexion.")
            return

        # Téléphone
        telephone = self.reg_tel.get_numero_complet()
        indicatif = self.reg_tel.get_indicatif()

        # Création du compte
        client_id = self.controller.creer_compte_client(
            username, password, societe, siret,
            nom, prenom, service, email, telephone, indicatif)

        if client_id:
            self.client_id = client_id
            self.client_info = {
                "nom": nom,
                "prenom": prenom,
                "service": service,
                "societe": societe,
                "siret": siret,
            }
            QMessageBox.information(
                self, "Compte créé",
                f"Bienvenue {prenom} {nom} !\n"
                f"Votre compte a été créé avec succès.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur",
                                 "Impossible de créer le compte.")


# ══════════════════════════════════════════════════════════════════════════════
# Connexion Vendeur
# ══════════════════════════════════════════════════════════════════════════════

class ConnexionVendeurDialog(QDialog):
    """Authentification vendeur : connexion ou création de compte."""

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.vendeur_info = None

        self.setWindowTitle("Espace Vendeur")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl = QLabel("Authentification Vendeur")
        lbl.setStyleSheet(S.TITLE_VENDEUR)
        layout.addWidget(lbl)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "Connexion")
        self.tabs.addTab(self._build_register_tab(), "Nouveau compte")
        layout.addWidget(self.tabs)

        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

    # ─── Onglet Connexion ─────────────────────────────────────────
    def _build_login_tab(self):
        tab = QWidget()
        form = QFormLayout()
        tab.setLayout(form)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Nom d'utilisateur")
        form.addRow("Identifiant:", self.login_username)

        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Mot de passe")
        form.addRow("Mot de passe:", self.login_password)

        btn = QPushButton("Se connecter")
        btn.setStyleSheet(S.BTN_DANGER + S.BTN_ACTION)
        btn.clicked.connect(self._login)
        form.addRow(btn)

        self.login_password.returnPressed.connect(self._login)
        self.login_username.returnPressed.connect(self._login)

        return tab

    # ─── Onglet Inscription ───────────────────────────────────────
    def _build_register_tab(self):
        tab = QWidget()
        form = QFormLayout()
        tab.setLayout(form)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choisir un identifiant")
        form.addRow("Identifiant:", self.reg_username)

        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("prenom.nom@symetrie.fr")
        form.addRow("Email:", self.reg_email)
        self.lbl_email_hint = QLabel("L'email doit être en @symetrie.fr")
        self.lbl_email_hint.setStyleSheet("color: #95a5a6; font-size: 11px;")
        form.addRow("", self.lbl_email_hint)

        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password.setPlaceholderText("Min. 10 car., Maj, min, chiffre, spécial")
        form.addRow("Mot de passe:", self.reg_password)

        self.reg_pwd_strength = PasswordStrengthLabel()
        form.addRow("", self.reg_pwd_strength)
        self.reg_password.textChanged.connect(self.reg_pwd_strength.update_strength)

        self.reg_password2 = QLineEdit()
        self.reg_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password2.setPlaceholderText("Confirmer le mot de passe")
        form.addRow("Confirmer:", self.reg_password2)

        self.reg_nom = QLineEdit()
        self.reg_nom.setPlaceholderText("Nom de famille")
        form.addRow("Nom:", self.reg_nom)

        self.reg_prenom = QLineEdit()
        self.reg_prenom.setPlaceholderText("Prénom")
        form.addRow("Prénom:", self.reg_prenom)

        btn = QPushButton("Créer le compte")
        btn.setStyleSheet(S.BTN_HIGHLIGHT)
        btn.clicked.connect(self._register)
        form.addRow(btn)

        return tab

    # ─── Connexion ────────────────────────────────────────────────
    def _login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Champs requis",
                                "Veuillez remplir tous les champs.")
            return

        info = self.controller.authentifier(username, password)
        if info:
            self.vendeur_info = info
            self.accept()
        else:
            QMessageBox.warning(self, "Échec d'authentification",
                                "Identifiant ou mot de passe incorrect.")

    # ─── Création de compte ───────────────────────────────────────
    def _register(self):
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text()
        password2 = self.reg_password2.text()
        nom = self.reg_nom.text().strip()
        prenom = self.reg_prenom.text().strip()

        if not username or not password or not nom or not prenom or not email:
            QMessageBox.warning(self, "Champs requis",
                                "Veuillez remplir tous les champs.")
            return

        # Validation email @symetrie.fr
        if not email.lower().endswith("@symetrie.fr"):
            QMessageBox.warning(self, "Email invalide",
                                "L'email doit être une adresse @symetrie.fr\n"
                                "Exemple : prenom.nom@symetrie.fr")
            return

        # Validation mot de passe
        pwd_ok, pwd_msg = valider_force_mot_de_passe(password)
        if not pwd_ok:
            QMessageBox.warning(self, "Mot de passe invalide", pwd_msg)
            return

        if password != password2:
            QMessageBox.warning(self, "Mots de passe différents",
                                "Les deux mots de passe ne correspondent pas.")
            return

        if self.controller.username_existe(username):
            QMessageBox.warning(self, "Identifiant déjà pris",
                                "Ce nom d'utilisateur existe déjà. Choisissez-en un autre.")
            return

        vendeur_id = self.controller.creer_compte_vendeur(
            username, password, nom, prenom, email)
        if vendeur_id:
            self.vendeur_info = {
                "id": vendeur_id,
                "username": username,
                "nom": nom,
                "prenom": prenom,
            }
            QMessageBox.information(
                self, "Compte créé",
                f"Bienvenue {prenom} {nom} !\nVotre compte a été créé avec succès.")
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur",
                                 "Impossible de créer le compte.")
