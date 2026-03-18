# ──────────────────────────────────────────────────────────────────────────────
# src/utils/siret_validator.py — Validation des numéros SIRET
# ──────────────────────────────────────────────────────────────────────────────
# Vérifie la validité d'un numéro SIRET français (14 chiffres) en trois étapes :
# 1. Contrôle du format (14 chiffres uniquement)
# 2. Algorithme de Luhn (vérification mathématique)
# 3. Vérification en ligne via l'API publique du gouvernement (optionnelle)
# ──────────────────────────────────────────────────────────────────────────────

import json
import urllib.request
import urllib.error


def valider_format_siret(siret: str) -> tuple[bool, str]:
    """Vérifie le format du SIRET (14 chiffres).
    Returns (ok, siret_nettoyé_ou_message_erreur).
    """
    siret_clean = siret.replace(" ", "").replace("-", "").replace(".", "")
    if not siret_clean.isdigit():
        return False, "Le SIRET ne doit contenir que des chiffres."
    if len(siret_clean) != 14:
        return False, f"Le SIRET doit comporter 14 chiffres (actuellement {len(siret_clean)})."
    return True, siret_clean


def valider_siret_luhn(siret: str) -> bool:
    """Vérifie le numéro SIRET via l'algorithme de Luhn.
    Note : quelques établissements de La Poste (SIREN 356000000) sont une
    exception connue à cet algorithme.
    """
    total = 0
    for i, ch in enumerate(reversed(siret)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def verifier_siret_en_ligne(siret: str) -> tuple[bool | None, str]:
    """Vérifie le SIRET via l'API publique du gouvernement français.

    Returns (result, nom_entreprise):
        - (True,  nom) si le SIRET est trouvé et confirmé
        - (False, "")  si le SIRET n'est pas référencé
        - (None,  "")  si l'API est indisponible
    """
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={siret}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DevisApp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            for result in data.get("results", []):
                # Vérifier dans les établissements correspondants
                for etab in result.get("matching_etablissements", []):
                    if etab.get("siret") == siret:
                        return True, result.get("nom_complet", "")
                # Vérifier le siège
                if result.get("siege", {}).get("siret") == siret:
                    return True, result.get("nom_complet", "")
            return False, ""
    except Exception:
        return None, ""


def valider_siret_complet(siret_brut: str) -> dict:
    """Validation complète du SIRET (format + Luhn + API en ligne).

    Returns dict avec clés :
        valide: bool
        siret: str (nettoyé)
        erreur: str | None
        nom_entreprise: str
        verification_en_ligne: True | False | None
    """
    # 1. Format
    format_ok, result = valider_format_siret(siret_brut)
    if not format_ok:
        return {"valide": False, "siret": siret_brut, "erreur": result}

    siret = result  # nettoyé

    # 2. Luhn
    if not valider_siret_luhn(siret):
        return {
            "valide": False,
            "siret": siret,
            "erreur": "Le numéro SIRET est invalide (vérification algorithmique échouée).",
        }

    # 3. Vérification en ligne (best-effort)
    en_ligne, nom = verifier_siret_en_ligne(siret)

    if en_ligne is True:
        return {
            "valide": True,
            "siret": siret,
            "erreur": None,
            "nom_entreprise": nom,
            "verification_en_ligne": True,
        }
    elif en_ligne is False:
        return {
            "valide": False,
            "siret": siret,
            "erreur": "Ce numéro SIRET n'est pas référencé dans la base officielle.",
            "verification_en_ligne": False,
        }
    else:
        # API indisponible → on se fie au Luhn uniquement
        return {
            "valide": True,
            "siret": siret,
            "erreur": None,
            "nom_entreprise": "",
            "verification_en_ligne": None,
        }
