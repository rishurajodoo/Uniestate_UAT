# -*- coding: utf-8 -*-
{
    'name': "Unit Customiztion",
    'summary': """This module is all about unit customization or product variants""",
    'description': """
    This module is all about unit customization or product variants
    """,
    'author': "Cognetive Force",
    'category': 'Uncategorized',
    "version": "17.0.1.0.0",
    'website': "http://www.yourcompany.com",
    'depends': ['base', 'stock', 'project_customization', 'ol_property_custom', 'marquespoint_overall',
                'customize_building', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product_search_panel.xml',
        'wizard/unit_wizard_view.xml',
    ],
}
