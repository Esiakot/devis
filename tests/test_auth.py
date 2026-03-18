# ──────────────────────────────────────────────────────────────────────────────
# tests/test_auth.py — Tests unitaires du module d'authentification
# ──────────────────────────────────────────────────────────────────────────────
import pytest
from src.utils.auth import hash_password, verify_password, valider_force_mot_de_passe


# ─── Hachage et vérification ──────────────────────────────────────

class TestHashPassword:

    def test_hash_retourne_format_sel_hash(self):
        """Le hash doit être au format 'sel_hex:hash_hex'."""
        result = hash_password("MonMotDePasse1!")
        assert ":" in result
        sel, hsh = result.split(":")
        assert len(sel) == 64  # 32 octets en hex
        assert len(hsh) == 64  # SHA-256 = 32 octets en hex

    def test_hash_est_different_a_chaque_appel(self):
        """Deux appels avec le même mot de passe produisent des hashes différents (sel aléatoire)."""
        h1 = hash_password("MotDePasse123!")
        h2 = hash_password("MotDePasse123!")
        assert h1 != h2

    def test_verification_mot_de_passe_correct(self):
        """verify_password retourne True pour le bon mot de passe."""
        stored = hash_password("SecurePass10!")
        assert verify_password("SecurePass10!", stored) is True

    def test_verification_mot_de_passe_incorrect(self):
        """verify_password retourne False pour un mauvais mot de passe."""
        stored = hash_password("SecurePass10!")
        assert verify_password("mauvais", stored) is False

    def test_verification_hash_corrompu(self):
        """verify_password retourne False si le hash est corrompu."""
        assert verify_password("test", "pas_un_hash_valide") is False

    def test_verification_hash_vide(self):
        """verify_password retourne False si le hash est vide."""
        assert verify_password("test", "") is False


# ─── Validation de la force du mot de passe ───────────────────────

class TestValidationForceMotDePasse:

    def test_mot_de_passe_valide(self):
        """Un mot de passe respectant toutes les règles est accepté."""
        ok, msg = valider_force_mot_de_passe("MonPass123!")
        assert ok is True
        assert msg == ""

    def test_trop_court(self):
        """Rejeté si moins de 10 caractères."""
        ok, msg = valider_force_mot_de_passe("Ab1!")
        assert ok is False
        assert "10 caractères" in msg

    def test_sans_majuscule(self):
        """Rejeté sans majuscule."""
        ok, msg = valider_force_mot_de_passe("monpass123!")
        assert ok is False
        assert "majuscule" in msg

    def test_sans_minuscule(self):
        """Rejeté sans minuscule."""
        ok, msg = valider_force_mot_de_passe("MONPASS123!")
        assert ok is False
        assert "minuscule" in msg

    def test_sans_chiffre(self):
        """Rejeté sans chiffre."""
        ok, msg = valider_force_mot_de_passe("MonPassWord!")
        assert ok is False
        assert "chiffre" in msg

    def test_sans_caractere_special(self):
        """Rejeté sans caractère spécial."""
        ok, msg = valider_force_mot_de_passe("MonPass1234")
        assert ok is False
        assert "spécial" in msg
