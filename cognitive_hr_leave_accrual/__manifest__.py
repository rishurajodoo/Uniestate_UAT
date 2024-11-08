# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Dynexcel (<http://dynexcel.com/>).
#
##############################################################################
{
    'name': 'Leave Allocation Automatically',
    'version': '17.0',
    'summary': '',
    'description': 'T',
    'author': 'Vrindha',
    'depends': ['base', 'hr_holidays'],
    'category': 'Accounting',
    'demo': [],
    'data': [
            'views/hr_leave_accrual.xml'
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
