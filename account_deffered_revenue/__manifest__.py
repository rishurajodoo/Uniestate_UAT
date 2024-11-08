{
    "name": "Property",
    "author": "Cognitive",
    "license": "OPL-1",
    'category': 'Customizations',
    "version": "17.0.1.0.0",
    "depends": ['account', 'sale_management', 'ol_property_custom', 'marquespoint_overall', 'base', 'sale', 'analytic'],
    "data": [
        'security/ir.model.access.csv',
        'views/deffered_revenue.xml',
        'views/sale_order.xml',
        'wizard/deffered_revenue_wizard.xml',
        # 'wizard/deffered_close_and_credit_note.xml'
    ],
    "auto_install": False,
    "application": True,
    "installable": True,
}
