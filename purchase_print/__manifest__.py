{
    'name': 'Purchase Print',
    'author': 'Developed by ',
    'summary': 'Purchase Order Print',
    'website': 'www.example.com',
    'depends': ['base', 'purchase', 'project'],
    'category': 'Purchase',
    'data': [
        'views/purchase_order_views.xml',
        'views/project_views.xml',
        'report/report.xml',
        'report/purchase_order_report.xml',
    ],
    "auto_install": False,
    "application": True,
    "installable": True,
}