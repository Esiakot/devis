# ──────────────────────────────────────────────────────────────────────────────
# tests/conftest.py — Fixtures partagées pour pytest
# ──────────────────────────────────────────────────────────────────────────────
import os
import sys
import pytest

# Ajouter la racine du projet au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.db_manager import DatabaseManager


@pytest.fixture
def db(tmp_path):
    """Crée une base de données de test temporaire (détruite après chaque test)."""
    db_file = str(tmp_path / "test.db")
    os.makedirs(os.path.join(tmp_path, "data"), exist_ok=True)
    # DatabaseManager attend db_name et construit le chemin dans data/
    # On monkey-patch Database pour pointer vers tmp_path
    from src.models.database import Database
    original_init = Database.__init__

    def patched_init(self, db_name="test.db"):
        self.db_path = db_file
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.create_tables()
        self.add_demo_data()

    Database.__init__ = patched_init
    manager = DatabaseManager("test.db")
    yield manager
    Database.__init__ = original_init
