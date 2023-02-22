# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import collections
import datetime
import hashlib
import pytz
import threading
import time
import math
import re

import requests
from lxml import etree
from werkzeug import urls

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from odoo.tools import pycompat
from datetime import datetime
from datetime import date

from odoo.addons import decimal_precision as dp


class Partner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'
    _order = "name desc"
    
    def _get_default_user_ids(self):
        return self.env.uid
    
    
    @api.model
    def _get_default_country(self):

        country = self.env['res.country'].search([('code', '=', 'CI')], limit=1)

        return country
            
    def _get_default_currency(self):

        return self.env.user.company_id.currency_id
    
    @api.multi
    def _get_default_ref(self):
        if self.ref == False or self.name == "/":
            seq = self.env['ir.sequence'].next_by_code('innoving.activite')
        return seq 

    def _fiscal_year(self):
        date_du_jour = date.today()
        fiscal_year_id =  self.env['account.fiscal.year'].search([('date_from', '<', date_du_jour), ('date_to', '>', date_du_jour)])
        #raise UserError(_('%s') % (fiscal_year_id))      
        return fiscal_year_id

    @api.depends('longueur', 'largeur', 'entreprenant_id.state')
    def _compute_odp(self):
        for record in self:
            record.update({'odp': record.longueur * record.largeur})


    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'activity'

    @api.depends('pub_longueur', 'pub_largeur', 'entreprenant_id.state', 'pub_largeur_2', 'pub_longueur_2')
    def _compute_pub(self):
        for record in self:
            record.update({'pub_en_mettre_carre': record.pub_longueur * record.pub_largeur,
                           'pub_en_mettre_carre_2': record.pub_longueur_2 * record.pub_largeur_2})

    entreprenant_id = fields.Many2one('innoving.entreprenant', string="Entreprenant")
    ref = fields.Char(string='Reference', default=_get_default_ref)
    fiscal_year_id = fields.Many2one('account.fiscal.year', string="Année fisclale", default=_fiscal_year)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company'),
                                               ('activity', 'Activité')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    country_id = fields.Many2one('res.country', default=_get_default_country)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_default_currency,
                                  track_visibility='always')
    #nouveau champs
    #rubrique votre entreprise
    name = fields.Char(string="Nom (Activité principale)")
    activity_birthday = fields.Char(string="Date de création activité")
    street = fields.Char(string="Rue / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    street3 = fields.Char(string="Rue 2 / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    city = fields.Char(string="Ville / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    activite_type_id = fields.Many2one('innoving.type.activite', string="Activite")
    regime_fiscale = fields.Char(string="Régime fiscale")
    chiffre_affaire_taxable = fields.Char(string="CA déclaré")
    min_ca = fields.Char(string="CA min")
    max_ca = fields.Char(string="CA max")
    secteur_id = fields.Many2one('innoving.secteur.activite', string="Secteur d'activité")
    forme_activite = fields.Selection(string="Forme activité", selection=[
        ('AUTRE', 'AUTRE'),
        ('COMMERCE', 'COMMERCE'),
        ('SERVICE', 'SERVICE')], related='secteur_id.forme_activite')
    zone_id = fields.Char(string="Zone")
    type_taxe = fields.Selection(string="Type de taxe", selection=[
        ('FORFAITAIRE (PCA)', 'FORFAITAIRE (PCA)'),
        ('ETABISSEMENT DE NUIT (ETN)', 'ETABISSEMENT DE NUIT (ETN)'),
        ('ODP', 'ODP'),
        ('GROS ODP', 'GROS ODP'),
        ('TICKET MARCHE', 'TICKET MARCHE'),
        ('PUB', 'PUB')])
    cga = fields.Selection(string="CGA", selection=[
        ('Oui', 'Oui'),
        ('Non', 'Non')])
    date_adhesion = fields.Char(string="Date adhésion")
    ref_cga = fields.Char(string="N° Adhésion CGA")
    periode_imposition = fields.Selection(string="Période d'imposition", selection=[
        ('Jour', 'Jour'),
        ('Mois', 'Mois'),
        ('Bimestrielle', 'Bimestrielle'),
        ('Trimestrielle', 'Trimestrielle'),
        ('Semestrielle', 'Semestrielle'),
        ('Annuelle', 'Annuelle')])
    taux_imposition = fields.Float(string="Indice d'imposition")
    taille_activite = fields.Selection(string="Taille activité", selection=[
        ('Très petite', 'Très petite'),
        ('Petite', 'Petite'),
        ('Moyenne', 'Moyenne'),
        ('Grande', 'Grande'),
        ('DGI', 'DGI')])
    date_debut_exploitation = fields.Char(string="C13: Date de debut d'exploitation:(Mois/Année)")
    #rubrique INS
    ciap = fields.Char(string="C14.a: Codification CIAP(réserver à l'INS) (activité principale)")
    longueur = fields.Float(string="Longueur ODP")
    largeur = fields.Float(string="Largeur")
    odp = fields.Float(string='Surface ODP', compute='_compute_odp',  store=True)
    baux_loyer = baux_loyer = fields.Selection(string="Baux  à loyer", selection=[
        ('4000', '4 000 CFA'),
        ('7000', '7 000 CFA'),
        ('8400', '8 400 CFA'),
        ('10000', '10 000 CFA'),
        ('11200', '11 200 CFA'),
        ('14000', '14 000 CFA'),
        ('15000', '15 000 CFA'),
        ('16000', '16 000 CFA'),
        ('17000', '17 000 CFA'),
        ('17500', '17 500 CFA'),
        ('20000', '20 000 CFA'),
        ('25000', '25 000 CFA'),
        ('56000', '56 000 CFA'),
        ('70000', '70 000 CFA')])

    pub_longueur = fields.Char(string="Longueur Peinte")
    pub_largeur = fields.Char(string="Largeur Peinte")
    pub_en_mettre_carre = fields.Float(string='PUB peinte en m²', compute='_compute_pub', store=True)
    pub_longueur_2 = fields.Float(string="Longueur Enseigne")
    pub_largeur_2 = fields.Float(string="Largeur Enseigne")
    pub_en_mettre_carre_2 = fields.Float(string="PUB Enseigne en m²", compute='_compute_pub', store=True)
    image = fields.Binary(string="Image")
    partner_latitude = fields.Char(string="Lat")
    partner_longitude = fields.Char(string="Long")
    idu_cepici = fields.Selection(string="C16: Votre entreprise dispose t-elle d'un numéro d'identification unique(IDU) du CEPICI ?", selection=[('oui', 'oui'), ('non', 'non')])
    idu_communicable = fields.Selection(string="Pouvez-vous nous donner ce numéro IDU?", selection=[('oui', 'oui'), ('non', 'non')])
    numero_idu = fields.Char(string="C16.a: Si oui, donner ce numéro IDU")
    chiffre_idu = fields.Integer(string="Saisir les 13 chiffres de l'IDU")
    lettre_fin_idu = fields.Char(string="Saisir la lettre de fin de l'IDU")
    autre_type_activite = fields.Selection( string="Faites-vous une autre activite", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    activicte_2 = fields.Many2one('innoving.type.activite', string="Activite")

    #rubrique Régime sociale
    etat_activite = fields.Selection(string="C21 : Quel est l’état d’activité de l'entreprise ?" , selection=[
                                        ('1', 'Activité non encore démarrée'),
                                        ('2', 'En activité'),
                                        ('3', 'En veille ou en cessation momentanée'),
                                        ('4', 'Cessation totale d’activité')])

    forme_juridique = fields.Selection(string="C21 : Quel est l’état d’activité de l'entreprise ?", selection=[
                                        ('1', 'Société en Nom Collectif'),
                                        ('2', 'Société en Commandite Simple'),
                                        ('3', 'Société en Participations'),
                                        ('4', 'Société de fait'),
                                        ('5', 'Société à Responsabilité limitée (SARL)'),
                                        ('6', 'Société par Actions simplifiées (SAS)'),
                                        ('7', 'Entreprise individuelle (pers. physique)'),
                                        ('8', 'Société anonyme (SA)'),
                                        ('9', "Groupement d'Intérêt économique (GIE)"),
                                        ('10', 'Ets public industriel et commercial (EPIC)'),
                                        ('11', 'Autres(à préciser)')])
    autre_forme_juridique = fields.Char(string="C22.a: Autre forme juridique à préciser")
    capital_en_action = fields.Selection(string="C23: Votre entreprise est-elle majoritairement (Plus de 50%) à capitaux:", selection=[
                                        ('1', 'Public'),
                                        ('2', 'Privé'),
                                        ('3', 'Privé étranger')])

    name_actionnaire = fields.Char(string="Nom et prénoms ou raison sociale de l'actionnaire")
    type_actionnaire = fields.Selection(string="L'actionnaire est-il une personne physique?", selection=[('1', 'Oui'),('2', 'Non')])
    sexe_actionnaire = fields.Selection(string="Si personne physique, précisez le sexe de l'actionnaire",
                                        selection=[('1', 'Masculin'),('2', 'Feminin'),('3','Sans objet')])
    nationalite_actionnaire = fields.Char(string="Quelle est la nationalité de l'actionnaire?")
    montant_action = fields.Float(string="Montant de l'action de l'actionnaire")
    part_sociale_actionnaire = fields.Float(string="Part sociale(en %) de l'actionnaire")
    autre_actionnaire = fields.Char(string="Autre actionnaire?")
    ca_ht_n_1 = fields.Float(string="D1.b21: Quel est le montant de votre chiffre d’affaires hors taxes en 2021 ?")
    ca_ht_n_2 = fields.Float(string="D1.b20: Quel est le montant de votre chiffre d’affaires hors taxes en 2020 ?")
    ca_ht_n_3 = fields.Float(string="D1.b19: Quel est le montant de votre chiffre d’affaires hors taxes en 2019 ?")
    valeur_ajoute_brute_n_1 = fields.Float(string="D1.c21: Quel est le montant de votre valeur ajoutée brute en 2021 ?")
    valeur_ajoute_brute_n_2 = fields.Float(string="D1.c20: Quel est le montant de votre valeur ajoutée brute en 2020 ?")
    valeur_ajoute_brute_n_3 = fields.Float(string="D1.c19: Quel est le montant de votre valeur ajoutée brute en 2019 ?")
    export_produit = fields.Selection(string="D2: Exportez-vous en partie ou en totalité vos produits/services ?", selection=[('1', 'Oui'), ('2', 'Non')])
    valeur_export_n_1 = fields.Float(string="D2.a21: Si oui, donnez la valeur de vos exportations en 2021")
    valeur_export_n_2 = fields.Float(string="D2.a20: Si oui, donnez la valeur de vos exportations en 2020")
    valeur_export_n_3 = fields.Float(string="D2.a19: Si oui, donnez la valeur de vos exportations en 2019")

    #rubrique : 19 contrainte  par ordre d'importance
    manque_personnel_qualifie = fields.Selection(string="a: Insuffisance de personnel qualifié", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_eleve_main_oeuvre = fields.Selection(string="b: Coût élevé de la main d'œuvre", selection=[('1', 'Oui'), ('0', 'Non')])
    formalite_administrative_contraignante = fields.Selection(string=" c: Formalités administratives contraignantes ", selection=[('1', 'Oui'), ('0', 'Non')])
    taxe_impot_eleve = fields.Selection(string=" d: Taxes et impôts trop élevés ", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_tranport_eleve = fields.Selection(string=" e: Coût du transport élevé (FRET) ", selection=[('1', 'Oui'), ('0', 'Non')])
    mauvais_etat_infrastructure = fields.Selection(string=" f: Mauvais état des infrastructures routières ", selection=[('1', 'Oui'), ('0', 'Non')])
    difficulte_approvisionnement_matiere_premiere = fields.Selection(string="g: Difficultés d'approvisionnement en matières premières et autres intrants (quantité et qualité) ", selection=[('1', 'Oui'), ('0', 'Non')])
    procedure_contentieux = fields.Selection(string=" h: Lourdeurs des procédures de règlement des contentieux ", selection=[('1', 'Oui'), ('0', 'Non')])
    ecoulement_production = fields.Selection(string="i: Difficultés d'écoulement de la production/insuffisance de débouchés", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_au_technologie = fields.Selection(string="j: Manque/Faible accès aux technologies spécialisées", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_machine = fields.Selection(string="k: Manque de machines et pièces de rechange", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_expertise_technique = fields.Selection(string="l: Manque d’expertise technique (maintenance machines)", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_local_adapte = fields.Selection(string="m: Manque de local adapté/terrain", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_commande_public = fields.Selection(string="n: Difficultés d'accès à la commande publique", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_structure_appui = fields.Selection(string="o: Accès limité aux structures d'appui aux entreprises", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_credit_bancaire = fields.Selection(string="p: Difficultés d'accès au crédit (Banque et Microfinance)", selection=[('1', 'Oui'), ('0', 'Non')])
    approvisionnement_energie = fields.Selection(string="q: Difficultés d'approvisionnement en énergie", selection=[('1', 'Oui'), ('0', 'Non')])
    concurrence_deloyale = fields.Selection(string="r: Concurrence déloyale", selection=[('1', 'Oui'), ('0', 'Non')])
    corruption = fields.Selection(string="s: Corruption (racket, pot de vins, etc.)", selection=[('1', 'Oui'), ('0', 'Non')])
    autre_contrainte = fields.Selection(string="t Autre contrainte (à préciser)", selection=[('1', 'Oui'), ('0', 'Non')])
    precise_contrainte = fields.Char(string="u: Précisez la contrainte )")
    aucune_contrainte = fields.Selection(string="u. Aucune contrainte", selection=[('1', 'Oui'), ('0', 'Non')])











