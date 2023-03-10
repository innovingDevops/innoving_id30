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

    @api.depends('longueur', 'largeur', 'entreprenant_id.state')
    def _compute_odp(self):
        for record in self:
            record.update({'odp': record.longueur * record.largeur})


    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'activity'

    @api.depends('pub_longueur', 'pub_largeur', 'entreprenant_id.state', 'pub_largeur_2', 'pub_longueur_2')
    def _compute_pub(self):
        for record in self:
            record.update({'pub_en_mettre_carre': record.pub_longueur * record.pub_largeur,
                           'pub_en_mettre_carre_2': record.pub_longueur_2 * record.pub_largeur_2})

    entreprenant_id = fields.Many2one('innoving.entreprenant', string="Entreprenant")
    ref = fields.Char(string='Reference', default=_get_default_ref)
    fiscal_year_id = fields.Many2one('account.fiscal.year', string="Ann??e fisclale", default=_fiscal_year)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company'),
                                               ('activity', 'Activit??')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    country_id = fields.Many2one('res.country', default=_get_default_country)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_default_currency,
                                  track_visibility='always')
    #nouveau champs
    #rubrique votre entreprise
    name = fields.Char(string="Nom (Activit?? principale)")
    activity_birthday = fields.Char(string="Date de cr??ation activit??")
    street = fields.Char(string="Rue / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    street3 = fields.Char(string="Rue 2 / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    city = fields.Char(string="Ville / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    activite_type_id = fields.Many2one('innoving.type.activite', string="Activite")
    regime_fiscale = fields.Char(string="R??gime fiscale")
    chiffre_affaire_taxable = fields.Char(string="CA d??clar??")
    min_ca = fields.Char(string="CA min")
    max_ca = fields.Char(string="CA max")
    secteur_id = fields.Many2one('innoving.secteur.activite', string="Secteur d'activit??")
    forme_activite = fields.Selection(string="Forme activit??", selection=[
        ('AUTRE', 'AUTRE'),
        ('COMMERCE', 'COMMERCE'),
        ('SERVICE', 'SERVICE')], related='secteur_id.forme_activite')
    zone_id = fields.Char(string="Zone")
    type_taxe = fields.Selection(string="Type de taxe", selection=[
        ('FORFAITAIRE (PCA)', 'FORFAITAIRE (PCA)'),
        ('ETABISSEMENT DE NUIT (ETN)', 'ETABISSEMENT DE NUIT (ETN)'),
        ('ODP', 'ODP'),
        ('GROS ODP', 'GROS ODP'),
        ('TICKET MARCHE', 'TICKET MARCHE'),
        ('PUB', 'PUB')])
    cga = fields.Selection(string="CGA", selection=[
        ('Oui', 'Oui'),
        ('Non', 'Non')])
    date_adhesion = fields.Char(string="Date adh??sion")
    ref_cga = fields.Char(string="N?? Adh??sion CGA")
    periode_imposition = fields.Selection(string="P??riode d'imposition", selection=[
        ('Jour', 'Jour'),
        ('Mois', 'Mois'),
        ('Bimestrielle', 'Bimestrielle'),
        ('Trimestrielle', 'Trimestrielle'),
        ('Semestrielle', 'Semestrielle'),
        ('Annuelle', 'Annuelle')])
    taux_imposition = fields.Float(string="Indice d'imposition")
    taille_activite = fields.Selection(string="Taille activit??", selection=[
        ('Tr??s petite', 'Tr??s petite'),
        ('Petite', 'Petite'),
        ('Moyenne', 'Moyenne'),
        ('Grande', 'Grande'),
        ('DGI', 'DGI')])
    date_debut_exploitation = fields.Char(string="C13: Date de debut d'exploitation:(Mois/Ann??e)")
    #rubrique INS
    ciap = fields.Char(string="C14.a: Codification CIAP(r??server ?? l'INS) (activit?? principale)")
    longueur = fields.Float(string="Longueur ODP")
    largeur = fields.Float(string="Largeur")
    odp = fields.Float(string='Surface ODP', compute='_compute_odp',  store=True)
    baux_loyer = baux_loyer = fields.Selection(string="Baux  ?? loyer", selection=[
        ('4000', '4 000 CFA'),
        ('7000', '7 000 CFA'),
        ('8400', '8 400 CFA'),
        ('10000', '10 000 CFA'),
        ('11200', '11 200 CFA'),
        ('14000', '14 000 CFA'),
        ('15000', '15 000 CFA'),
        ('16000', '16 000 CFA'),
        ('17000', '17 000 CFA'),
        ('17500', '17 500 CFA'),
        ('20000', '20 000 CFA'),
        ('25000', '25 000 CFA'),
        ('56000', '56 000 CFA'),
        ('70000', '70 000 CFA')])

    pub_longueur = fields.Char(string="Longueur Peinte")
    pub_largeur = fields.Char(string="Largeur Peinte")
    pub_en_mettre_carre = fields.Float(string='PUB peinte en m??', compute='_compute_pub', store=True)
    pub_longueur_2 = fields.Float(string="Longueur Enseigne")
    pub_largeur_2 = fields.Float(string="Largeur Enseigne")
    pub_en_mettre_carre_2 = fields.Float(string="PUB Enseigne en m??", compute='_compute_pub', store=True)
    image = fields.Binary(string="Image")
    partner_latitude = fields.Char(string="Lat")
    partner_longitude = fields.Char(string="Long")
    idu_cepici = fields.Selection(string="C16: Votre entreprise dispose t-elle d'un num??ro d'identification unique(IDU) du CEPICI ?", selection=[('oui', 'oui'), ('non', 'non')])
    idu_communicable = fields.Selection(string="Pouvez-vous nous donner ce num??ro IDU?", selection=[('oui', 'oui'), ('non', 'non')])
    numero_idu = fields.Char(string="C16.a: Si oui, donner ce num??ro IDU")
    chiffre_idu = fields.Integer(string="Saisir les 13 chiffres de l'IDU")
    lettre_fin_idu = fields.Char(string="Saisir la lettre de fin de l'IDU")
    autre_type_activite = fields.Selection( string="Avez-vous une autre activite", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    activicte_2 = fields.Many2one('innoving.type.activite', string="Activite")

    #rubrique R??gime sociale
    etat_activite = fields.Selection(string="C21 : Quel est l?????tat d???activit?? de l'entreprise ?" , selection=[
                                        ('1', 'Activit?? non encore d??marr??e'),
                                        ('2', 'En activit??'),
                                        ('3', 'En veille ou en cessation momentan??e'),
                                        ('4', 'Cessation totale d???activit??')])

    forme_juridique = fields.Selection(string="C21 : Quel est l?????tat d???activit?? de l'entreprise ?", selection=[
                                        ('1', 'Soci??t?? en Nom Collectif'),
                                        ('2', 'Soci??t?? en Commandite Simple'),
                                        ('3', 'Soci??t?? en Participations'),
                                        ('4', 'Soci??t?? de fait'),
                                        ('5', 'Soci??t?? ?? Responsabilit?? limit??e (SARL)'),
                                        ('6', 'Soci??t?? par Actions simplifi??es (SAS)'),
                                        ('7', 'Entreprise individuelle (pers. physique)'),
                                        ('8', 'Soci??t?? anonyme (SA)'),
                                        ('9', "Groupement d'Int??r??t ??conomique (GIE)"),
                                        ('10', 'Ets public industriel et commercial (EPIC)'),
                                        ('11', 'Autres(?? pr??ciser)')])
    autre_forme_juridique = fields.Char(string="C22.a: Autre forme juridique ?? pr??ciser")
    capital_en_action = fields.Selection(string="C23: Votre entreprise est-elle majoritairement (Plus de 50%) ?? capitaux:", selection=[
                                        ('1', 'Public'),
                                        ('2', 'Priv??'),
                                        ('3', 'Priv?? ??tranger')])

    name_actionnaire = fields.Char(string="Nom et pr??noms ou raison sociale de l'actionnaire")
    type_actionnaire = fields.Selection(string="L'actionnaire est-il une personne physique?", selection=[('1', 'Oui'),('2', 'Non')])
    sexe_actionnaire = fields.Selection(string="Si personne physique, pr??cisez le sexe de l'actionnaire",
                                        selection=[('1', 'Masculin'),('2', 'Feminin'),('3','Sans objet')])
    nationalite_actionnaire = fields.Char(string="Quelle est la nationalit?? de l'actionnaire?")
    montant_action = fields.Float(string="Montant de l'action de l'actionnaire")
    part_sociale_actionnaire = fields.Float(string="Part sociale(en %) de l'actionnaire")
    autre_actionnaire = fields.Char(string="Autre actionnaire?")
    ca_ht_n_1 = fields.Float(string="D1.b21: Quel est le montant de votre chiffre d???affaires hors taxes en 2021 ?")
    ca_ht_n_2 = fields.Float(string="D1.b20: Quel est le montant de votre chiffre d???affaires hors taxes en 2020 ?")
    ca_ht_n_3 = fields.Float(string="D1.b19: Quel est le montant de votre chiffre d???affaires hors taxes en 2019 ?")
    valeur_ajoute_brute_n_1 = fields.Float(string="D1.c21: Quel est le montant de votre valeur ajout??e brute en 2021 ?")
    valeur_ajoute_brute_n_2 = fields.Float(string="D1.c20: Quel est le montant de votre valeur ajout??e brute en 2020 ?")
    valeur_ajoute_brute_n_3 = fields.Float(string="D1.c19: Quel est le montant de votre valeur ajout??e brute en 2019 ?")
    export_produit = fields.Selection(string="D2: Exportez-vous en partie ou en totalit?? vos produits/services ?", selection=[('1', 'Oui'), ('2', 'Non')])
    valeur_export_n_1 = fields.Float(string="D2.a21: Si oui, donnez la valeur de vos exportations en 2021")
    valeur_export_n_2 = fields.Float(string="D2.a20: Si oui, donnez la valeur de vos exportations en 2020")
    valeur_export_n_3 = fields.Float(string="D2.a19: Si oui, donnez la valeur de vos exportations en 2019")

    #rubrique : 19 contrainte  par ordre d'importance
    manque_personnel_qualifie = fields.Selection(string="a: Insuffisance de personnel qualifi??", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_eleve_main_oeuvre = fields.Selection(string="b: Co??t ??lev?? de la main d'??uvre", selection=[('1', 'Oui'), ('0', 'Non')])
    formalite_administrative_contraignante = fields.Selection(string=" c: Formalit??s administratives contraignantes ", selection=[('1', 'Oui'), ('0', 'Non')])
    taxe_impot_eleve = fields.Selection(string=" d: Taxes et imp??ts trop ??lev??s ", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_tranport_eleve = fields.Selection(string=" e: Co??t du transport ??lev?? (FRET) ", selection=[('1', 'Oui'), ('0', 'Non')])
    mauvais_etat_infrastructure = fields.Selection(string=" f: Mauvais ??tat des infrastructures routi??res ", selection=[('1', 'Oui'), ('0', 'Non')])
    difficulte_approvisionnement_matiere_premiere = fields.Selection(string="g: Difficult??s d'approvisionnement en mati??res premi??res et autres intrants (quantit?? et qualit??) ", selection=[('1', 'Oui'), ('0', 'Non')])
    procedure_contentieux = fields.Selection(string=" h: Lourdeurs des proc??dures de r??glement des contentieux ", selection=[('1', 'Oui'), ('0', 'Non')])
    ecoulement_production = fields.Selection(string="i: Difficult??s d'??coulement de la production/insuffisance de d??bouch??s", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_au_technologie = fields.Selection(string="j: Manque/Faible acc??s aux technologies sp??cialis??es", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_machine = fields.Selection(string="k: Manque de machines et pi??ces de rechange", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_expertise_technique = fields.Selection(string="l: Manque d???expertise technique (maintenance machines)", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_local_adapte = fields.Selection(string="m: Manque de local adapt??/terrain", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_commande_public = fields.Selection(string="n: Difficult??s d'acc??s ?? la commande publique", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_structure_appui = fields.Selection(string="o: Acc??s limit?? aux structures d'appui aux entreprises", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_credit_bancaire = fields.Selection(string="p: Difficult??s d'acc??s au cr??dit (Banque et Microfinance)", selection=[('1', 'Oui'), ('0', 'Non')])
    approvisionnement_energie = fields.Selection(string="q: Difficult??s d'approvisionnement en ??nergie", selection=[('1', 'Oui'), ('0', 'Non')])
    concurrence_deloyale = fields.Selection(string="r: Concurrence d??loyale", selection=[('1', 'Oui'), ('0', 'Non')])
    corruption = fields.Selection(string="s: Corruption (racket, pot de vins, etc.)", selection=[('1', 'Oui'), ('0', 'Non')])
    autre_contrainte = fields.Selection(string="t Autre contrainte (?? pr??ciser)", selection=[('1', 'Oui'), ('0', 'Non')])
    precise_contrainte = fields.Char(string="u: Pr??cisez la contrainte )")
    aucune_contrainte = fields.Selection(string="u. Aucune contrainte", selection=[('1', 'Oui'), ('0', 'Non')])

    #ajout champ informel
    autre_activte = fields.Selection(string="Autre activit?? secondaire? ", selection=[('1', 'Oui'), ('2', 'Non')])
    autre_activite_precision = fields.Char(string="Pr??cisez l'activict?? ")
    autre_local = fields.Char(string=" C18.a: Autre local ?? pr??ciser")
    autre_moyen_comptable = fields.Char(string="C16.a: Autre moyen de comptabilit?? ?? pr??ciser ")
    autre_status_local = fields.Char(string="C19.a: Autre statut de terrain ?? pr??ciser ")
    code_ciap = fields.Char(string="Code CIAP (activit?? secondaire) ")
    communique_registre_metier = fields.Selection(string="Pouvez-vous nous communiquer ce num??ro RM? ", selection=[('1', 'Oui'), ('2', 'Non')])
    connexion_internet = fields.Selection(string="C22: Votre entreprise/??tablissement dispose-t-elle/il d???une connexion internet ? ", selection=[('1', 'Oui'), ('2', 'Non')])
    contrainte_rencontre = fields.Many2many('innoving.contrainte.activite','innoving_partner_contrainte_rel', 'activite_id', 'contrainte_activite_id',
                                            string="E1: Quelles sont les principales contraintes que votre entreprise rencontre dans le cadre de votre activit?? (choix multiples) ?")
    declaration_cnps = fields.Selection(string="C15: Votre entreprise est-elle d??clar??e ?? la CNPS? ", selection=[('1', 'Oui'), ('2', 'Non')])
    designation_activite = fields.Char(string=" D??signation de l'activit??")
    deux_1er_chiffre_rm = fields.Integer(string=" Saisir les 2 premi??rs chiffres du RM")
    deux_1er_lettre_rm = fields.Char(string=" Saisir les 2 premi??res lettres du RM")
    deux_dernier_lettre_rm = fields.Char(string="Saisir les 2 derni??res lettres du RM")
    doc_fin_exercice = fields.Selection(string="Votre entreprise produit-elle un document comptable en fin d???exercice ? ", selection=[('1', 'Oui'), ('2', 'Non')])
    effectif_nationaux_femme_permanent = fields.Integer(string=" D6a3f: Quel est l'effectif des nationaux femmes permanentes en 2021 ?")
    effectif_nationaux_femme_temporaire = fields.Integer(string=" D6a4f: Quel est l'effectif des nationaux femmes Saisonniers/temporaires en 2021 ?")
    effectif_nationaux_homme_permanent = fields.Integer(string=" D6a3h: Quel est l'effectif nationaux hommes permanents en 2021 ?")
    effectif_nationaux_homme_temporaire = fields.Integer(string=" D6a4h: Quel est l'effectif nationaux hommes Saisonniers/temporaires en 2021 ?")
    effectif_non_nationaux_femme = fields.Integer(string=" D6a5f: Quel est l'effectif total des non nationaux femmes en 2021 ?")
    effectif_non_nationaux_femme_permanent = fields.Integer(string=" D6a6f: Quel est l'effectif des non nationaux femmes permanentes en 2021 ?")
    effectif_non_nationaux_femme_temporaire = fields.Integer(string=" D6a7f: Quel est l'effectif des non nationaux femmes Saisonniers/temporaires en 2021 ?")
    effectif_non_nationaux_homme = fields.Integer(string=" D6a5h: Quel est l'effectif total des non nationaux hommes en 2021 ?")
    effectif_non_nationaux_homme_permanent = fields.Integer(string=" D6a6h: Quel est l'effectif non nationaux hommes permanents en 2021 ?")
    effectif_non_nationaux_homme_temporaire = fields.Integer(string=" D6a7h: Quel est l'effectif non nationaux hommes Saisonniers/temporaires en 2021 ?")
    effectif_total = fields.Integer(string=" D6 : Quel est l???effectif total de votre entreprise/??tablissement en 2021?")
    effectif_total_femme = fields.Integer(string=" D6a1f: Quel est l'effectif total femmes de votre entreprise/??tablissement en 2021")
    effectif_total_homme = fields.Integer(string=" D6a1h: Quel est l'effectif total hommes de votre entreprise/??tablissement en 2021 ?")
    effectif_total_nationaux_femme = fields.Integer(string=" D6a2f: Quel est l'effectif total des nationaux femmes en 2021 ?")
    effectif_total_nationaux_homme = fields.Integer(string=" D6a2h: Quel est l'effectif total des nationaux hommes en 2021 ?")
    etat_fonctionnement_entreprise = fields.Selection(string="C21 : Quel est l?????tat d???activit?? de l'entreprise ? ",
                                                      selection=[('1', 'En activit??'),
                                                                ('2', 'En veille / Arr??t momentan??'),
                                                                ('3', 'Activit?? en attente de d??marrage'),
                                                                ('4', "Cessation d'activit??")])
    etat_infrastructure = fields.Selection(string=" f: Mauvais ??tat des infrastructures routi??res", selection=[('1', 'Oui'), ('0', 'Non')])
    import_produit = fields.Selection(string="D5: Importez-vous en partie ou en totalit?? vos marchandises ou mati??res premi??res ? ", selection=[('1', 'En partie'), ('2', 'En totalit??'),('3', 'Non')])
    import_service = fields.Selection(string="D5: Importez-vous en partie ou en totalit?? vos produis ou services ? ", selection=[('1', 'En partie'), ('2', 'En totalit??'),('3', 'Non')])
    local_activicte = fields.Selection(string=" C18: Dans quel type de local exercez-vous votre activit?? ? ",
                                       selection=[('1', 'Bureau / B??timent'),
                                                  ('2', 'Hangar'),
                                                  ('3', 'Baraque'),
                                                  ('4', 'Box'),
                                                  ('5', 'Magasin/Entrep??t'),
                                                  ('6', 'Local fixe dans un march??'),
                                                  ('7', 'A domicile'),
                                                  ('8', 'Carri??re'),
                                                  ('9', 'Conteneur'),
                                                  ('10', 'A ciel ouvert'),
                                                  ('11', 'Autres ?? pr??ciser')])
    masse_salariale_nationaux_permanent = fields.Float(string=" D6a3ms: Quel est la masse salariale des nationaux permanents en 2021 ?")
    masse_salariale_nationaux_temporaire = fields.Float(string=" D6a4ms: Quel est la masse salariale des nationaux Saisonniers/temporaires en 2021 ?")
    masse_salariale_non_nationaux_permanent = fields.Float(string=" D6a6ms: Quel est la masse salariale des non nationaux permanents en 2021 ?")
    masse_salariale_non_nationaux_temporaire = fields.Float(string=" D6a7ms: Quel est la masse salariale des non nationaux Saisonniers/temporaires en 2021 ?")
    masse_salariale_total = fields.Float(string=" D6a1ms: Quel est la masse salariale totale en FCFA de votre entreprise/??tablissement en 2021 ?")
    masse_salariale_total_nationaux = fields.Float(string=" D6a2ms: Quel est la masse salariale totale des nationaux de votre entreprise/??tablissement en 2021 ?")
    masse_salariale_total_non_nationaux = fields.Float(string=" D6a5ms: Quel est la masse salariale totale des non nationaux de votre entreprise/??tablissement en 2021 ?")
    montant = fields.Float(string=" Montant ")
    montant_charge_mensuelle = fields.Float(string=" D2. Quel est le montant total des charges mensuelles li??es ?? votre activit?? (en FCFA) en 2021 ?")
    montant_total_actif = fields.Float(string=" D9 Quel est le montant total des Actif (en FCFA)")
    montant_total_actif_immobiliser = fields.Float(string=" D8 Quel est le montant total des Actifs immobilis??s (en FCFA)")
    montant_total_capiteaux_propre = fields.Float(string=" D7 Quel est le montant total des Capitaux propres (en FCFA)")
    montant_total_charge_ordinaire = fields.Float(string=" D11 Quel est le montant total des charges ordinaires (en FCFA)")
    montant_total_impot_taxe = fields.Float(string=" D12 Quel est le montant total des Imp??ts et taxes (en FCFA)")
    montant_total_ressource_stable = fields.Float(string=" D10 Quel est le montant total des Ressources stables (en FCFA)")
    montant_vente_maximum_realiser = fields.Float(string=" D3.b: Quelles est le montant maximum de vos ventes mensuelles (en FCFA) r??alis??es au cours des 12 derniers mois ?")
    montant_vente_minimum_realiser = fields.Float(string=" D3.a: Quelles est le montant minimum de vos ventes mensuelles (en FCFA) r??alis??es au cours des 12 derniers mois ?")
    moyen_comptable = fields.Selection(string="C16 : Quel moyen principal utilisez-vous pour votre comptabilit?? ? ", selection=[
        ('1', 'Carnet ou cahier de d??penses et recettes'),
        ('2', 'Fiche de caisse informatis??e??'),
        ('3', 'Aucun'),
        ('4', 'Autre ?? pr??ciser')])
    name_activite_secondaire = fields.Char(string="D??signation de l'activit?? secondaire ")
    nombre_etablissement = fields.Char(string="C20.b: Combien d?????tablissements avez-vous ? ")
    num_compte_contribuable = fields.Char(string="Si oui, donnez le num??ro de compte contribuable ")
    num_registre_commerce = fields.Char(string="Si oui, donnez le num??ro de registre de commerce ")
    num_registre_metier  = fields.Char(string="C14.a: Si oui, donnez le num??ro de registre de m??tier ")
    numero_cnps = fields.Integer(string="C15.a: Si oui, donnez le num??ro CNPS (en 7 chiffres) ")
    numero_cnps_communicable = fields.Selection(string="Pouvez-vous nous communiquer ce num??ro CNPS? ", selection=[('1', 'Oui'), ('2', 'Non')])
    periodicite = fields.Selection(string=" P??riodicit??", selection=[('1', 'Jour'), ('2', 'Semaine'),('3','Mois'),('4','Ann??e')])
    quatre_chiffre_rm = fields.Float(string=" Saisir les 4 chiffres pr??cedents les 2 lettres saisies du RM", selection=[('1', 'Oui'), ('2', 'Non')])
    registre_metier = fields.Selection(string="C14: Votre entreprise dispose-t-elle d???un num??ro de registre M??tier (RM)? ", selection=[('1', 'Oui'), ('2', 'Non')])
    sept_chiffre_rm = fields.Integer(string="Saisir les 7 derniers chiffres du RM ")
    statut_comptabilite_formel = fields.Selection(string="Votre entreprise tient-elle, une comptabilit?? formelle ??crite ? ", selection=[('1', 'Oui'), ('2', 'Non')])
    statut_compte_contribuable = fields.Selection(string="Votre entreprise dispose t-elle d'un num??ro de compte contribuable(NCC)? ", selection=[('1', 'Oui'), ('2', 'Non')])
    statut_entreprise = fields.Selection(string="C20.a: Quel est le statut de votre entreprise/??tablissement ? ",
                                         selection=[('1', '??tablissement principal'),
                                                    ('2', '??tablissement secondaire'),
                                                    ('3', '??tablissement unique')])
    statut_local = fields.Selection(string="C19 : Quel est le statut du terrain sur lequel votre entreprise/??tablissement est localis??(e) ? ",
                                    selection=[('1', 'Occupation du domaine public'),
                                                ('2', 'Propri??taire du local/terrain'),
                                                ('3', 'Espace d??di?? autoris??'),
                                                ('4', 'Autre ?? pr??ciser')])
    statut_registre_commerce = fields.Selection(string=" Votre entreprise dispose-t-elle d???un num??ro de Registre de Commerce (RC)?", selection=[('1', 'Oui'), ('2', 'Non')])
    type_entreprise = fields.Selection(string="Votre structure est-elle une Organisation Non Gouvernemental (ONG) ou une Institution sans but lucratif (*)", selection=[('1', 'Oui'), ('2', 'Non')])
    utilisation_logiciel_metier = fields.Selection(string=" C21: Utilisez-vous des logiciels m??tiers au sein de votre entreprise/??tablissement ?", selection=[('1', 'Oui'), ('2', 'Non')])










