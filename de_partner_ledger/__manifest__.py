# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Dynexcel (<http://dynexcel.com/>).
#
##############################################################################
{
    'name': 'Partner Ledger',
    'version': '17.0',
    'summary': 'This module will add Partner Ledger Report',
    'description': 'This module provides the movement of individual products with opening and closing stocks',
    'author': 'Vrindha',
    'depends': ['base', 'account', 'contacts', 'pdc_payments'],
    'category': 'Accounting',
    'demo': [],
    'data': ['views/partner_ledger_views.xml',
             'security/ir.model.access.csv',
             'report/partner_ledger_report.xml',

             'report/partner_ledger_report_template_final.xml',

             # 'report/partner_ledger_report_template.xml',
             ],
    'installable': True,
    'images': ['static/description/banner.png'],
    'qweb': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
