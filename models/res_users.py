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


class Users(models.Model):
    _inherit = 'res.users'
    _name = 'res.users'

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
    type_users = fields.Selection(string="Type utilisateur", selection=[
        ('Manager', 'Manager'),
        ('Superviseur', 'Superviseur'),
        ('Chef Equipe', 'Chef Equipe'),
        ('Identificateur', 'Identificateur'),
        ('Evaluateur', 'Evaluateur'),
        ('Backoffice', 'Backoffice'),
        ('Lecture', 'Lecture')
    ], track_visibility="always")
    equipe_id = fields.Many2one('innoving.equipe', string="Equipe de l'identificateur")
    has_equipe = fields.Boolean(string='Déja dans une equipe')
    is_chef = fields.Selection(string="Statut chef equipe", selection=[
        ('Occupe', 'Occupe'),
        ('Libre', 'Libre'),
    ], default='Libre', track_visibility="always")
    superviseur_id = fields.Many2one('res.users', string="Superviseur")
    manager_id = fields.Many2one('res.users', string="Manager")
    district = fields.Selection(string="District", selection=[
        ('Abidjan', 'Abidjan'),
        ('Yamoussoukro', 'Yamoussoukro')
    ], track_visibility="always")



