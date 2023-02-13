# -*- coding: utf-8 -*-

import base64
from datetime import date
import hashlib
import pytz
import threading
from odoo.exceptions import UserError

from email.utils import formataddr
from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _


# Modeles des classes d'etudes/ apprentissage à la paroisse
class InnovingEquipeIdentificateur(models.Model):
    _name = "innoving.equipe"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Gestion des Equipes"
    _order = "name asc"

    def _get_default_user_id(self):
        return self.env.uid


    active = fields.Boolean(string='Actif', default=True, track_visibility="always")
    image = fields.Binary(string="Photo", track_visibility="always")
    name = fields.Char(string="Nom", track_visibility="always")
    code = fields.Char(string="Ref", track_visibility="always", default="/")
    nbr_identificateur = fields.Integer(string="Nombre agent", compute='_compute_identificateur', store=True)
    user_id = fields.Many2one("res.users", string="Agent", default=_get_default_user_id, track_visibility="always")
    date_ajout = fields.Datetime("Date ajout", default=lambda self: fields.datetime.now(), track_visibility="always")
    state = fields.Selection(string="Etat", selection=[
        ('draft', 'brouillon'),
        ('confirm', 'Ouvert'),
        ('done', 'Fermé')
    ], default='draft', track_visibility="always")

    date_confirm = fields.Date(string="Date de confirmation", track_visibility="always")
    date_done = fields.Date(string="Date clôture", track_visibility="always")
    date_cancel = fields.Date(string="Date rejette", track_visibility="always")

    # champ relationnel
    chef_equipe_id = fields.Many2one('res.users', string="Chef d'Equipe")
    identificateur_ids = fields.Many2many('res.users', 'innoving_users_equipe', 'user_id', 'equipe_id', string="liste des identificateurs")



    @api.depends('identificateur_ids')
    def _compute_identificateur(self):
        for req in self:
            req.nbr_identificateur = len(req.identificateur_ids)
            self.update({'nbr_identificateur': req.nbr_identificateur})


    @api.multi
    def button_draft(self, force=False):
        self.write({'state': 'draft'})

    @api.multi
    def button_confirm(self, force=False):
        if self.identificateur_ids:
            for user in self.identificateur_ids:
                msg_error = ""
                if user.has_equipe == False:
                    user.write({'has_equipe': True,'equipe_id':self.id})
                else :
                    msg_error = "Attention ! L'identificateur "+user.name+" est déjà dans l'équipe "+user.equipe_id.name
                    msg_error += "\n Veuillez le deselectionner ou changer son équipe en cours"
                    raise UserError(_('%s') % msg_error)
            self.write({'state': 'confirm'})



    @api.multi
    def button_done(self, force=False):
        self.write({'state': 'done', 'date_done': fields.Date.context_today(self)})

    @api.multi
    def button_cancel(self, force=False):
        self.write({'state': 'cancel', 'date_cancel': fields.Date.context_today(self)})






