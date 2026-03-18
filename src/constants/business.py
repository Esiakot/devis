# ──────────────────────────────────────────────────────────────────────────────
# src/constants/business.py — Constantes métier
# ──────────────────────────────────────────────────────────────────────────────
# Regroupe les paramètres financiers (taux de TVA, limite de poids, validité
# des devis), les paramètres applicatifs (intervalle de rafraîchissement),
# les informations de l'entreprise utilisées dans les PDF (nom, adresse,
# SIRET, etc.) et les conditions générales de vente.
# ──────────────────────────────────────────────────────────────────────────────

# --- Paramètres métier ---
TVA_RATE = 0.20  # 20%
POIDS_LIMITE_POURCENTAGE = 0.85  # 85% de la charge max
DEVIS_VALIDITE_JOURS = 30

# --- Paramètres applicatifs ---
AUTO_REFRESH_MS = 10000  # Intervalle de rafraîchissement automatique (ms)

# --- Informations entreprise (utilisées dans les PDF) ---
ENTREPRISE = {
    'nom': "Votre Entreprise SAS",
    'adresse': "Zone Industrielle\n1234 Avenue de l'Innovation\n75000 PARIS, France",
    'telephone': "+33 1 XX XX XX XX",
    'email': "contact@entreprise.fr",
    'siret': "XXX XXX XXX XXXXX",
    'tva_intra': "FRXX XXXXXXXXX",
    'capital': "XXX XXX",
    'rcs': "Paris XXX XXX XXX",
}

# --- Conditions générales (PDF) ---
CONDITIONS_GENERALES = [
    f"- Validité du devis: {DEVIS_VALIDITE_JOURS} jours à compter de la date d'émission",
    "- Délai de livraison: À définir selon disponibilité (généralement 8-12 semaines)",
    "- Conditions de paiement: 30% à la commande, 70% à la livraison",
    "- Garantie: 2 ans pièces et main d'oeuvre",
    "- Installation et formation: Sur devis séparé",
    "- Les prix s'entendent départ usine, hors frais de transport et d'installation",
]
