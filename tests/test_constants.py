# ──────────────────────────────────────────────────────────────────────────────
# tests/test_constants.py — Tests des constantes métier
# ──────────────────────────────────────────────────────────────────────────────
import pytest
from src.constants.business import TVA_RATE, POIDS_LIMITE_POURCENTAGE, DEVIS_VALIDITE_JOURS, ENTREPRISE
from src.constants.statuts import (
    STATUT_COLORS, STATUT_EMOJIS, ROLE_COLORS,
    get_statut_emoji, get_statut_color,
)


class TestConstantesBusiness:

    def test_tva_rate_valide(self):
        """Le taux de TVA est un pourcentage réaliste."""
        assert 0 < TVA_RATE < 1
        assert TVA_RATE == 0.20

    def test_poids_limite_pourcentage(self):
        """Le seuil de poids est entre 0 et 1."""
        assert 0 < POIDS_LIMITE_POURCENTAGE < 1

    def test_validite_devis_positive(self):
        """La durée de validité du devis est positive."""
        assert DEVIS_VALIDITE_JOURS > 0

    def test_entreprise_champs_obligatoires(self):
        """Les champs essentiels de l'entreprise sont présents."""
        for champ in ['nom', 'adresse', 'siret', 'email', 'telephone']:
            assert champ in ENTREPRISE
            assert len(ENTREPRISE[champ]) > 0


class TestConstantsStatuts:

    def test_statut_colors_complet(self):
        """Tous les statuts ont une couleur définie."""
        for statut in ['en_attente', 'accepte', 'refuse', 'contre_proposition']:
            assert statut in STATUT_COLORS

    def test_statut_emojis_complet(self):
        """Tous les statuts ont un emoji défini."""
        for statut in ['en_attente', 'accepte', 'refuse', 'contre_proposition']:
            assert statut in STATUT_EMOJIS

    def test_get_statut_emoji_connu(self):
        assert get_statut_emoji('accepte') == ''
        assert get_statut_emoji('refuse') == ''

    def test_get_statut_emoji_inconnu(self):
        """Un statut inconnu retourne l'emoji par défaut."""
        assert get_statut_emoji('inexistant') == ''

    def test_get_statut_color_connu(self):
        assert get_statut_color('accepte') == '#27ae60'

    def test_get_statut_color_inconnu(self):
        """Un statut inconnu retourne la couleur par défaut."""
        assert get_statut_color('inexistant') == '#95a5a6'

    def test_role_colors(self):
        """Les rôles acheteur et vendeur ont une couleur."""
        assert 'acheteur' in ROLE_COLORS
        assert 'vendeur' in ROLE_COLORS
