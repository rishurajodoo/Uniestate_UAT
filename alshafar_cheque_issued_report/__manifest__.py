# -*- coding: utf-8 -*-
{
    'name': "Alshafar Cheque Issued Report",

    'summary': """This module is all about PDC cheque report""",

    'description': """
    This module is all about PDC cheque report
    """,

    'author': "CognitiveForce",

    'depends': ['base', 'pdc_payments'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'wizard/report_wizard.xml',
        'wizard/onhand_report_wizard.xml',
        'report/repor_action.xml',
    ],
}
