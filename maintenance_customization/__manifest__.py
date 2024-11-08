# -*- coding: utf-8 -*-
{
    'name': "maintenance_customization",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "M.Rizwan",
    'website': "http://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Maintenance',
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    'depends': ['base', 'maintenance', 'ol_property_custom', 'unit_customiztion', 'snd_petty_cash', 'hr_maintenance', 'stock', 'product', 'account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/maintenance_operation_type_view.xml',
        'views/maintenance_request_view.xml',
        'views/product_product_inherited.xml',
        'views/petty_cash_inherited_id.xml',
        'views/spare_parts_view.xml',
        'views/stock_picking_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
