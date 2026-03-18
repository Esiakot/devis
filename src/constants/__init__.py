# ──────────────────────────────────────────────────────────────────────────────
# src/constants/__init__.py — Constantes centralisées du projet
# ──────────────────────────────────────────────────────────────────────────────
# Point d'import unique pour toutes les constantes de l'application. Regroupe
# et réexporte les constantes métier (TVA, entreprise, conditions générales),
# les constantes de statuts (couleurs, emojis) et les constantes PDF (palette).
# Tous les modules du projet importent leurs constantes depuis ce package.
# ──────────────────────────────────────────────────────────────────────────────

from src.constants.business import (
    TVA_RATE, POIDS_LIMITE_POURCENTAGE, DEVIS_VALIDITE_JOURS,
    AUTO_REFRESH_MS, ENTREPRISE, CONDITIONS_GENERALES,
)
from src.constants.statuts import (
    STATUT_COLORS, STATUT_EMOJIS, STATUT_CLOTURE_LABELS, ROLE_COLORS,
    get_statut_emoji, get_statut_color,
)
from src.constants.pdf import PDF_COLORS
