# -*- coding: utf-8 -*-
{
    'name': 'Website Customization',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Website customization',
    'depends': ['website','website_sale','sale_management', 'unit_customiztion'],
    'data': [
        'data/website_data_views.xml',
        'views/template.xml',
        'views/website_sale_views.xml',
        'views/enquire_form_template.xml',
    ],
    'installable': True,
    'application': False,
}
