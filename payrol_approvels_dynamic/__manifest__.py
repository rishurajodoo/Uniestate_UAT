{
    'name': 'Payrol Approvel Dynamic',
    'author': 'Developed by Jawad Ali',
    'summary': 'For management of Sales Approvel Dynamic',
    'website': 'www.example.com',
    'depends': ['base', 'mail', 'hr_payroll', 'hr_payroll_account'],
    'category': 'Purchase',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/hr_payroll_approval.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_run.xml',
    ]
}