import sys
import subprocess
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt
from src.models.db_manager import DatabaseManager 


class LauncherWindow(QWidget):
    """Fenêtre de lancement pour choisir ou lancer les deux apps."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Configurateur de Devis - Lanceur")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Titre
        lbl_title = QLabel("🔷 Configurateur de Devis")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #74b9ff;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Choisissez votre interface")
        lbl_subtitle.setStyleSheet("font-size: 14px; color: #b2bec3;")
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_subtitle)
        
        layout.addSpacing(20)
        
        # Bouton lancer les deux
        btn_both = QPushButton("🚀 Lancer Client + Vendeur")
        btn_both.setStyleSheet("""
            background-color: #9b59b6; color: white; 
            padding: 15px; font-size: 16px; font-weight: bold;
            border-radius: 8px;
        """)
        btn_both.clicked.connect(self.lancer_les_deux)
        layout.addWidget(btn_both)
        
        layout.addSpacing(10)
        
        # Bouton Client seul
        btn_client = QPushButton("🛒 Interface CLIENT")
        btn_client.setStyleSheet("""
            background-color: #00b894; color: white; 
            padding: 12px; font-size: 14px;
            border-radius: 5px;
        """)
        btn_client.clicked.connect(self.lancer_client)
        layout.addWidget(btn_client)
        
        # Bouton Vendeur seul
        btn_vendeur = QPushButton("🏭 Interface VENDEUR")
        btn_vendeur.setStyleSheet("""
            background-color: #e74c3c; color: white; 
            padding: 12px; font-size: 14px;
            border-radius: 5px;
        """)
        btn_vendeur.clicked.connect(self.lancer_vendeur)
        layout.addWidget(btn_vendeur)
        
        layout.addStretch()
        
        # Info
        lbl_info = QLabel("Les deux fenêtres partagent la même base de données")
        lbl_info.setStyleSheet("color: #636e72; font-size: 10px;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)
    
    def get_python_exe(self):
        """Retourne le chemin de l'exécutable Python du venv."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            return venv_python
        return sys.executable
    
    def lancer_client(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen([self.get_python_exe(), os.path.join(base_dir, "client_app.py")])
        self.close()
    
    def lancer_vendeur(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen([self.get_python_exe(), os.path.join(base_dir, "vendeur_app.py")])
        self.close()
    
    def lancer_les_deux(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        python_exe = self.get_python_exe()
        subprocess.Popen([python_exe, os.path.join(base_dir, "client_app.py")])
        subprocess.Popen([python_exe, os.path.join(base_dir, "vendeur_app.py")])
        self.close()


def main():
    # --- 1. INITIALISATION DE LA BASE DE DONNÉES ---
    print("--- Démarrage du Configurateur de Devis ---")
    db = DatabaseManager()
    db.create_tables()
    db.add_demo_data()
    print("---------------------------------------")

    # --- 2. LANCEMENT DU LANCEUR ---
    app = QApplication(sys.argv)
    
    # Style Fusion pour un rendu moderne
    app.setStyle("Fusion")
    
    # === THÈME SOMBRE GLOBAL ===
    dark_palette = QPalette()
    
    # Couleurs de base
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 52, 54))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(223, 230, 233))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 39, 46))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 52, 54))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 52, 54))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(223, 230, 233))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(223, 230, 233))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(99, 110, 114))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(223, 230, 233))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(116, 185, 255))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(9, 132, 227))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(dark_palette)
    
    # Style CSS complémentaire
    app.setStyleSheet("""
        QToolTip { 
            color: #dfe6e9; 
            background-color: #2d3436; 
            border: 1px solid #636e72; 
        }
        QTableWidget {
            gridline-color: #636e72;
            background-color: #1e272e;
            alternate-background-color: #2d3436;
        }
        QHeaderView::section {
            background-color: #636e72;
            color: #dfe6e9;
            padding: 5px;
            border: 1px solid #2d3436;
        }
        QTabWidget::pane {
            border: 1px solid #636e72;
            background-color: #2d3436;
        }
        QTabBar::tab {
            background-color: #636e72;
            color: #dfe6e9;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #0984e3;
            color: white;
        }
        QScrollArea {
            background-color: #2d3436;
            border: none;
        }
        QGroupBox {
            border: 1px solid #636e72;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            color: #74b9ff;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    
    window = LauncherWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()