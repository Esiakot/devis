# ──────────────────────────────────────────────────────────────────────────────
# src/views/theme.py — Thèmes et styles de l'application
# ──────────────────────────────────────────────────────────────────────────────
# Centralise toute la personnalisation visuelle : palettes sombres QPalette
# avec accent configurable (bleu/rouge/violet), feuilles de style CSS Qt
# pour chaque interface (client, vendeur, launcher), et la classe S regroupant
# toutes les constantes de style (boutons, labels, tableaux, etc.).
# ──────────────────────────────────────────────────────────────────────────────

from PyQt6.QtGui import QPalette, QColor


def create_dark_palette(accent_color: str = "blue") -> QPalette:
    """
    Crée une palette sombre pour QApplication.
    accent_color: 'blue' (client), 'red' (vendeur), 'purple' (launcher)
    """
    palette = QPalette()

    palette.setColor(QPalette.ColorRole.Window, QColor(30, 35, 40))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 30, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 45, 50))
    palette.setColor(QPalette.ColorRole.Text, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(236, 240, 241))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(236, 240, 241))

    accents = {
        'blue': {
            'button': QColor(52, 73, 94),
            'highlight': QColor(52, 152, 219),
            'link': QColor(52, 152, 219),
        },
        'red': {
            'button': QColor(94, 52, 52),
            'highlight': QColor(231, 76, 60),
            'link': QColor(231, 76, 60),
        },
        'purple': {
            'button': QColor(99, 110, 114),
            'highlight': QColor(9, 132, 227),
            'link': QColor(116, 185, 255),
        },
    }

    a = accents.get(accent_color, accents['blue'])
    palette.setColor(QPalette.ColorRole.Button, a['button'])
    palette.setColor(QPalette.ColorRole.Highlight, a['highlight'])
    palette.setColor(QPalette.ColorRole.Link, a['link'])

    return palette


# --- Feuille de style de base (partagée) ---
_BASE_STYLESHEET = """
    QMainWindow {{
        background-color: #1e2328;
    }}
    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 5px;
        background-color: #1e2328;
    }}
    QTabBar::tab {{
        background-color: {tab_bg};
        color: #ecf0f1;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }}
    QTabBar::tab:selected {{
        background-color: {accent};
        color: white;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {tab_hover};
    }}
    QPushButton {{
        background-color: {accent};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {accent_hover};
    }}
    QPushButton:pressed {{
        background-color: {accent_pressed};
    }}
    QPushButton:disabled {{
        background-color: #5d6d7e;
        color: #aeb6bf;
    }}
    QTableWidget {{
        background-color: #1e2328;
        alternate-background-color: #252a30;
        gridline-color: {border};
        border: 1px solid {border};
        border-radius: 5px;
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {accent};
        color: white;
    }}
    QHeaderView::section {{
        background-color: {tab_bg};
        color: #ecf0f1;
        padding: 8px;
        border: none;
        font-weight: bold;
    }}
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: #2c3e50;
        color: #ecf0f1;
        border: 1px solid {border};
        border-radius: 4px;
        padding: 6px;
    }}
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 2px solid {accent};
    }}
    QGroupBox {{
        font-weight: bold;
        border: 1px solid {border};
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: {accent};
    }}
    QScrollBar:vertical {{
        background-color: #1e2328;
        width: 12px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {border};
        border-radius: 6px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {accent};
    }}
    QProgressBar {{
        border: 1px solid {border};
        border-radius: 4px;
        text-align: center;
        background-color: #2c3e50;
    }}
    QProgressBar::chunk {{
        background-color: {accent};
        border-radius: 3px;
    }}
"""


def get_stylesheet(theme: str = "client") -> str:
    """
    Retourne la feuille de style CSS Qt selon le thème.
    theme: 'client' (bleu), 'vendeur' (rouge)
    """
    themes = {
        'client': {
            'accent': '#3498db',
            'accent_hover': '#2980b9',
            'accent_pressed': '#21618c',
            'border': '#34495e',
            'tab_bg': '#2c3e50',
            'tab_hover': '#34495e',
        },
        'vendeur': {
            'accent': '#e74c3c',
            'accent_hover': '#c0392b',
            'accent_pressed': '#922b21',
            'border': '#5e3434',
            'tab_bg': '#4a2c2c',
            'tab_hover': '#5e3434',
        },
    }

    t = themes.get(theme, themes['client'])
    return _BASE_STYLESHEET.format(**t)


# --- Style launcher (main.py) ---
LAUNCHER_STYLESHEET = """
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
"""


class S:
    """Named style constants — replaces all inline setStyleSheet() calls."""

    # --- Headers ---
    HEADER_CLIENT = "font-size: 20px; font-weight: bold; color: #00b894; padding: 10px;"
    HEADER_VENDEUR = "font-size: 20px; font-weight: bold; color: #e74c3c; padding: 10px;"

    # --- Titles ---
    TITLE = "font-size: 16px; font-weight: bold; color: #74b9ff;"
    TITLE_CLIENT = "font-size: 16px; font-weight: bold; color: #00b894;"
    TITLE_VENDEUR = "font-size: 16px; font-weight: bold; color: #e74c3c;"

    # --- Buttons ---
    BTN_SUCCESS = "background-color: #27ae60; color: white;"
    BTN_PRIMARY = "background-color: #3498db; color: white;"
    BTN_DANGER = "background-color: #e74c3c; color: white;"
    BTN_ACCENT = "background-color: #9b59b6; color: white;"
    BTN_CLOTURE = "background-color: #8e44ad; color: white; padding: 8px;"
    BTN_HIGHLIGHT = "background-color: #00b894; color: white; padding: 10px; font-size: 14px;"
    BTN_SUBMIT = "background-color: #3498db; color: white; padding: 15px; font-size: 16px;"
    BTN_ACTION = "padding: 10px;"
    BTN_DISABLED = "background-color: #636e72; color: #b2bec3; padding: 10px;"
    BTN_REMOVE = "background-color: #e74c3c; color: white; border-radius: 5px;"
    BTN_ADD_PERSO = "background-color: #8e44ad; color: white; padding: 5px;"

    # --- Labels ---
    LBL_MUTED = "color: #b2bec3;"
    LBL_INFO = "color: #f39c12; font-style: italic;"
    LBL_WARNING = "color: #f39c12; font-size: 14px;"
    LBL_TOTAL = "font-size: 18px; font-weight: bold; color: #00b894;"
    LBL_PRODUCT = "font-weight: bold; font-size: 14px; color: #74b9ff;"
    LBL_OPTION = "color: #dfe6e9; font-weight: bold;"
    LBL_BOLD_BLUE = "font-weight: bold; color: #74b9ff;"
    LBL_BOLD = "font-weight: bold;"
    LBL_SUBTOTAL = "font-weight: bold; color: #00b894;"

    # --- Alert boxes ---
    ALERT_ERROR = "color: #e74c3c; font-weight: bold; padding: 10px; background-color: #2d3436; border-radius: 5px;"

    # --- Frames ---
    FRAME_DARK = "background-color: #2d3436; padding: 10px; border-radius: 5px;"
    FRAME_OPTION = "background-color: #636e72; padding: 8px; margin: 3px; border-radius: 5px;"
    FRAME_PERSO = "background-color: #636e72; padding: 5px; border-radius: 3px;"

    # --- Product widget ---
    WIDGET_PRODUCT = """
        QFrame { background-color: #2d3436; border-radius: 5px; padding: 10px; }
        QLabel { color: #dfe6e9; }
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { color: #dfe6e9; background-color: #636e72; }
        QCheckBox { color: #dfe6e9; }
        QGroupBox { color: #74b9ff; font-weight: bold; }
    """
    PROGRESS_OK = """
        QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
        QProgressBar::chunk { background-color: #27ae60; border-radius: 5px; }
    """
    PROGRESS_WARN = """
        QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
        QProgressBar::chunk { background-color: #f39c12; border-radius: 5px; }
    """
    PROGRESS_DANGER = """
        QProgressBar { background-color: #636e72; border-radius: 5px; text-align: center; }
        QProgressBar::chunk { background-color: #e74c3c; border-radius: 5px; }
    """

    # --- Spin box dynamic ---
    SPIN_ACTIVE = "background-color: #f39c12; color: black;"
    SPIN_INACTIVE = "background-color: #636e72; color: #b2bec3;"

    # --- Checkbox states (ProduitConfigWidget) ---
    CB_AVAILABLE = "color: #dfe6e9;"
    CB_UNAVAILABLE = "color: #e74c3c;"

    # --- Launcher ---
    LAUNCHER_TITLE = "font-size: 24px; font-weight: bold; color: #74b9ff;"
    LAUNCHER_SUBTITLE = "font-size: 14px; color: #b2bec3;"
    LAUNCHER_INFO = "color: #636e72; font-size: 10px;"
    LAUNCHER_BTN_MAIN = ("background-color: #9b59b6; color: white; "
                         "padding: 15px; font-size: 16px; font-weight: bold; border-radius: 8px;")
    LAUNCHER_BTN_CLIENT = ("background-color: #00b894; color: white; "
                           "padding: 12px; font-size: 14px; border-radius: 5px;")
    LAUNCHER_BTN_VENDEUR = ("background-color: #e74c3c; color: white; "
                            "padding: 12px; font-size: 14px; border-radius: 5px;")

    # --- Dynamic helpers ---
    @staticmethod
    def bold(color: str) -> str:
        return f"color: {color}; font-weight: bold;"

    @staticmethod
    def italic(color: str) -> str:
        return f"color: {color}; font-style: italic;"

    @staticmethod
    def bold_italic(color: str) -> str:
        return f"color: {color}; font-weight: bold; font-style: italic;"

    @staticmethod
    def badge(bg_color: str) -> str:
        return (f"font-size: 14px; font-weight: bold; padding: 5px 10px; "
                f"border-radius: 5px; background-color: {bg_color}; color: white;")
