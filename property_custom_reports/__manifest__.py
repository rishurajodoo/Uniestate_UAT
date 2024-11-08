# -*- coding: utf-8 -*-
{
    'name': "property_custom_reports",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'account', 'unit_customiztion'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/property_custom_report_views.xml',
        'report/report.xml',
        'report/tenancy_contract_ejari_template.xml',
        'report/debit_note_template.xml',
        'report/sale_quote_report_template_rent.xml',
        'report/tax_invoice_template.xml',
        'report/addendum_report_template.xml',
        'report/invoice_reports_inherit.xml',
        'views/views.xml',
        'views/sale_order.xml',
        'views/unit_views.xml',
        # 'views/res_partner.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
