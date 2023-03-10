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


class InnovingAffectation(models.Model):
    _name = "innoving.affectation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des affectations d'ilots"
    _order = "name asc"
    
    def _get_default_user_id(self):
        return self.env.uid


    active = fields.Boolean(string='Actif',default=True, track_visibility="always")
    name = fields.Char(string="Nom", track_visibility="always")
    code = fields.Char(string="Code", track_visibility="always")
    date_demarrage = fields.Datetime("Date affectation",default=lambda self: fields.datetime.now(), track_visibility="always")
    user_id = fields.Many2one("res.users",string="Agent",default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout",default=lambda self: fields.datetime.now(), track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancel', 'Annulé/Rejeté')
        ], default='draft', track_visibility="always")
    equipe_affected = fields.Many2one('innoving.equipe', string="Equipe")
    membre_ids = fields.Many2many('res.users', 'innoving_users_equipe_rel', 'user_id', 'equipe_id', string="Membre de ma team")

    
    @api.multi
    def button_draft(self, force=False):
        self.write({'state': 'draft'})
        
    @api.multi
    def button_confirm(self, force=False):

        for identificateur in self.membre_ids:

            donnee = {
                'cluster_id':identificateur.ilot_id.cluster_id.id,
                'region_id': identificateur.ilot_id.region_id.id,
                'departement_id': identificateur.ilot_id.departement_id.id,
                'sousprefecture_id': identificateur.ilot_id.sousprefecture_id.id,
                'commune_id': identificateur.ilot_id.commune_id.id,
                'localite_id': identificateur.ilot_id.localite_id.id,
                'zonerecensement_id': identificateur.ilot_id.zonerecensement_id.id,
                'quartier_id': identificateur.ilot_id.quartier_id.id,
                'ilot_id': identificateur.ilot_id.id,
                'identificateur_id': identificateur.id,
                'equipe_id': self.equipe_affected.id,
            }
            self.env['innoving.historique.identificateur'].create(donnee)
            donnee.pop('identificateur_id')
            identificateur.write(donnee)
        self.write({'state': 'confirm', 'date_confirm': fields.Date.context_today(self)})
        
    @api.multi
    def button_done(self, force=False):
        self.write({'state': 'done', 'date_done': fields.Date.context_today(self)})
        
        
    @api.multi
    def button_cancel(self, force=False):
        self.write({'state': 'cancel','date_cancel': fields.Date.context_today(self)})

    @api.onchange('equipe_affected')
    def _onchange_equipe_affected(self):
        if self.equipe_affected:
            self.name = "Repartition - %s" % self.equipe_affected.name