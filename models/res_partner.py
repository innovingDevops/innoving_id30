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
    fiscal_year_id = fields.Many2one('account.fiscal.year', string="Année fisclale", default=_fiscal_year)
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company'),
                                               ('activity', 'Activité')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    country_id = fields.Many2one('res.country', default=_get_default_country)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_default_currency,
                                  track_visibility='always')
    #nouveau champs
    #rubrique votre entreprise
    name = fields.Char(string="Nom (Activité principale)")
    activity_birthday = fields.Char(string="Date de création activité")
    street = fields.Char(string="Rue / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    street3 = fields.Char(string="Rue 2 / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    city = fields.Char(string="Ville / ADRESSE GEOGRAPHIQUE DE L'ETABLISSEMENT")
    activite_type_id = fields.Many2one('innoving.type.activite', string="Activite")
    regime_fiscale = fields.Char(string="Régime fiscale")
    chiffre_affaire_taxable = fields.Char(string="CA déclaré")
    min_ca = fields.Char(string="CA min")
    max_ca = fields.Char(string="CA max")
    secteur_id = fields.Many2one('innoving.secteur.activite', string="Secteur d'activité")
    forme_activite = fields.Selection(string="Forme activité", selection=[
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
    date_adhesion = fields.Char(string="Date adhésion")
    ref_cga = fields.Char(string="N° Adhésion CGA")
    periode_imposition = fields.Selection(string="Période d'imposition", selection=[
        ('Jour', 'Jour'),
        ('Mois', 'Mois'),
        ('Bimestrielle', 'Bimestrielle'),
        ('Trimestrielle', 'Trimestrielle'),
        ('Semestrielle', 'Semestrielle'),
        ('Annuelle', 'Annuelle')])
    taux_imposition = fields.Float(string="Indice d'imposition")
    taille_activite = fields.Selection(string="Taille activité", selection=[
        ('Très petite', 'Très petite'),
        ('Petite', 'Petite'),
        ('Moyenne', 'Moyenne'),
        ('Grande', 'Grande'),
        ('DGI', 'DGI')])
    date_debut_exploitation = fields.Char(string="C13: Date de debut d'exploitation:(Mois/Année)")
    #rubrique INS
    ciap = fields.Char(string="C14.a: Codification CIAP(réserver à l'INS) (activité principale)")
    longueur = fields.Float(string="Longueur ODP")
    largeur = fields.Float(string="Largeur")
    odp = fields.Float(string='Surface ODP', compute='_compute_odp',  store=True)
    baux_loyer = baux_loyer = fields.Selection(string="Baux  à loyer", selection=[
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
    pub_en_mettre_carre = fields.Float(string='PUB peinte en m²', compute='_compute_pub', store=True)
    pub_longueur_2 = fields.Float(string="Longueur Enseigne")
    pub_largeur_2 = fields.Float(string="Largeur Enseigne")
    pub_en_mettre_carre_2 = fields.Float(string="PUB Enseigne en m²", compute='_compute_pub', store=True)
    image = fields.Binary(string="Image")
    partner_latitude = fields.Char(string="Lat")
    partner_longitude = fields.Char(string="Long")
    idu_cepici = fields.Selection(string="C16: Votre entreprise dispose t-elle d'un numéro d'identification unique(IDU) du CEPICI ?", selection=[('oui', 'oui'), ('non', 'non')])
    idu_communicable = fields.Selection(string="Pouvez-vous nous donner ce numéro IDU?", selection=[('oui', 'oui'), ('non', 'non')])
    numero_idu = fields.Char(string="C16.a: Si oui, donner ce numéro IDU")
    chiffre_idu = fields.Integer(string="Saisir les 13 chiffres de l'IDU")
    lettre_fin_idu = fields.Char(string="Saisir la lettre de fin de l'IDU")
    autre_type_activite = fields.Selection( string="Avez-vous une autre activite", selection=[('Oui', 'Oui'), ('Non', 'Non')])
    activicte_2 = fields.Many2one('innoving.type.activite', string="Activite")

    #rubrique Régime sociale
    etat_activite = fields.Selection(string="C21 : Quel est l’état d’activité de l'entreprise ?" , selection=[
                                        ('1', 'Activité non encore démarrée'),
                                        ('2', 'En activité'),
                                        ('3', 'En veille ou en cessation momentanée'),
                                        ('4', 'Cessation totale d’activité')])

    forme_juridique = fields.Selection(string="C21 : Quel est l’état d’activité de l'entreprise ?", selection=[
                                        ('1', 'Société en Nom Collectif'),
                                        ('2', 'Société en Commandite Simple'),
                                        ('3', 'Société en Participations'),
                                        ('4', 'Société de fait'),
                                        ('5', 'Société à Responsabilité limitée (SARL)'),
                                        ('6', 'Société par Actions simplifiées (SAS)'),
                                        ('7', 'Entreprise individuelle (pers. physique)'),
                                        ('8', 'Société anonyme (SA)'),
                                        ('9', "Groupement d'Intérêt économique (GIE)"),
                                        ('10', 'Ets public industriel et commercial (EPIC)'),
                                        ('11', 'Autres(à préciser)')])
    autre_forme_juridique = fields.Char(string="C22.a: Autre forme juridique à préciser")
    capital_en_action = fields.Selection(string="C23: Votre entreprise est-elle majoritairement (Plus de 50%) à capitaux:", selection=[
                                        ('1', 'Public'),
                                        ('2', 'Privé'),
                                        ('3', 'Privé étranger')])

    name_actionnaire = fields.Char(string="Nom et prénoms ou raison sociale de l'actionnaire")
    type_actionnaire = fields.Selection(string="L'actionnaire est-il une personne physique?", selection=[('1', 'Oui'),('2', 'Non')])
    sexe_actionnaire = fields.Selection(string="Si personne physique, précisez le sexe de l'actionnaire",
                                        selection=[('1', 'Masculin'),('2', 'Feminin'),('3','Sans objet')])
    nationalite_actionnaire = fields.Char(string="Quelle est la nationalité de l'actionnaire?")
    montant_action = fields.Float(string="Montant de l'action de l'actionnaire")
    part_sociale_actionnaire = fields.Float(string="Part sociale(en %) de l'actionnaire")
    autre_actionnaire = fields.Char(string="Autre actionnaire?")
    ca_ht_n_1 = fields.Float(string="D1.b21: Quel est le montant de votre chiffre d’affaires hors taxes en 2021 ?")
    ca_ht_n_2 = fields.Float(string="D1.b20: Quel est le montant de votre chiffre d’affaires hors taxes en 2020 ?")
    ca_ht_n_3 = fields.Float(string="D1.b19: Quel est le montant de votre chiffre d’affaires hors taxes en 2019 ?")
    valeur_ajoute_brute_n_1 = fields.Float(string="D1.c21: Quel est le montant de votre valeur ajoutée brute en 2021 ?")
    valeur_ajoute_brute_n_2 = fields.Float(string="D1.c20: Quel est le montant de votre valeur ajoutée brute en 2020 ?")
    valeur_ajoute_brute_n_3 = fields.Float(string="D1.c19: Quel est le montant de votre valeur ajoutée brute en 2019 ?")
    export_produit = fields.Selection(string="D2: Exportez-vous en partie ou en totalité vos produits/services ?", selection=[('1', 'Oui'), ('2', 'Non')])
    valeur_export_n_1 = fields.Float(string="D2.a21: Si oui, donnez la valeur de vos exportations en 2021")
    valeur_export_n_2 = fields.Float(string="D2.a20: Si oui, donnez la valeur de vos exportations en 2020")
    valeur_export_n_3 = fields.Float(string="D2.a19: Si oui, donnez la valeur de vos exportations en 2019")

    #rubrique : 19 contrainte  par ordre d'importance
    manque_personnel_qualifie = fields.Selection(string="a: Insuffisance de personnel qualifié", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_eleve_main_oeuvre = fields.Selection(string="b: Coût élevé de la main d'œuvre", selection=[('1', 'Oui'), ('0', 'Non')])
    formalite_administrative_contraignante = fields.Selection(string=" c: Formalités administratives contraignantes ", selection=[('1', 'Oui'), ('0', 'Non')])
    taxe_impot_eleve = fields.Selection(string=" d: Taxes et impôts trop élevés ", selection=[('1', 'Oui'), ('0', 'Non')])
    cout_tranport_eleve = fields.Selection(string=" e: Coût du transport élevé (FRET) ", selection=[('1', 'Oui'), ('0', 'Non')])
    mauvais_etat_infrastructure = fields.Selection(string=" f: Mauvais état des infrastructures routières ", selection=[('1', 'Oui'), ('0', 'Non')])
    difficulte_approvisionnement_matiere_premiere = fields.Selection(string="g: Difficultés d'approvisionnement en matières premières et autres intrants (quantité et qualité) ", selection=[('1', 'Oui'), ('0', 'Non')])
    procedure_contentieux = fields.Selection(string=" h: Lourdeurs des procédures de règlement des contentieux ", selection=[('1', 'Oui'), ('0', 'Non')])
    ecoulement_production = fields.Selection(string="i: Difficultés d'écoulement de la production/insuffisance de débouchés", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_au_technologie = fields.Selection(string="j: Manque/Faible accès aux technologies spécialisées", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_machine = fields.Selection(string="k: Manque de machines et pièces de rechange", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_expertise_technique = fields.Selection(string="l: Manque d’expertise technique (maintenance machines)", selection=[('1', 'Oui'), ('0', 'Non')])
    manque_local_adapte = fields.Selection(string="m: Manque de local adapté/terrain", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_commande_public = fields.Selection(string="n: Difficultés d'accès à la commande publique", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_structure_appui = fields.Selection(string="o: Accès limité aux structures d'appui aux entreprises", selection=[('1', 'Oui'), ('0', 'Non')])
    acces_credit_bancaire = fields.Selection(string="p: Difficultés d'accès au crédit (Banque et Microfinance)", selection=[('1', 'Oui'), ('0', 'Non')])
    approvisionnement_energie = fields.Selection(string="q: Difficultés d'approvisionnement en énergie", selection=[('1', 'Oui'), ('0', 'Non')])
    concurrence_deloyale = fields.Selection(string="r: Concurrence déloyale", selection=[('1', 'Oui'), ('0', 'Non')])
    corruption = fields.Selection(string="s: Corruption (racket, pot de vins, etc.)", selection=[('1', 'Oui'), ('0', 'Non')])
    autre_contrainte = fields.Selection(string="t Autre contrainte (à préciser)", selection=[('1', 'Oui'), ('0', 'Non')])
    precise_contrainte = fields.Char(string="u: Précisez la contrainte )")
    aucune_contrainte = fields.Selection(string="u. Aucune contrainte", selection=[('1', 'Oui'), ('0', 'Non')])

    #ajout champ informel
    autre_activte = fields.Selection(string="Autre activité secondaire? ", selection=[('1', 'Oui'), ('2', 'Non')])
    autre_activite_precision = fields.Char(string="Précisez l'activicté ")
    autre_local = fields.Char(string=" C18.a: Autre local à préciser")
    autre_moyen_comptable = fields.Char(string="C16.a: Autre moyen de comptabilité à préciser ")
    autre_status_local = fields.Char(string="C19.a: Autre statut de terrain à préciser ")
    code_ciap = fields.Char(string="Code CIAP (activité secondaire) ")
    communique_registre_metier = fields.Selection(string="Pouvez-vous nous communiquer ce numéro RM? ", selection=[('1', 'Oui'), ('2', 'Non')])
    connexion_internet = fields.Selection(string="C22: Votre entreprise/établissement dispose-t-elle/il d’une connexion internet ? ", selection=[('1', 'Oui'), ('2', 'Non')])
    contrainte_rencontre = fields.Many2many('innoving.contrainte.activite','innoving_partner_contrainte_rel', 'activite_id', 'contrainte_activite_id',
                                            string="E1: Quelles sont les principales contraintes que votre entreprise rencontre dans le cadre de votre activité (choix multiples) ?")
    declaration_cnps = fields.Selection(string="C15: Votre entreprise est-elle déclarée à la CNPS? ", selection=[('1', 'Oui'), ('2', 'Non')])
    designation_activite = fields.Char(string=" Désignation de l'activité")
    deux_1er_chiffre_rm = fields.Integer(string=" Saisir les 2 premièrs chiffres du RM")
    deux_1er_lettre_rm = fields.Char(string=" Saisir les 2 premières lettres du RM")
    deux_dernier_lettre_rm = fields.Char(string="Saisir les 2 dernières lettres du RM")
    doc_fin_exercice = fields.Selection(string="Votre entreprise produit-elle un document comptable en fin d’exercice ? ", selection=[('1', 'Oui'), ('2', 'Non')])
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
    effectif_total = fields.Integer(string=" D6 : Quel est l’effectif total de votre entreprise/établissement en 2021?")
    effectif_total_femme = fields.Integer(string=" D6a1f: Quel est l'effectif total femmes de votre entreprise/établissement en 2021")
    effectif_total_homme = fields.Integer(string=" D6a1h: Quel est l'effectif total hommes de votre entreprise/établissement en 2021 ?")
    effectif_total_nationaux_femme = fields.Integer(string=" D6a2f: Quel est l'effectif total des nationaux femmes en 2021 ?")
    effectif_total_nationaux_homme = fields.Integer(string=" D6a2h: Quel est l'effectif total des nationaux hommes en 2021 ?")
    etat_fonctionnement_entreprise = fields.Selection(string="C21 : Quel est l’état d’activité de l'entreprise ? ",
                                                      selection=[('1', 'En activité'),
                                                                ('2', 'En veille / Arrêt momentané'),
                                                                ('3', 'Activité en attente de démarrage'),
                                                                ('4', "Cessation d'activité")])
    etat_infrastructure = fields.Selection(string=" f: Mauvais état des infrastructures routières", selection=[('1', 'Oui'), ('0', 'Non')])
    import_produit = fields.Selection(string="D5: Importez-vous en partie ou en totalité vos marchandises ou matières premières ? ", selection=[('1', 'En partie'), ('2', 'En totalité'),('3', 'Non')])
    import_service = fields.Selection(string="D5: Importez-vous en partie ou en totalité vos produis ou services ? ", selection=[('1', 'En partie'), ('2', 'En totalité'),('3', 'Non')])
    local_activicte = fields.Selection(string=" C18: Dans quel type de local exercez-vous votre activité ? ",
                                       selection=[('1', 'Bureau / Bâtiment'),
                                                  ('2', 'Hangar'),
                                                  ('3', 'Baraque'),
                                                  ('4', 'Box'),
                                                  ('5', 'Magasin/Entrepôt'),
                                                  ('6', 'Local fixe dans un marché'),
                                                  ('7', 'A domicile'),
                                                  ('8', 'Carrière'),
                                                  ('9', 'Conteneur'),
                                                  ('10', 'A ciel ouvert'),
                                                  ('11', 'Autres à préciser')])
    masse_salariale_nationaux_permanent = fields.Float(string=" D6a3ms: Quel est la masse salariale des nationaux permanents en 2021 ?")
    masse_salariale_nationaux_temporaire = fields.Float(string=" D6a4ms: Quel est la masse salariale des nationaux Saisonniers/temporaires en 2021 ?")
    masse_salariale_non_nationaux_permanent = fields.Float(string=" D6a6ms: Quel est la masse salariale des non nationaux permanents en 2021 ?")
    masse_salariale_non_nationaux_temporaire = fields.Float(string=" D6a7ms: Quel est la masse salariale des non nationaux Saisonniers/temporaires en 2021 ?")
    masse_salariale_total = fields.Float(string=" D6a1ms: Quel est la masse salariale totale en FCFA de votre entreprise/établissement en 2021 ?")
    masse_salariale_total_nationaux = fields.Float(string=" D6a2ms: Quel est la masse salariale totale des nationaux de votre entreprise/établissement en 2021 ?")
    masse_salariale_total_non_nationaux = fields.Float(string=" D6a5ms: Quel est la masse salariale totale des non nationaux de votre entreprise/établissement en 2021 ?")
    montant = fields.Float(string=" Montant ")
    montant_charge_mensuelle = fields.Float(string=" D2. Quel est le montant total des charges mensuelles liées à votre activité (en FCFA) en 2021 ?")
    montant_total_actif = fields.Float(string=" D9 Quel est le montant total des Actif (en FCFA)")
    montant_total_actif_immobiliser = fields.Float(string=" D8 Quel est le montant total des Actifs immobilisés (en FCFA)")
    montant_total_capiteaux_propre = fields.Float(string=" D7 Quel est le montant total des Capitaux propres (en FCFA)")
    montant_total_charge_ordinaire = fields.Float(string=" D11 Quel est le montant total des charges ordinaires (en FCFA)")
    montant_total_impot_taxe = fields.Float(string=" D12 Quel est le montant total des Impôts et taxes (en FCFA)")
    montant_total_ressource_stable = fields.Float(string=" D10 Quel est le montant total des Ressources stables (en FCFA)")
    montant_vente_maximum_realiser = fields.Float(string=" D3.b: Quelles est le montant maximum de vos ventes mensuelles (en FCFA) réalisées au cours des 12 derniers mois ?")
    montant_vente_minimum_realiser = fields.Float(string=" D3.a: Quelles est le montant minimum de vos ventes mensuelles (en FCFA) réalisées au cours des 12 derniers mois ?")
    moyen_comptable = fields.Selection(string="C16 : Quel moyen principal utilisez-vous pour votre comptabilité ? ", selection=[
        ('1', 'Carnet ou cahier de dépenses et recettes'),
        ('2', 'Fiche de caisse informatiséeé'),
        ('3', 'Aucun'),
        ('4', 'Autre à préciser')])
    name_activite_secondaire = fields.Char(string="Désignation de l'activité secondaire ")
    nombre_etablissement = fields.Char(string="C20.b: Combien d’établissements avez-vous ? ")
    num_compte_contribuable = fields.Char(string="Si oui, donnez le numéro de compte contribuable ")
    num_registre_commerce = fields.Char(string="Si oui, donnez le numéro de registre de commerce ")
    num_registre_metier  = fields.Char(string="C14.a: Si oui, donnez le numéro de registre de métier ")
    numero_cnps = fields.Integer(string="C15.a: Si oui, donnez le numéro CNPS (en 7 chiffres) ")
    numero_cnps_communicable = fields.Selection(string="Pouvez-vous nous communiquer ce numéro CNPS? ", selection=[('1', 'Oui'), ('2', 'Non')])
    periodicite = fields.Selection(string=" Périodicité", selection=[('1', 'Jour'), ('2', 'Semaine'),('3','Mois'),('4','Année')])
    quatre_chiffre_rm = fields.Float(string=" Saisir les 4 chiffres précedents les 2 lettres saisies du RM", selection=[('1', 'Oui'), ('2', 'Non')])
    registre_metier = fields.Selection(string="C14: Votre entreprise dispose-t-elle d’un numéro de registre Métier (RM)? ", selection=[('1', 'Oui'), ('2', 'Non')])
    sept_chiffre_rm = fields.Integer(string="Saisir les 7 derniers chiffres du RM ")
    statut_comptabilite_formel = fields.Selection(string="Votre entreprise tient-elle, une comptabilité formelle écrite ? ", selection=[('1', 'Oui'), ('2', 'Non')])
    statut_compte_contribuable = fields.Selection(string="Votre entreprise dispose t-elle d'un numéro de compte contribuable(NCC)? ", selection=[('1', 'Oui'), ('2', 'Non')])
    statut_entreprise = fields.Selection(string="C20.a: Quel est le statut de votre entreprise/établissement ? ",
                                         selection=[('1', 'Établissement principal'),
                                                    ('2', 'Établissement secondaire'),
                                                    ('3', 'Établissement unique')])
    statut_local = fields.Selection(string="C19 : Quel est le statut du terrain sur lequel votre entreprise/établissement est localisé(e) ? ",
                                    selection=[('1', 'Occupation du domaine public'),
                                                ('2', 'Propriétaire du local/terrain'),
                                                ('3', 'Espace dédié autorisé'),
                                                ('4', 'Autre à préciser')])
    statut_registre_commerce = fields.Selection(string=" Votre entreprise dispose-t-elle d’un numéro de Registre de Commerce (RC)?", selection=[('1', 'Oui'), ('2', 'Non')])
    type_entreprise = fields.Selection(string="Votre structure est-elle une Organisation Non Gouvernemental (ONG) ou une Institution sans but lucratif (*)", selection=[('1', 'Oui'), ('2', 'Non')])
    utilisation_logiciel_metier = fields.Selection(string=" C21: Utilisez-vous des logiciels métiers au sein de votre entreprise/établissement ?", selection=[('1', 'Oui'), ('2', 'Non')])










