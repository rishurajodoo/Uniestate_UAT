# -*- coding: utf-8 -*-
{
    'name': "Alshafar Payment Voucher",

    'summary': """This module is all about payment voucher""",

    'description': """
    This module is all about payment voucher
    """,

    'author': "CognitiveForce",
    'depends': ['base', 'pdc_payments'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/payment_temp.xml',
    ],
}
