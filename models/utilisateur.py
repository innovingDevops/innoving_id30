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
from datetime import date

from odoo.addons import decimal_precision as dp


class InnovingUtilisateur(models.Model):
    _name = "innoving.utilisateur"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gestion des utilisateurs d'identification"
    _order = "name asc"

    def _get_default_user_id(self):
        return self.env.uid

    active = fields.Boolean(string='Actif',default=True, track_visibility="always")
    name = fields.Char(string="Nom et prénoms", track_visibility="always")
    code = fields.Char(string="Code", track_visibility="always")
    user_id = fields.Many2one("res.users",string="Agent",default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout",default=lambda self: fields.datetime.now(), track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'Brouillon'),
        ('confirm', 'Confirmé'),
        ('done' , 'Terminé'),
        ('cancel', 'Annulé/Rejeté')
        ] , default='draft', track_visibility="always")
    type = fields.Selection(string="Type utilisateur", selection=[
        ('Identificateur', 'Identificateur'),
        ('Superviseur', 'Superviseur'),
        ('Evaluateur', 'Evaluateur'),
        ('Backoffice', 'Backoffice'),
        ('Lecture', 'Lecture')
        ], track_visibility="always")
    telephone = fields.Char(string="Téléphone", track_visibility="always")
    cluster_id = fields.Many2one('innoving.cluster', string="Cluster")
    region_id = fields.Many2one('innoving.region', string="Région")
    departement_id = fields.Many2one('innoving.departement', string="Département")
    sousprefecture_id = fields.Many2one('innoving.sous.prefecture', string="Sous préfecture")
    commune_id = fields.Many2one('innoving.commune', string="Commune")
    localite_id = fields.Many2one('innoving.localite', string="Localite")
    zonerecensement_id = fields.Many2one('innoving.zone.recensement', string="Zone recensement")
    quartier_id = fields.Many2one('innoving.quartier', string="Quartier")
    ilot_ids = fields.Many2many('innoving.ilot', 'user_id', 'ilot_id', string="Ilots")
    superviseur_id = fields.Many2one('innoving.utilisateur', string="Superviseur")

