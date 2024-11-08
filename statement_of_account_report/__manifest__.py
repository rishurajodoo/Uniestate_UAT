# -*- coding: utf-8 -*-
{
    'name': "statement_of_account_report",

    'summary': """
        Statement of Account for Marquis Point Installment Plan lines""",

    'description': """
        Statement of Account
    """,

    'author': "M.Rizwan",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'marquespoint_overall'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/soa_template.xml',
        'report/report.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
