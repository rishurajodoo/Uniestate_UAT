{
    'name': 'Purchase Approvel Dynamic',
    'author': 'Developed by Jawad Ali',
    'summary': 'For management of Sales Approvel Dynamic',
    'website': 'www.example.com',
    'depends': ['base', 'mail', 'purchase'],
    'category': 'Purchase',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        # 'data/example_sequenc.xml',
        # 'wizard/file.xml',
        'views/manu.xml',
        'views/sales_approvals.xml',
        # 'report/report.xml',
    ]
}