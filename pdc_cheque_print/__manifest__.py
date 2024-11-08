# -*- coding: utf-8 -*-
{
    'name': "PDC Payments",
    'summary': """
        PDC Cheque Print""",
    'description': """
        PDC Cheque Print
    """,
    'author': "Viltco",
    'website': "http://www.viltco.com",
    'category': 'Accounting',
    "version": "17.0.1.0.0",
    'depends': ['pdc_payments'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cheque_type.xml',
        'reports/cheque_format_reports.xml',
        'reports/cheque_format_templates.xml',
        'views/pdc_payment_cheque.xml',
        'views/pdc_form.xml',

    ],
}
