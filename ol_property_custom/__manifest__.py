{
    "name": "Property",

    "author": "Cognitive",
    'Maintainer': "M.Rizwan",
    "license": "OPL-1",
    'category': 'Customizations',
    "version": "17.0.1.0.0",

    "depends": [
        'project', 'sale_management', 'contacts', 'product', 'crm', 'sale_crm', 'account',
        'stock', 'sale_commission'],

    "data": [
        'security/ir.model.access.csv',
        'wizard/create_building.xml',
        'views/so_inherit.xml',
        'views/main_view.xml',
        'views/fields.xml',
        'views/installment_invoice_button.xml',
        'views/res_config_settings_view.xml',

    ],

    "images": [['static/description/icon.png']],
    "auto_install": False,
    "application": True,
    "installable": True,
}
