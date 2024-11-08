# -*- coding: utf-8 -*-
{
    "name": "Local Purchase Order Report",
    "author": "Cognitive",
    "category": "purchase",
    "license": "OPL-1",
    "version": "17.0.1.0.0",
    "depends": [
        'purchase', 'crm', 'ol_property_custom', 'marquespoint_overall', "ol_sales_agreement_report"
    ],
    "data": [
        'reports/report.xml',
        'reports/local_po_report.xml',
        'views/purchase_order.xml',
        'views/project_project.xml',
        'views/res_users.xml',
        'views/res_partner.xml',
    ],
    "images": [],
    "auto_install": False,
    "application": True,
    "installable": True,
}
