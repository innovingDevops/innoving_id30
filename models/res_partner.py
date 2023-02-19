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

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'activity'



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
    name = fields.Char(string="Nom (Activité principale) (*)")
    activity_birthday = fields.Char(string="Date de création activité (*)")
    street = fields.Char(string="Rue / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    street3 = fields.Char(string="Rue 2 / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    city = fields.Char(string="Ville / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    activite_type_id = fields.Char(string="Type d'activité")
    regime_fiscale = fields.Char(string="Régime fiscale")
    chiffre_affaire_taxable = fields.Char(string="CA déclaré (*)")
    min_ca = fields.Char(string="CA min")
    max_ca = fields.Char(string="CA max")
    secteur_id = fields.Char(string="Secteur d'activité (*)")
    forme_activite = fields.Char(string="Forme activité")
    zone_id = fields.Char(string="Zone")
    type_taxe = fields.Char(string="Type de taxe (*)")
    cga = fields.Char(string="CGA")
    date_adhesion = fields.Char(string="Date adhésion")
    ref_cga = fields.Char(string="N° Adhésion CGA")
    periode_imposition = fields.Char(string="Période d'imposition")
    taux_imposition = fields.Char(string="Indice d'imposition")
    taille_activite = fields.Char(string="Taille de l'activité")
    date_debut_exploitation = fields.Char(string="C13: Date de debut d'exploitation:(Mois/Année) (*)")

    #rubrique INS
    ciap = fields.Char(string="C14.a: Codification CIAP(réserver à l'INS) (activité principale)")
    longueur = fields.Char(string="Longueur ODP")
    largeur = fields.Char(string="Largeur")
    odp = fields.Char(string="Surface ODP")
    baux_loyer = fields.Char(string="Baux à loyer")
    pub_longueur = fields.Char(string="Longueur Peinte")
    pub_largeur = fields.Char(string="Largeur Peinte")
    pub_en_mettre_carre = fields.Char(string="PUB Peinte en m²")
    pub_longueur_2 = fields.Char(string="Longueur Enseigne")
    pub_largeur_2 = fields.Char(string="Largeur Enseigne")
    pub_en_mettre_carre_2 = fields.Char(string="PUB Enseigne en m²")
    image = fields.Binary(string="Image (*)")
    partner_latitude = fields.Char(string="Lat")
    partner_longitude = fields.Char(string="Long")
    idu_cepici = fields.Selection(string="C16: Votre entreprise dispose t-elle d'un numéro d'identification unique(IDU) du CEPICI ?", selection=[('oui', 'oui'), ('non', 'non')])
    idu_communicable = fields.Selection(string="Pouvez-vous nous donner ce numéro IDU?", selection=[('oui', 'oui'), ('non', 'non')])
    numero_idu = fields.Char(string="C16.a: Si oui, donner ce numéro IDU")
    numero_idu = fields.Integer(string="Saisir les 13 chiffres de l'IDU")
    lettre_fin_idu = fields.Char(string="Saisir la lettre de fin de l'IDU")
    autre_type_activite = fields.Char(string="C14b Autre type d'activité réalisée dans ce local ?")
    activicte_2 = fields.Char(string="Autre activité secondaire?")

    #rubrique Régime sociale
    etat_activite = fields.Char(string="C21 : Quel est l’état d’activité de l'entreprise ?")
    forme_juridique = fields.Char(string="C22: Quelle est la forme juridique de votre entreprise ?")
    autre_forme_juridique = fields.Char(string="C22.a: Autre forme juridique à préciser")
    capital_en_action = fields.Selection(string="C23: Votre entreprise est-elle majoritairement (Plus de 50%) à capitaux:", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    name_actionnaire = fields.Char(string="Nom et prénoms ou raison sociale de l'actionnaire")
    type_actionnaire = fields.Selection(string="L'actionnaire est-il une personne physique?", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    sexe_actionnaire = fields.Char(string="Si personne physique, précisez le sexe de l'actionnaire")
    nationalite_actionnaire = fields.Char(string="Quelle est la nationalité de l'actionnaire?")
    montant_action = fields.Char(string="Montant de l'action de l'actionnaire")
    part_sociale_actionnaire = fields.Char(string="Part sociale(en %) de l'actionnaire")
    autre_actionnaire = fields.Char(string="Autre actionnaire?")
    ca_ht_n_1 = fields.Char(string="D1.b21: Quel est le montant de votre chiffre d’affaires hors taxes en 2021 ?")
    ca_ht_n_2 = fields.Char(string="D1.b20: Quel est le montant de votre chiffre d’affaires hors taxes en 2020 ?")
    ca_ht_n_3 = fields.Char(string="D1.b19: Quel est le montant de votre chiffre d’affaires hors taxes en 2019 ?")
    valeur_ajoute_brute_n_1 = fields.Char(string="D1.c21: Quel est le montant de votre valeur ajoutée brute en 2021 ?")
    valeur_ajoute_brute_n_2 = fields.Char(string="D1.c20: Quel est le montant de votre valeur ajoutée brute en 2020 ?")
    valeur_ajoute_brute_n_3 = fields.Char(string="D1.c19: Quel est le montant de votre valeur ajoutée brute en 2019 ?")
    export_produit = fields.Selection(string="D2: Exportez-vous en partie ou en totalité vos produits/services ?", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    valeur_export_n_1 = fields.Char(string="D2.a21: Si oui, donnez la valeur de vos exportations en 2021")
    valeur_export_n_2 = fields.Char(string="D2.a20: Si oui, donnez la valeur de vos exportations en 2020")
    valeur_export_n_3 = fields.Char(string="D2.a19: Si oui, donnez la valeur de vos exportations en 2019")

    #rubrique : 19 contrainte  par ordre d'importance
    manque_personnel_qualifie = fields.Char(string="a: Insuffisance de personnel qualifié")
    cout_eleve_main_oeuvre = fields.Char(string="b: Coût élevé de la main d'œuvre")
    formalite_administrative_contraignante = fields.Char(string="c: Formalités administratives contraignantes")
    taxe_impot_eleve = fields.Char(string="d: Taxes et impôts trop élevés")
    cout_tranport_eleve = fields.Char(string="e: Coût du transport élevé (FRET)")
    mauvais_etat_infrastructure = fields.Char(string="f: Mauvais état des infrastructures routières")
    difficulte_approvisionnement_matiere_premiere = fields.Char(string="g: Difficultés d'approvisionnement en matières premières et autres intrants (quantité et qualité)")
    procedure_contentieux = fields.Char(string="h: Lourdeurs des procédures de règlement des contentieux")
    ecoulement_production = fields.Char(string="i: Difficultés d'écoulement de la production/insuffisance de débouchés")
    acces_au_technologie = fields.Char(string="j: Manque/Faible accès aux technologies spécialisées")
    manque_machine = fields.Char(string="k : Manque de machines et pièces de rechange")
    manque_expertise_technique = fields.Char(string="l: Manque d’expertise technique (maintenance machines)")
    manque_local_adapte = fields.Char(string="m: Manque de local adapté/terrain")
    acces_commande_public = fields.Char(string="n: Difficultés d'accès à la commande publique")
    acces_strucutre_appui = fields.Char(string="o: Accès limité aux structures d'appui aux entreprises")
    acces_credit_bancaire = fields.Char(string="p: Difficultés d'accès au crédit (Banque et Microfinance)")
    approvisionnement_energie = fields.Char(string="q: Difficultés d'approvisionnement en énergie")
    concurrence_deloyale = fields.Char(string="r: Concurrence déloyale")
    corruption = fields.Char(string="s: Corruption (racket, pot de vins, etc.)")
    autre_contrainte = fields.Char(string="t. Autre contrainte (à préciser)")
    aucune_contrainte = fields.Boolean(string="u. Aucune contrainte")



