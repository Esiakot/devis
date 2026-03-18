# ──────────────────────────────────────────────────────────────────────────────
# src/constants/statuts.py — Statuts, couleurs et emojis
# ──────────────────────────────────────────────────────────────────────────────
# Centralise les constantes liées aux statuts des options (en attente, accepté,
# refusé, contre-proposition) et des affaires (gagnée, perdue, annulée).
# Fournit les dictionnaires de couleurs et d'emojis associés, ainsi que les
# couleurs par rôle (acheteur/vendeur) et deux fonctions helper utilitaires.
# ──────────────────────────────────────────────────────────────────────────────

# --- Couleurs des statuts (partagées UI + PDF) ---
STATUT_COLORS = {
    'en_attente': '#95a5a6',
    'accepte': '#27ae60',
    'refuse': '#e74c3c',
    'contre_proposition': '#f39c12',
}

STATUT_EMOJIS = {
    'en_attente': '⏳',
    'accepte': '✅',
    'refuse': '❌',
    'contre_proposition': '💬',
}

STATUT_CLOTURE_LABELS = {
    'gagne': '✅ GAGNÉE',
    'perdu': '❌ PERDUE',
    'annule': '🚫 ANNULÉE',
}

# --- Couleurs des rôles (commentaires, badges) ---
ROLE_COLORS = {
    'acheteur': '#00b894',
    'vendeur': '#e74c3c',
}


def get_statut_emoji(statut: str) -> str:
    """Retourne l'emoji correspondant à un statut d'option."""
    return STATUT_EMOJIS.get(statut, '⏳')


def get_statut_color(statut: str) -> str:
    """Retourne la couleur hex correspondant à un statut d'option."""
    return STATUT_COLORS.get(statut, '#95a5a6')
