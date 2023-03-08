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


class InnovingIlot(models.Model):
    _name = "innoving.historique.identificateur"
    #_inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des historiques des identificateurs"
    _order = "name asc"
    
    def _get_default_user_id(self):
        return self.env.uid

   
    active = fields.Boolean(string='Actif',default=True, track_visibility="always")
    name = fields.Char(string="Numéro", track_visibility="always")
    code = fields.Char(string="Code", track_visibility="always")
    user_id = fields.Many2one("res.users",string="Agent",default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout",default=lambda self: fields.datetime.now(), track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirmé'),
        ('done' , 'Terminé'),
        ('cancel', 'Annulé/Rejeté')
        ] , default='draft', track_visibility="always")
    cluster_id = fields.Many2one('innoving.cluster', string="Cluster")
    region_id = fields.Many2one('innoving.region', string="Région")
    departement_id = fields.Many2one('innoving.departement', string="Département")
    sousprefecture_id = fields.Many2one('innoving.sous.prefecture', string="Sous préfecture")
    commune_id = fields.Many2one('innoving.commune', string="Commune")
    localite_id = fields.Many2one('innoving.localite', string="Localite")
    zonerecensement_id = fields.Many2one('innoving.zone.recensement', string='Zone recensement')
    quartier_id = fields.Many2one('innoving.quartier', string="Quartier")
    ilot_id = fields.Many2one('innoving.ilot', string="Ilot")
    identificateur_id = fields.Many2one("res.users", string="Identifiacteur")
    equipe_id = fields.Many2one("innoving.equipe", string="Equipe")

    
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
        
    