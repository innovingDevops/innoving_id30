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
    
    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'activity'
            
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
        
    entreprenant_id = fields.Many2one('innoving.entreprenant', string="Entreprenant")
    ref = fields.Char(string='Reference', default=_get_default_ref)
    fiscal_year_id = fields.Many2one('account.fiscal.year', string="Année fisclale", default=_fiscal_year)
