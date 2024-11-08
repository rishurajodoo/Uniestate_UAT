# -*- coding: utf-8 -*-
{
    'name': "Floor Customization",
    'summary': """This module is all about floor customization""",
    'description': """
    This module is all about floor customization
    """,
    'author': "Cognetive Fore",
    'category': 'Uncategorized',
    "version": "17.0.1.0.0",
    'depends': ['base', 'ol_property_custom', 'project_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'wizard/floor_wizard.xml',
    ],
}
