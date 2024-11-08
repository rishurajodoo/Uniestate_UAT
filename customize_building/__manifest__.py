# -*- coding: utf-8 -*-
{
    'name': "Customize Building",
    'summary': """This module is all about building customization""",
    'description': """
    In this module we add one2many field in to wizard when creating building from project 
    """,
    'author': "Cognitive Force",
    'category': 'Uncategorized',
    "version": "17.0.1.0.0",
    'depends': ['base', 'ol_property_custom', 'project_customization', 'account', 'account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_asset_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
