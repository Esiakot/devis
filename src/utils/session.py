# ──────────────────────────────────────────────────────────────────────────────
# src/utils/session.py — Persistance de session utilisateur
# ──────────────────────────────────────────────────────────────────────────────
# Stocke / récupère la session active (client ou vendeur) dans un fichier JSON
# sous data/. Permet de rester connecté entre plusieurs ouvertures de l'app.
# ──────────────────────────────────────────────────────────────────────────────

import json
import os

_SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data")


def _session_path(role: str) -> str:
    """Retourne le chemin du fichier session pour un rôle donné."""
    return os.path.join(_SESSION_DIR, f"session_{role}.json")


def sauvegarder_session(role: str, data: dict):
    """Sauvegarde les informations de session sur disque."""
    os.makedirs(_SESSION_DIR, exist_ok=True)
    with open(_session_path(role), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def charger_session(role: str) -> dict | None:
    """Charge la session existante. Retourne None si absente ou corrompue."""
    path = _session_path(role)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def supprimer_session(role: str):
    """Supprime le fichier de session (déconnexion)."""
    path = _session_path(role)
    if os.path.exists(path):
        os.remove(path)
