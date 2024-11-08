# -*- coding: utf-8 -*-
{
    'name': "sale_customization",
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
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['base','sale','marquespoint_overall','sale_management', 'pdc_payments', 'unit_customiztion'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/so_tenant_contract_view.xml',
        'views/so_rent_installment_flow_view.xml',
        'wizard/rent_installment_wizard_view.xml',
        'wizard/pdc_payment_wizard_views.xml',
        # 'views/sale_search_pannel.xml',
    ],
}
