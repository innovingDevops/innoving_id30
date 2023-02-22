# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'innoving id30',
    'version': '1.0',
    'summary': "Identification des entreprenants ivoiriens",
    'sequence': 15,
    'autor':'Innoving',
    'description': """
Gestion d'identification des entreprenants ivoirien ...
====================
The specific and easy-to-use Invoicing system in Odoo allows you to keep track of your accounting, even when you are not an accountant. It provides an easy way to follow up on your vendors and customers.

You could use this simplified accounting in case you work with an (external) account to keep your books, and you still want to keep track of payments. This module also offers you an easy method of registering payments, without having to encode complete abstracts of account.
    """,
    'category': 'documents,project',
    'website': 'https://www.innoving.info/',
    'images': [''],
    'depends': ['base_setup','base','mass_mailing','account'],
    'data': [
        'security/group_security.xml',
        'security/ir.model.access.csv',
        #'data/data_sequence.xml',  
        'views/cluster_view.xml',
        'views/commune_view.xml',
        'views/departement_view.xml',
        'views/entreprenant_view.xml',
        'views/ilot_view.xml',
        'views/localite_view.xml',
        'views/quartier_view.xml',
        'views/region_view.xml',
        'views/sous_prefecture_view.xml',
        'views/zone_recensement_view.xml', 
        'views/res_users_view.xml',
        'views/equipe_identificateur_view.xml',
        'views/affectation_view.xml',
        'views/activite_secteur_view.xml',
        'views/type_activite_view.xml',
        'views/res_partner_view.xml',
        'views/district_view.xml',
        'views/menu_view.xml',
    ],
    'demo': [
    ],
    'js': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'post_init_hook': '_auto_install_l10n',
}
