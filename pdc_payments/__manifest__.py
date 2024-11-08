# -*- coding: utf-8 -*-
{
    'name': "PDC Payments",
    'summary': """
        PDC Payments Cheque Print""",
    'description': """
        PDC Payments Cheque Print
    """,
    'author': "Viltco",
    'website': "http://www.viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'marquespoint_overall', 'account_edi'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/pdc_sequence.xml',
        'data/pdc_payment_cron.xml',
        'security/security.xml',
        'reports/pdc_payment_report.xml',
        'reports/pdc_payment_template.xml',
        'wizards/pdc_payment_wizard_views.xml',
        'wizards/pdc_recall_wizard_view.xml',
        'wizards/pdc_bounce_wizard_view.xml',
        'views/pdc_payment_views.xml',
        'views/res_config_setting_view.xml',
        'views/account_move_view.xml',
    ],
}
