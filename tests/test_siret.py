# ──────────────────────────────────────────────────────────────────────────────
# tests/test_siret.py — Tests unitaires de la validation SIRET
# ──────────────────────────────────────────────────────────────────────────────
import pytest
from src.utils.siret_validator import (
    valider_format_siret,
    valider_siret_luhn,
    valider_siret_complet,
)


# ─── Validation du format ─────────────────────────────────────────

class TestFormatSiret:

    def test_format_valide_14_chiffres(self):
        ok, result = valider_format_siret("12345678901234")
        assert ok is True
        assert result == "12345678901234"

    def test_format_avec_espaces(self):
        """Les espaces doivent être nettoyés."""
        ok, result = valider_format_siret("123 456 789 01234")
        assert ok is True
        assert result == "12345678901234"

    def test_format_avec_tirets(self):
        """Les tirets doivent être nettoyés."""
        ok, result = valider_format_siret("123-456-789-01234")
        assert ok is True
        assert result == "12345678901234"

    def test_format_trop_court(self):
        ok, result = valider_format_siret("1234")
        assert ok is False
        assert "14 chiffres" in result

    def test_format_trop_long(self):
        ok, result = valider_format_siret("123456789012345")
        assert ok is False
        assert "14 chiffres" in result

    def test_format_avec_lettres(self):
        ok, result = valider_format_siret("ABCDEFGHIJKLMN")
        assert ok is False
        assert "chiffres" in result

    def test_format_vide(self):
        ok, result = valider_format_siret("")
        assert ok is False


# ─── Algorithme de Luhn ───────────────────────────────────────────

class TestLuhn:

    def test_siret_valide_luhn(self):
        """SIRET connu comme valide (algorithme de Luhn)."""
        # SIRET de test : 73282932000074 (valide Luhn)
        assert valider_siret_luhn("73282932000074") is True

    def test_siret_invalide_luhn(self):
        """Un SIRET inventé doit échouer à Luhn."""
        assert valider_siret_luhn("12345678901234") is False

    def test_siret_tout_zeros(self):
        """00000000000000 passe Luhn (somme = 0, divisible par 10)."""
        assert valider_siret_luhn("00000000000000") is True


# ─── Validation complète (sans appel API) ─────────────────────────

class TestValidationComplete:

    def test_format_invalide_retourne_erreur(self):
        result = valider_siret_complet("ABC")
        assert result["valide"] is False
        assert result["erreur"] is not None

    def test_luhn_invalide_retourne_erreur(self):
        result = valider_siret_complet("12345678901234")
        assert result["valide"] is False
        assert "algorithmique" in result["erreur"]
