# ──────────────────────────────────────────────────────────────────────────────
# main.py — Lanceur principal du Configurateur de Devis
# ──────────────────────────────────────────────────────────────────────────────
# Point d'entrée de l'application. Affiche une fenêtre de lancement (LauncherWindow)
# qui permet à l'utilisateur de démarrer l'interface Client, l'interface Vendeur,
# ou les deux simultanément dans des processus séparés. Gère également le
# bootstrapping PyQt6 (palette sombre, stylesheet) commun à toutes les fenêtres.
# ──────────────────────────────────────────────────────────────────────────────
import sys
import subprocess
import os

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

from src.models.db_manager import DatabaseManager
from src.views.theme import create_dark_palette, LAUNCHER_STYLESHEET, S

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _get_python_exe():
    """Retourne le chemin de l'exécutable Python du venv (cross-platform)."""
    for rel in (".venv/bin/python", ".venv/Scripts/python.exe"):
        path = os.path.join(BASE_DIR, rel)
        if os.path.exists(path):
            return path
    return sys.executable


def run_app(app_class, palette_accent, stylesheet_key):
    """Boilerplate commun à toutes les fenêtres PyQt du projet."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if stylesheet_key == 'launcher':
        app.setPalette(create_dark_palette(palette_accent))
        app.setStyleSheet(LAUNCHER_STYLESHEET)
    else:
        from src.views.theme import get_stylesheet
        app.setPalette(create_dark_palette(palette_accent))
        app.setStyleSheet(get_stylesheet(stylesheet_key))
    window = app_class()
    window.show()
    sys.exit(app.exec())


class LauncherWindow(QWidget):
    """Fenêtre de lancement pour choisir ou lancer les deux apps."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurateur de Devis - Lanceur")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        lbl_title = QLabel("Configurateur de Devis")
        lbl_title.setStyleSheet(S.LAUNCHER_TITLE)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        lbl_subtitle = QLabel("Choisissez votre interface")
        lbl_subtitle.setStyleSheet(S.LAUNCHER_SUBTITLE)
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_subtitle)

        layout.addSpacing(20)

        btn_both = QPushButton("Lancer Client + Vendeur")
        btn_both.setStyleSheet(S.LAUNCHER_BTN_MAIN)
        btn_both.clicked.connect(self._lancer_les_deux)
        layout.addWidget(btn_both)

        layout.addSpacing(10)

        btn_client = QPushButton("Interface CLIENT")
        btn_client.setStyleSheet(S.LAUNCHER_BTN_CLIENT)
        btn_client.clicked.connect(lambda: self._lancer("client_app.py"))
        layout.addWidget(btn_client)

        btn_vendeur = QPushButton("Interface VENDEUR")
        btn_vendeur.setStyleSheet(S.LAUNCHER_BTN_VENDEUR)
        btn_vendeur.clicked.connect(lambda: self._lancer("vendeur_app.py"))
        layout.addWidget(btn_vendeur)

        layout.addStretch()

        lbl_info = QLabel("Les deux fenêtres partagent la même base de données")
        lbl_info.setStyleSheet(S.LAUNCHER_INFO)
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

    def _lancer(self, script):
        subprocess.Popen([_get_python_exe(), os.path.join(BASE_DIR, script)])
        self.close()

    def _lancer_les_deux(self):
        exe = _get_python_exe()
        subprocess.Popen([exe, os.path.join(BASE_DIR, "client_app.py")])
        subprocess.Popen([exe, os.path.join(BASE_DIR, "vendeur_app.py")])
        self.close()


def main():
    DatabaseManager()  # Initialise la base (schéma + données démo)
    run_app(LauncherWindow, 'purple', 'launcher')


if __name__ == "__main__":
    main()
