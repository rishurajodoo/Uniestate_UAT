
# -*- coding: utf-8 -*-
{
    'name': "Tenancy Contract",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Aswin",
    'website': "https://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'unit_customiztion'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/report_action.xml',
        'report/tenancy_contract_report.xml',
        'report/external_layout_changes.xml',
        'views/sale_order_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
