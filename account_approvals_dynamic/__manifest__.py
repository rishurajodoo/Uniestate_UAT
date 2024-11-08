{
    'name': 'Account Approvel Dynamic',
    'summary': 'For management of Account Approvel Dynamic',
    'website': 'www.example.com',
    'depends': ['base', 'mail', 'account'],
    'category': 'account',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/account_move.xml',
        'views/account_approvals.xml',
    ]
}