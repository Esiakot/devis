# ──────────────────────────────────────────────────────────────────────────────
# src/models/repositories/produit_repo.py — Repository Produits
# ──────────────────────────────────────────────────────────────────────────────
# Accès en lecture au catalogue de produits et d'options. Fournit la liste des
# produits disponibles, les options associées à un produit donné (spécifiques
# et universelles) et la liste complète des options. Utilisé par les widgets
# de configuration de produits dans l'interface.
# ──────────────────────────────────────────────────────────────────────────────


class ProduitRepository:

    def __init__(self, get_connection):
        self._conn = get_connection

    def get_produits(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix_base, charge_max FROM produit ORDER BY nom")
        results = cursor.fetchall()
        conn.close()
        return results

    def get_options_pour_produit(self, produit_id):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT o.id, o.nom, o.prix, o.poids, o.universelle
            FROM option o
            LEFT JOIN produit_option po ON o.id = po.option_id
            WHERE o.universelle = 1 OR po.produit_id = ?
            ORDER BY o.universelle DESC, o.nom
        """, (produit_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def get_options(self):
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nom, prix, poids FROM option ORDER BY nom")
        results = cursor.fetchall()
        conn.close()
        return results
