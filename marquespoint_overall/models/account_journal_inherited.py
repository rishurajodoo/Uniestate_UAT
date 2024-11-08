from odoo import models, fields


class AccountJournalInherited(models.Model):
    _inherit = 'account.journal'

    pay_rec = fields.Selection([
        ('payable', 'Payable'),
        ('receivable', 'Receivable'),
    ], string='PAY/REC', default=False)

