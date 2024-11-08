{
    'name': 'Maintenance Approvel Dynamic',
    'summary': 'For management of Maintenance Approvel Dynamic',
    'website': 'www.example.com',
    'depends': ['base', 'mail', 'sale','maintenance_customization'],
    'category': 'Maintenance',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/sales_approvals.xml',
    ]
}