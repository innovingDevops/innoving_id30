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


class Id30ActiviteSecteur(models.Model):
    _name = "id30.activite.secteur"
    _description = "Permet de gérer les secteurs d'activité id30"

    name = fields.Char(string='Secteur activité')
    code_secteur_activite = fields.Char(string='Code secteur')
    #categorie_taxe_ids = fields.Many2many('colibri.categorie.taxe', 'categorie_taxe_id', 'activite_secteur_id', string="Secteur d'activité", track_visibility='always')
    forme_activite = fields.Selection(string="Forme activité", selection=[
        ('AUTRE', 'AUTRE'),
        ('COMMERCE', 'COMMERCE'),
        ('SERVICE', 'SERVICE')])
    #taxe_ids = fields.Many2many('product.template', 'secteur_taxe_rel', 'secteur_id', 'taxe_id', string="taxes", track_visibility='always')
    type_activite = fields.Selection(string="Type activité", selection=[
        ('ORDINAIRE', 'ORDINAIRE'),
        ('TAXI', 'TAXI'),
        ('TRANSPORT', 'TRANSPORT'),
        ('STATIONNEMENT', 'STATIONNEMENT')])
    type_taxe = fields.Selection(string="Type de taxe", selection=[
        ('FORFAITAIRE (PCA)', 'FORFAITAIRE (PCA)'),
        ('ETABISSEMENT DE NUIT (ETN)', 'ETABISSEMENT DE NUIT (ETN)'),
        ('ODP', 'ODP'),
        ('GROS ODP', 'GROS ODP'),
        ('TICKET MARCHE', 'TICKET MARCHE'),
        ('PUB', 'PUB')])
    