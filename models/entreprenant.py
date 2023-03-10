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


class InnovingEntreprenant(models.Model):
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
    ref = fields.Char(string='R??f??rence', track_visibility='always')
    telephone = fields.Char(string='T??l??phone', track_visibility='always')
    adresse = fields.Char(string='Adresse Entreprenant')
    email = fields.Char(string='Email')
    nature_piece = fields.Selection(string="Nature Pi??ce", selection=[
        ('CNI', 'CNI'),
        ('PASSEPORT', 'PASSEPORT'),
        ('AUTRE', 'AUTRE')
        ])
    cni = fields.Char(string='Num??ro Pi??ce')
    image = fields.Binary(string='Image', attachment=True,track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirm??'),
        ('valid', 'Valid??'),
        ('cancel', 'Annul??/Rejet??')
        ], track_visibility='always', default='draft')
    
    date_confirm = fields.Date('Date confirmation')
    date_valid = fields.Date('Date validation')
    creat_year = fields.Char(string="Ann??e de cr??ation", default=_creat_year)
    creat_month = fields.Char(string="Mois de cr??ation", default=_creat_month)
    activity_number = fields.Integer(string="Nbre d'activit??",compute='_compute_activity_number',store=True)
    amount_total = fields.Float(string='Montant ?? payer / an')
    #transaction_ids = fields.One2many('colibri.transaction', 'contribuable_id', string='Transaction', track_visibility='always')
    amount_paye = fields.Float(string='Montant pay??')
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
    regime_fiscale = fields.Selection(string="R??gime fiscale", selection=[
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
    date_validite_piece = fields.Date('Date de validit?? ')
    biometrie = fields.Text(string='Biom??trie')
    #activite_ids = fields.One2many('res.partner', 'entreprenant_id', string='Activit??', track_visibility='always')
    
    
    milieu_implantation = fields.Selection(string="Milieu implantation", selection=[
        ('1', 'Urbain'),
        ('2', 'Rural')
        ], track_visibility="always")
    district_id = fields.Many2one('innoving.district', string="District")
    nom_repondant = fields.Char(string=" Nom et pr??noms repondant")
    fonction_repondant = fields.Char(string="Fonction repondant")
    contact_1_repondant = fields.Char(string="contact repondant 1")
    contact_2_repondant = fields.Char(string="contact repondant 2")
    email_repondant = fields.Char(string="E-mail repondant")
    nom_prenom_dirigeant = fields.Char(string="Non et prenoms dirigeant")
    email_dirigeant = fields.Char(string="E-mail dirigeant")
    qualite_dirigeant = fields.Selection(string="Qualit?? dirigeant", selection=[
        ('1', 'Pr??sident du Conseil d???Administration'),
        ('2', 'Directeur G??n??ral'),
        ('3', 'Administrateur G??n??ral'),
        ('4', 'G??rant'),
        ('5', 'Exploitant'),
        ('6', 'Autre ?? pr??ciser')
    ])
    autre_qualite = fields.Char(string="Autre qualit??")
    sigle_entreprise = fields.Char(string="Sigle entr??prise")
    telephone_fixe_2_entreprise = fields.Char(string="Tel fixe entreprise")
    telephone_portable_1_entreprise = fields.Char(string="Tel 1 entr??prise")
    telephone_portable_2_entreprise = fields.Char(string="Tel 2 entr??prise")
    fax_entreprise = fields.Char(string="Fax entr??prise")
    email_entreprise = fields.Char(string="E-mail entr??prise")
    site_web_entreprise = fields.Char(string="Site web entr??prise")
    adresse_geographique_entreprise = fields.Char(string="Adresse g??ographie entr??prise")
    boite_postale_entreprise = fields.Char(string="Boite postale entr??prise")
    type_entreprenant = fields.Selection(string="Type entreprenant", selection=[
        ('Formel', 'Formel'),
        ('Informel', 'Informel')
        ])
    
    cluster_id = fields.Many2one('innoving.cluster', string="Cluster")
    region_id = fields.Many2one('innoving.region', string="R??gion")
    departement_id = fields.Many2one('innoving.departement', string="D??partement")
    sousprefecture_id = fields.Many2one('innoving.sous.prefecture', string="Sous pr??fecture")
    commune_id = fields.Many2one('innoving.commune', string="Commune")
    localite_id = fields.Many2one('innoving.localite', string="Localite")
    zonerecensement_id = fields.Many2one('innoving.zone.recensement', string="Zone recensement")
    quartier_id = fields.Many2one('innoving.quartier', string="Quartier")

    activite_ids = fields.One2many('res.partner', 'entreprenant_id', string='Activit??s', track_visibility='always')



    _sql_constraints = [
        ("telephone_uniq", "unique(telephone)", "Le num??ro de t??l??phone de l'entreprenant doit ??tre unique !"),
        ("cni_uniq", "unique(cni)", "Le num??ro de la CNI de l'entreprenant doit ??tre unique !"),
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
        
    
    
    @api.depends('user_id')
    def depend_user_id(self):
        if self.user_id:
            self.cluster_id = self.user_id.cluster_id.id
            self.region_id = self.user_id.region_id.id
            self.departement_id = self.user_id.departement_id.id
            self.sousprefecture_id = self.user_id.sousprefecture_id.id
            self.commune_id = self.user_id.commune_id.id
            self.localite_id = self.user_id.localite_id.id
            self.zonerecensement_id = self.user_id.zonerecensement_id.id
            self.quartier_id = self.user_id.quartier_id.id

    