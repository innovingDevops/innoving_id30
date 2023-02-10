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


class InnovingZoneRecesement(models.Model):
    _name = "innoving.zone.recensement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des zones de recesement"
    _order = "name asc"
    
    def _get_default_user_id(self):
        return self.env.uid

    
    
            
    active = fields.Boolean(string='Actif',default=True, track_visibility="always")
    name = fields.Char(string="Nom", track_visibility="always")
    code = fields.Char(string="Code", track_visibility="always")
    user_id = fields.Many2one("res.users",string="Agent",default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout",default=lambda self: fields.datetime.now(), track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirmé'),
        ('done' , 'Terminé'),
        ('cancel', 'Annulé/Rejeté')
        ] , default='draft', track_visibility="always")
    #quartier_ids = fields.Many2many('innoving.quartier','zonerecensement_quartier_rel','zonerecensement_id','quartier_id','Quartier')
    quartier_ids = fields.One2many('innoving.quartier','zonerecencement_id',string='ZR')
    localite_id = fields.Many2one('innoving.localite', string='Localite')
        
    
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
        
    