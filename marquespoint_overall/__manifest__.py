# -*- coding: utf-8 -*-
{
    'name': "CognitiveForce Property",
    'summary': """
       """,
    'description': """
    """,
    'author': "CognitiveForce",
    'version': '17.0.1.0.0',
    'depends': ['base', 'product', 'sale', 'ol_property_custom', 'project', 'crm', 'account', 'mail', 'account_asset',
                'maintenance'],
    # always loaded
    'data': [
        'wizard/installment_wizard_view.xml',
        "wizard/sale_advance_payment_wizard_view.xml",
        "wizard/cancel_sale_views.xml",
        "wizard/installment_no_calculate.xml",
        'security/ir.model.access.csv',
        'security/groups_security.xml',
        'data/server.xml',
        'report/inherited_external_layout.xml',
        'report/sale_quote_report_template.xml',
        'report/report.xml',
        'data/mail_template_data.xml',
        'data/mail_type.xml',
        'views/product_template_view.xml',
        'views/payment_plan_view.xml',
        'views/sale_order_view.xml',
        'views/payment_view.xml',
        'views/purchaser_flow_views.xml',
        'views/tenancy_contract_view.xml',
        'views/account_assets_view.xml',
        'views/mantinance_request_view.xml',
        'views/sale_cancel_reason_views.xml',
        'views/res_config_settings_views.xml',
        'views/project_views.xml',
        'views/account_move_views.xml',
        'views/payment_plan_line.xml',
        'wizard/sale_reschedule_approval.xml'
    ],
}
