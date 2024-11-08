# -*- coding: utf-8 -*-
{
    'name': "snd_petty_cash",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "M.Rizwan",
    'website': "https://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/snd_petty_cash_sequence.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
