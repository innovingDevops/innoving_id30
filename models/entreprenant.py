# -*- coding: utf-8 -*-

import base64
import datetime
import hashlib
import pytz
import threading

from email.utils import formataddr
from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import browse_record
#from datetime import datetime
#from datetime import date

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import html_translate

from datetime import date, datetime, timedelta
import time
#from xlwt.antlr import ifelse
from dateutil.relativedelta import relativedelta
import string
#from odoo.http import request


class InnovingInnoving(models.Model):
    _name = "innoving.entreprenant"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des entreprenants"
    _order = "name asc"
    
    def _get_default_user_id(self):
        return self.env.uid

    def _creat_year(self):
        created_year = datetime.today().year
        return created_year
    
    
    def _creat_month(self):
        created_month = datetime.today().month
        return created_month
    
    
    '''@api.depends('activite_ids')
    def _compute_activity_number(self):
        nb = 0
        for line in self:
            nb = len(line.activite_ids)
            line.update({'activity_number': nb})'''
        
    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'CI')], limit=1)
        return country
    
    active = fields.Boolean(string='Actif',default=True, track_visibility="always")
    name = fields.Char(string="Nom / Nom Enseigne / Raison sociale", track_visibility="always")
    code = fields.Char(string="Code", track_visibility="always")
    user_id = fields.Many2one("res.users",string="Agent",default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout",default=lambda self: fields.datetime.now(), track_visibility="always")
    ref = fields.Char(string='Référence', track_visibility='always')
    telephone = fields.Char(string='Téléphone', track_visibility='always')
    adresse = fields.Char(string='Adresse Entreprenant')
    email = fields.Char(string='Email')
    nature_piece = fields.Selection(string="Nature Pièce", selection=[
        ('CNI', 'CNI'),
        ('PASSEPORT', 'PASSEPORT'),
        ('AUTRE', 'AUTRE')
        ])
    cni = fields.Char(string='Numéro Pièce')
    image = fields.Binary(string='Image', attachment=True,track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirmé'),
        ('valid', 'Validé'),
        ('cancel', 'Annulé/Rejeté')
        ], track_visibility='always', default='draft')
    
    date_confirm = fields.Date('Date confirmation')
    date_valid = fields.Date('Date validation')
    creat_year = fields.Char(string="Année de création", default=_creat_year)
    creat_month = fields.Char(string="Mois de création", default=_creat_month)
    activity_number = fields.Integer(string="Nbre d'activité",compute='_compute_activity_number',store=True)
    amount_total = fields.Float(string='Montant à payer / an')
    #transaction_ids = fields.One2many('colibri.transaction', 'contribuable_id', string='Transaction', track_visibility='always')
    amount_paye = fields.Float(string='Montant payé')
    sexe = fields.Selection(string="Genre", selection=[
        ('masculin', 'Masculin'),
        ('feminin', 'Feminin')
        ])
    birthday = fields.Date('Date de naissance')
    country_id = fields.Many2one('res.country', default=_get_default_country)
    lieu_naissance = fields.Char(string="Lieu de naissance")
    photo_id = fields.Binary(string='Image scanner', attachment=True)
    photo_id_name = fields.Char(string="Nom image scanner")
    url_server_photo_id = fields.Char(string="Serveur image scanner")
    commune_identification = fields.Char(string="Com. d'identification")
    profession = fields.Char(string="Profession")
    regime_fiscale = fields.Selection(string="Régime fiscale", selection=[
        ('TCE', 'TCE'),
        ('TEE', 'TEE'),
        ('IME', 'IME'),
        ('RSI', 'RSI'),
        ('RNI', 'RNI')])
    rccm = fields.Char(string='RCCM')
    terminal = fields.Selection(string="Type de terminal", selection=[
        ('Smartphone', 'Smartphone'),
        ('Feature phone', 'Feature phone')
        ])
    date_validite_piece = fields.Date('Date de validité ')
    biometrie = fields.Text(string='Biométrie')
    #activite_ids = fields.One2many('res.partner', 'entreprenant_id', string='Activité', track_visibility='always')
    
    
    sous_prefecture = fields.Char(string="Sous Prefecture")
    commune = fields.Char(string="Commune")
    milieu_implantation = fields.Char(string="Milieu implantation")
    district = fields.Selection(string="District", selection=[
        ('Abidjan', 'Abidjan'),
        ('Yamoussoukro', 'Yamoussoukro')
        ] , default='draft', track_visibility="always")
    region_id = fields.Many2one("innoving.region",string="Région",track_visibility="always")
    departement_id = fields.Many2one("innoving.departement",string="Département",track_visibility="always")
    nom_repondant = fields.Char(string=" Nom et prénoms repondant")
    fonction_repondant = fields.Char(string="Fonction repondant")
    contact_1_repondant = fields.Char(string="contact repondant 1")
    contact_2_repondant = fields.Char(string="contact repondant 2")
    email_repondant = fields.Char(string="E-mail repondant")
    nom_prenom_dirigeant = fields.Char(string="Non et prenoms dirigeant")
    email_dirigeant = fields.Char(string="E-mail dirigeant")
    qualite_dirigeant = fields.Char(string="Qualité dirigeant")
    autre_qualite = fields.Char(string="Autres qualité")
    
    sigle_entreprise = fields.Char(string="Sigle entréprise")
    telephone_fixe_2_entreprise = fields.Char(string="Tel fixe entreprise")
    telephone_portable_1_entreprise = fields.Char(string="Tel 1 entréprise")
    telephone_portable_2_entreprise = fields.Char(string="Tel 2 entréprise")
    faxe_entreprise = fields.Char(string="Fax entréprise")
    email_entreprise = fields.Char(string="E-mail entréprise")
    site_web_entreprise = fields.Char(string="Site web entréprise")
    adresse_geographique_entreprise = fields.Char(string="Adresse géographie entréprise")
    boite_postale_entreprise = fields.Char(string="Boite postale entréprise")



    _sql_constraints = [
        ("telephone_uniq", "unique(telephone)", "Le numéro de téléphone de l'entreprenant doit être unique !"),
        ("cni_uniq", "unique(cni)", "Le numéro de la CNI de l'entreprenant doit être unique !"),
    ]

    
    @api.multi
    def button_draft(self, force=False):
        self.write({'state': 'draft'})
        
    @api.multi
    def button_confirm(self, force=False):
        self.write({'state': 'confirm', 'date_confirm': fields.Date.context_today(self)})
        
    @api.multi
    def button_done(self, force=False):
        self.write({'state': 'done', 'date_done': fields.Date.context_today(self)})
        
        
    @api.multi
    def button_cancel(self, force=False):
        self.write({'state': 'cancel','date_cancel': fields.Date.context_today(self)})
        
    