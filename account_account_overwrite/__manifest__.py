# -*- coding: utf-8 -*-

{
    'name': 'Account Overwrite',
    'version': '17.0',
    'description': 'Account Receivable/Payable',
    'author': 'cognitive',
    'depends': ['base', 'pdc_payments', 'marquespoint_overall'],
    'category': 'Accounting',
    'demo': [],
    'data': [
        'views/payment_view.xml',
        'views/pdc_payment_view.xml',
        'views/pdc_payment_wizard.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
