# -*- coding: utf-8 -*-
{
    'name': "ALSHAFAR Cheque Receipt Voucher",

    'summary': """This module is about cheque receipt voucher""",

    'description': """
        This module is about cheque receipt voucher
    """,

    'author': "CognitiveForce",

    'depends': ['base', 'pdc_payments', 'account'],

    'data': [
        # 'security/ir.model.access.csv',
        'report/report_action.xml',
        'report/report_temp.xml',
        'report/cheque_payment_report.xml',
    ],

}
