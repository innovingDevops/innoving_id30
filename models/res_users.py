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
    ilot_ids = fields.Many2many('innoving.ilot','innoving_user_ilot_rel', 'user_id', 'ilot_id', string="Ilots")
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

    @api.onchange('type_users')
    def change_type_utilisateur(self):
        if self.partner_id:
            if self.type_users:
                current_user = self.env['res.users'].search([('name', '=', self.name),('login', '=', self.login)])
                groups = {
                    'Manager': 'Manager',
                    'Superviseur': 'Superviseur',
                    'Chef Equipe': 'Chef Equipe',
                    'Identificateur': 'Identificateur',
                    'Evaluateur': 'Evaluateur',
                    'Collecteur': 'Collecteur',
                    'Backoffice': 'Backoffice',
                    'Lecture': 'Lecture'}

                #recuperation des id de chaque role/group dans le dictionnaire
                for ele in groups:
                    this_group = self.env['res.groups'].search([('name', '=', ele)])
                    groups[ele] = this_group.id

                new_role_id = groups[self.type_users]
                compt = 0

                ################################################################################
                #Ajout de role ==> Processus
                #1- on parcourt l'ensemble des roles a la recherche de celui actif
                #2- On modifie la ligne du role actif pour mettre le role choisi
                #3- si aucun role actif on ajoute une ligne de role avec le role choisi
                ##################################################################################

                for ele in groups:
                    compt += 1
                    query = ''' SELECT * FROM res_groups_users_rel WHERE gid=%(gid)s AND uid=%(uid)s'''
                    args = {
                        'gid': groups[ele],
                        'uid': current_user.id,
                    }
                    self.env.cr.execute(query, args)
                    result = self.env.cr.dictfetchone()
                    if result:
                        query2 = ''' UPDATE res_groups_users_rel SET gid=%(new_gid)s WHERE gid=%(gid)s AND uid=%(uid)s'''
                        args2 = {
                            'gid': result['gid'],
                            'uid': current_user.id,
                            'new_gid': new_role_id
                        }
                        self.env.cr.execute(query2, args2)
                        break               #sortir de boucle

                    #si fin de boucle alors ==> #3
                    if compt == len(groups) :
                        query2 = ''' INSERT INTO res_groups_users_rel(gid,uid) VALUES (%(new_gid)s,%(uid)s)'''
                        args2 = {
                            'uid': current_user.id,
                            'new_gid': new_role_id
                        }
                        self.env.cr.execute(query2, args2)

    @api.model
    def create(self, vals):
        res = super(Users, self).create(vals)
        if vals['type_users']:
            res.change_type_utilisateur()
        return res










