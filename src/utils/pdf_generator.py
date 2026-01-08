# -*- coding: utf-8 -*-
"""
Générateur PDF professionnel pour devis
Design moderne avec tableaux et mise en page soignée
"""

from fpdf import FPDF
import os
import datetime


class DevisPDF(FPDF):
    """PDF personnalisé avec en-tête et pied de page professionnels."""
    
    # Couleurs entreprise
    BLEU_FONCE = (41, 128, 185)
    BLEU_CLAIR = (52, 152, 219)
    GRIS_FONCE = (44, 62, 80)
    GRIS_CLAIR = (236, 240, 241)
    BLANC = (255, 255, 255)
    ROUGE = (231, 76, 60)
    VERT = (39, 174, 96)
    
    def __init__(self, numero_affaire, version, client_nom="", base_path=None):
        super().__init__()
        self.numero_affaire = numero_affaire
        self.version = version
        self.client_nom = client_nom
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.set_auto_page_break(auto=True, margin=25)
        
    def header(self):
        """En-tête professionnel avec logo et infos entreprise."""
        # Logo - chercher à plusieurs endroits possibles
        logo_paths = [
            os.path.join(self.base_path, "assets", "logo.jpg"),
            os.path.join(self.base_path, "assets", "logo.png"),
            os.path.join(os.path.dirname(self.base_path), "assets", "logo.jpg"),
        ]
        
        logo_found = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, 10, 8, 40)
                    logo_found = True
                    break
                except:
                    pass
        
        if not logo_found:
            # Logo texte si pas d'image
            self.set_font("Arial", "B", 20)
            self.set_text_color(*self.BLEU_FONCE)
            self.cell(50, 15, "ENTREPRISE", ln=False)
        
        # Infos entreprise à droite
        self.set_font("Arial", "", 8)
        self.set_text_color(*self.GRIS_FONCE)
        self.set_xy(120, 10)
        self.multi_cell(80, 4, 
            "Votre Entreprise SAS\n"
            "Zone Industrielle\n"
            "1234 Avenue de l'Innovation\n"
            "75000 PARIS, France\n"
            "Tel: +33 1 XX XX XX XX\n"
            "Email: contact@entreprise.fr\n"
            "SIRET: XXX XXX XXX XXXXX\n"
            "TVA: FRXX XXXXXXXXX", align="R")
        
        # Ligne de séparation
        self.set_draw_color(*self.BLEU_FONCE)
        self.set_line_width(0.5)
        self.line(10, 45, 200, 45)
        self.ln(40)
        
    def footer(self):
        """Pied de page avec numéro de page et mentions légales."""
        self.set_y(-20)
        self.set_draw_color(*self.BLEU_FONCE)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        
        self.set_font("Arial", "I", 7)
        self.set_text_color(*self.GRIS_FONCE)
        self.ln(3)
        self.cell(0, 4, "Votre Entreprise SAS - Capital XXX XXX EUR - RCS Paris XXX XXX XXX", align="C", ln=True)
        self.cell(0, 4, f"Page {self.page_no()}/{{nb}} | Devis {self.numero_affaire}-V{self.version} | Validite: 30 jours", align="C")
        
    def titre_devis(self):
        """Bloc titre du devis."""
        # Bandeau coloré
        self.set_fill_color(*self.BLEU_FONCE)
        self.rect(10, 50, 190, 18, 'F')
        
        self.set_xy(10, 52)
        self.set_font("Arial", "B", 18)
        self.set_text_color(*self.BLANC)
        self.cell(95, 14, "DEVIS", align="L")
        
        self.set_font("Arial", "B", 14)
        self.cell(95, 14, f"N° {self.numero_affaire}-V{self.version}", align="R")
        
        self.ln(25)
        
    def bloc_client(self, client_nom, date_str=None):
        """Bloc informations client."""
        if date_str is None:
            date_str = datetime.datetime.now().strftime('%d/%m/%Y')
            
        # Cadre client
        self.set_fill_color(*self.GRIS_CLAIR)
        self.rect(10, self.get_y(), 90, 30, 'F')
        
        # Cadre date
        self.rect(110, self.get_y(), 90, 30, 'F')
        
        y_start = self.get_y()
        
        # Client
        self.set_xy(12, y_start + 2)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.BLEU_FONCE)
        self.cell(0, 6, "CLIENT", ln=True)
        
        self.set_x(12)
        self.set_font("Arial", "", 10)
        self.set_text_color(*self.GRIS_FONCE)
        self.multi_cell(85, 5, client_nom or "Client non specifie")
        
        # Date et validité
        self.set_xy(112, y_start + 2)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*self.BLEU_FONCE)
        self.cell(0, 6, "DATE & VALIDITE", ln=True)
        
        self.set_x(112)
        self.set_font("Arial", "", 10)
        self.set_text_color(*self.GRIS_FONCE)
        self.cell(0, 5, f"Date: {date_str}", ln=True)
        self.set_x(112)
        self.cell(0, 5, f"Valide jusqu'au: {(datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%d/%m/%Y')}")
        
        self.set_y(y_start + 35)
        
    def tableau_produit(self, prod_nom, quantite, prix_unitaire, options_standard, options_perso):
        """
        Tableau pour un produit avec ses options.
        Exclut les options refusées (statut_vendeur='refuse' ou statut_acheteur='refuse').
        """
        # Vérifier si on a besoin d'une nouvelle page
        if self.get_y() > 220:
            self.add_page()
        
        # Titre produit
        self.set_fill_color(*self.BLEU_CLAIR)
        self.set_text_color(*self.BLANC)
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, f"  {prod_nom}", fill=True, ln=True)
        
        # En-tête du tableau
        self.set_fill_color(*self.GRIS_FONCE)
        self.set_text_color(*self.BLANC)
        self.set_font("Arial", "B", 9)
        
        col_widths = [90, 25, 25, 25, 25]  # Description, Qté, P.U. HT, Statut, Total HT
        headers = ["Description", "Qte", "P.U. HT", "Statut", "Total HT"]
        
        for i, (w, h) in enumerate(zip(col_widths, headers)):
            self.cell(w, 7, h, border=1, fill=True, align="C")
        self.ln()
        
        # Style pour les lignes
        self.set_font("Arial", "", 9)
        self.set_text_color(*self.GRIS_FONCE)
        
        total_prod = 0
        row_alt = False
        
        # Ligne produit de base
        self.set_fill_color(245, 247, 250)
        self.cell(col_widths[0], 6, f"  {prod_nom} (base)", border=1, fill=True)
        self.cell(col_widths[1], 6, str(quantite), border=1, fill=True, align="C")
        self.cell(col_widths[2], 6, f"{prix_unitaire:.2f} EUR", border=1, fill=True, align="R")
        self.cell(col_widths[3], 6, "Inclus", border=1, fill=True, align="C")
        sous_total = prix_unitaire * quantite
        total_prod += sous_total
        self.cell(col_widths[4], 6, f"{sous_total:.2f} EUR", border=1, fill=True, align="R")
        self.ln()
        
        # Options standard (exclure les refusées)
        for opt in options_standard:
            statut_v = opt.get('statut_vendeur', 'en_attente')
            statut_a = opt.get('statut_acheteur', 'en_attente')
            
            # Exclure les options refusées
            if statut_v == 'refuse' or statut_a == 'refuse':
                continue
                
            row_alt = not row_alt
            if row_alt:
                self.set_fill_color(250, 252, 255)
            else:
                self.set_fill_color(255, 255, 255)
            
            # Déterminer le prix final
            if statut_v == 'contre_proposition' and opt.get('prix_propose'):
                prix_final = opt['prix_propose']
            else:
                prix_final = opt['prix']
            
            # Déterminer le statut affiché
            if statut_v == 'accepte' or statut_a == 'accepte':
                statut_display = "Accepte"
                self.set_text_color(*self.VERT)
            elif statut_v == 'contre_proposition':
                if statut_a == 'accepte':
                    statut_display = "Accepte"
                    self.set_text_color(*self.VERT)
                else:
                    statut_display = "Negocie"
                    self.set_text_color(243, 156, 18)  # Orange
            else:
                statut_display = "En cours"
                self.set_text_color(149, 165, 166)  # Gris
            
            self.set_text_color(*self.GRIS_FONCE)
            self.cell(col_widths[0], 6, f"  + {opt['nom']}", border=1, fill=True)
            self.cell(col_widths[1], 6, str(quantite), border=1, fill=True, align="C")
            self.cell(col_widths[2], 6, f"{prix_final:.2f} EUR", border=1, fill=True, align="R")
            
            # Couleur du statut
            if statut_display == "Accepte":
                self.set_text_color(*self.VERT)
            elif statut_display == "Negocie":
                self.set_text_color(243, 156, 18)
            else:
                self.set_text_color(149, 165, 166)
            self.cell(col_widths[3], 6, statut_display, border=1, fill=True, align="C")
            
            self.set_text_color(*self.GRIS_FONCE)
            sous_total = prix_final * quantite
            total_prod += sous_total
            self.cell(col_widths[4], 6, f"{sous_total:.2f} EUR", border=1, fill=True, align="R")
            self.ln()
        
        # Options personnalisées (exclure les refusées)
        for opt in options_perso:
            statut_v = opt.get('statut_vendeur', 'en_attente')
            statut_a = opt.get('statut_acheteur', 'en_attente')
            
            # Exclure les options refusées
            if statut_v == 'refuse' or statut_a == 'refuse':
                continue
                
            row_alt = not row_alt
            if row_alt:
                self.set_fill_color(255, 250, 245)  # Teinte légère pour perso
            else:
                self.set_fill_color(255, 255, 250)
            
            # Déterminer le prix final
            if statut_v == 'contre_proposition' and opt.get('prix_propose'):
                prix_final = opt['prix_propose']
            elif statut_v == 'accepte' and opt.get('prix_demande'):
                prix_final = opt['prix_demande']
            else:
                prix_final = opt.get('prix_propose') or opt.get('prix_demande') or 0
            
            # Déterminer le statut affiché
            if statut_v == 'accepte' or statut_a == 'accepte':
                statut_display = "Accepte"
            elif statut_v == 'contre_proposition':
                if statut_a == 'accepte':
                    statut_display = "Accepte"
                else:
                    statut_display = "Negocie"
            else:
                statut_display = "En cours"
            
            desc = opt['description'][:40] + "..." if len(opt['description']) > 40 else opt['description']
            
            self.set_text_color(*self.GRIS_FONCE)
            self.set_font("Arial", "I", 9)
            self.cell(col_widths[0], 6, f"  * {desc}", border=1, fill=True)
            self.set_font("Arial", "", 9)
            self.cell(col_widths[1], 6, str(quantite), border=1, fill=True, align="C")
            self.cell(col_widths[2], 6, f"{prix_final:.2f} EUR", border=1, fill=True, align="R")
            
            # Couleur du statut
            if statut_display == "Accepte":
                self.set_text_color(*self.VERT)
            elif statut_display == "Negocie":
                self.set_text_color(243, 156, 18)
            else:
                self.set_text_color(149, 165, 166)
            self.cell(col_widths[3], 6, statut_display, border=1, fill=True, align="C")
            
            self.set_text_color(*self.GRIS_FONCE)
            sous_total = prix_final * quantite
            total_prod += sous_total
            self.cell(col_widths[4], 6, f"{sous_total:.2f} EUR", border=1, fill=True, align="R")
            self.ln()
        
        # Sous-total produit
        self.set_fill_color(*self.BLEU_CLAIR)
        self.set_text_color(*self.BLANC)
        self.set_font("Arial", "B", 9)
        self.cell(sum(col_widths[:4]), 7, f"Sous-total {prod_nom} HT", border=1, fill=True, align="R")
        self.cell(col_widths[4], 7, f"{total_prod:.2f} EUR", border=1, fill=True, align="R")
        self.ln(12)
        
        return total_prod
        
    def bloc_total(self, total_ht):
        """Bloc récapitulatif avec total HT, TVA, TTC."""
        tva = total_ht * 0.20
        total_ttc = total_ht + tva
        
        # Position à droite
        x_start = 110
        width = 90
        
        self.set_y(self.get_y() + 5)
        
        # Cadre récapitulatif
        y_start = self.get_y()
        self.set_fill_color(*self.GRIS_CLAIR)
        self.rect(x_start, y_start, width, 35, 'F')
        
        self.set_xy(x_start + 5, y_start + 3)
        self.set_font("Arial", "", 10)
        self.set_text_color(*self.GRIS_FONCE)
        
        # Total HT
        self.cell(50, 7, "Total HT:", align="L")
        self.cell(30, 7, f"{total_ht:.2f} EUR", align="R", ln=True)
        
        # TVA
        self.set_x(x_start + 5)
        self.cell(50, 7, "TVA (20%):", align="L")
        self.cell(30, 7, f"{tva:.2f} EUR", align="R", ln=True)
        
        # Ligne
        self.set_x(x_start + 5)
        self.set_draw_color(*self.GRIS_FONCE)
        self.line(x_start + 5, self.get_y(), x_start + width - 5, self.get_y())
        self.ln(2)
        
        # Total TTC
        self.set_x(x_start + 5)
        self.set_font("Arial", "B", 12)
        self.set_text_color(*self.BLEU_FONCE)
        self.cell(50, 10, "TOTAL TTC:", align="L")
        self.cell(30, 10, f"{total_ttc:.2f} EUR", align="R")
        
        self.ln(20)
        
    def conditions_generales(self):
        """Conditions générales de vente."""
        if self.get_y() > 240:
            self.add_page()
            
        self.set_font("Arial", "B", 9)
        self.set_text_color(*self.BLEU_FONCE)
        self.cell(0, 6, "CONDITIONS GENERALES", ln=True)
        
        self.set_font("Arial", "", 8)
        self.set_text_color(*self.GRIS_FONCE)
        
        conditions = [
            "- Validite du devis: 30 jours a compter de la date d'emission",
            "- Delai de livraison: A definir selon disponibilite (generalement 8-12 semaines)",
            "- Conditions de paiement: 30% a la commande, 70% a la livraison",
            "- Garantie: 2 ans pieces et main d'oeuvre",
            "- Installation et formation: Sur devis separé",
            "- Les prix s'entendent depart usine, hors frais de transport et d'installation"
        ]
        
        for cond in conditions:
            self.cell(0, 4, cond, ln=True)
            
        self.ln(10)
        
    def signature(self):
        """Zone de signature."""
        if self.get_y() > 250:
            self.add_page()
            
        self.set_font("Arial", "B", 9)
        self.set_text_color(*self.BLEU_FONCE)
        self.cell(95, 6, "Pour le fournisseur:", ln=False)
        self.cell(95, 6, "Bon pour accord (le client):", ln=True)
        
        self.ln(5)
        
        # Cadres signature
        self.set_draw_color(*self.GRIS_FONCE)
        self.rect(10, self.get_y(), 90, 25)
        self.rect(105, self.get_y(), 90, 25)
        
        self.set_font("Arial", "", 8)
        self.set_text_color(*self.GRIS_FONCE)
        self.set_xy(12, self.get_y() + 2)
        self.cell(0, 4, "Date et signature:")
        
        self.set_xy(107, self.get_y())
        self.cell(0, 4, "Date, signature et cachet:")


def generer_devis_pdf(db, devis_id, client_nom="", output_dir=None):
    """
    Génère un PDF professionnel pour un devis.
    
    Args:
        db: Instance DatabaseManager
        devis_id: ID du devis
        client_nom: Nom du client (optionnel)
        output_dir: Dossier de sortie (optionnel)
    
    Returns:
        str: Chemin du fichier PDF généré
    """
    # Récupérer les infos
    info = db.get_devis_info(devis_id)
    if not info:
        return None
    
    numero_affaire = info[5]
    version = info[2]
    
    data = db.get_options_devis_detail(devis_id)
    
    # Déterminer le chemin de base (racine du projet)
    if output_dir:
        base_path = os.path.dirname(output_dir)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # Créer le PDF
    pdf = DevisPDF(numero_affaire, version, client_nom, base_path)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre
    pdf.titre_devis()
    
    # Bloc client
    pdf.bloc_client(client_nom)
    
    # Tableaux produits
    total_general = 0
    for prod_data in data['produits']:
        total_prod = pdf.tableau_produit(
            prod_data['nom'],
            prod_data['quantite'],
            prod_data['prix_unitaire'],
            prod_data['options_standard'],
            prod_data['options_perso']
        )
        total_general += total_prod
    
    # Total
    pdf.bloc_total(total_general)
    
    # Conditions
    pdf.conditions_generales()
    
    # Signature
    pdf.signature()
    
    # Sauvegarder
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   "generated_devis")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"Devis_{numero_affaire}_V{version}.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)
    
    return filepath
