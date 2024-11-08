# -*- coding: utf-8 -*-
{
    'name': "property_performance_reports",
    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'marquespoint_overall', 'ol_property_custom', 'sale_cancellation_report'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/property_performance_report_views.xml',
        'report/report.xml',
        'report/property_performance_report_template.xml',
        # 'report/debit_note_template.xml',
        # 'report/sale_quote_report_template_rent.xml',
        # 'report/tax_invoice_template.xml',
        # 'report/addendum_report_template.xml',
        # 'report/invoice_reports_inherit.xml',
        # 'views/views.xml',
        # 'views/sale_order.xml',
        # 'views/unit_views.xml',
        # 'views/res_partner.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
