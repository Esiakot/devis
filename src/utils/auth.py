# ──────────────────────────────────────────────────────────────────────────────
# src/utils/auth.py — Hachage, vérification de mots de passe, validation
# ──────────────────────────────────────────────────────────────────────────────
# Utilise PBKDF2-HMAC-SHA256 avec sel aléatoire (32 octets) et 100 000
# itérations. Le format de stockage est "sel_hex:hash_hex". La comparaison
# se fait en temps constant via hmac.compare_digest pour éviter les
# attaques par timing.
# ──────────────────────────────────────────────────────────────────────────────

import hashlib
import hmac
import os
import re

_ITERATIONS = 100_000
_SALT_LENGTH = 32


def hash_password(password: str) -> str:
    """Hache un mot de passe avec un sel aléatoire (PBKDF2-SHA256).

    Returns "sel_hex:hash_hex" prêt à être stocké en base.
    """
    salt = os.urandom(_SALT_LENGTH)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    return salt.hex() + ":" + hash_bytes.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie un mot de passe contre un hash stocké (comparaison temps constant)."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, _ITERATIONS
        )
        return hmac.compare_digest(hash_bytes.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def valider_force_mot_de_passe(password: str) -> tuple[bool, str]:
    """Vérifie la robustesse d'un mot de passe.

    Règles : ≥10 caractères, majuscule, minuscule, chiffre, caractère spécial.
    Returns (ok, message_erreur_ou_vide).
    """
    if len(password) < 10:
        return False, "Le mot de passe doit contenir au moins 10 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%...)."
    return True, ""


# ─── Indicatifs téléphoniques ─────────────────────────────────────
INDICATIFS_TELEPHONE = [
    ("+33", "France"),
    ("+32", "Belgique"),
    ("+41", "Suisse"),
    ("+352", "Luxembourg"),
    ("+377", "Monaco"),
    ("+1", "États-Unis / Canada"),
    ("+44", "Royaume-Uni"),
    ("+49", "Allemagne"),
    ("+34", "Espagne"),
    ("+39", "Italie"),
    ("+351", "Portugal"),
    ("+31", "Pays-Bas"),
    ("+46", "Suède"),
    ("+47", "Norvège"),
    ("+45", "Danemark"),
    ("+358", "Finlande"),
    ("+48", "Pologne"),
    ("+420", "Rép. Tchèque"),
    ("+43", "Autriche"),
    ("+81", "Japon"),
    ("+86", "Chine"),
    ("+91", "Inde"),
    ("+55", "Brésil"),
    ("+212", "Maroc"),
    ("+216", "Tunisie"),
    ("+213", "Algérie"),
]


def formater_telephone(indicatif: str, numero_brut: str) -> str:
    """Formate un numéro de téléphone : indicatif + groupes de 2 chiffres.

    Ex: formater_telephone("+33", "611592646") -> "+33 6 11 59 26 46"
    """
    chiffres = re.sub(r"\D", "", numero_brut)[:9]
    if not chiffres:
        return ""
    # Premier chiffre seul, puis groupes de 2
    parts = [chiffres[0]]
    for i in range(1, len(chiffres), 2):
        parts.append(chiffres[i:i+2])
    return f"{indicatif} {' '.join(parts)}"


def extraire_indicatif_numero(telephone: str) -> tuple[str, str]:
    """Extrait l'indicatif et le numéro brut d'un téléphone formaté.

    Ex: "+33 6 11 59 26 46" -> ("+33", "611592646")
    """
    if not telephone:
        return "+33", ""
    # Chercher l'indicatif le plus long en premier
    for code, _ in sorted(INDICATIFS_TELEPHONE, key=lambda x: -len(x[0])):
        if telephone.startswith(code):
            numero = re.sub(r"\D", "", telephone[len(code):])
            return code, numero
    return "+33", re.sub(r"\D", "", telephone)
