from odoo import fields, models, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    order_id = fields.Many2one(
        "sale.order",
        "Purchase",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    due_date = fields.Date('Due Date')
    # pay_rec = fields.Selection(related='journal_id.pay_rec',
    #                            string='PAY/REC')
    # journal_ids = fields.Many2many('account.journal', compute='_compute_journal_ids')

    # @api.depends('payment_type')
    # def _compute_journal_ids(self):
    #     for rec in self:
    #         payable = self.env['account.journal'].search(
    #             ['&', ('type', 'in', ['bank', 'cash']), ('pay_rec', '=', 'payable')])
    #         receivable = self.env['account.journal'].search(
    #             ['&', ('type', 'in', ['bank', 'cash']), ('pay_rec', '=', 'receivable')])
    #         if rec.payment_type == 'inbound':
    #             # rec.journal_id = False
    #             rec.journal_ids = receivable.ids
    #         else:
    #             # rec.journal_id = False
    #             rec.journal_ids = payable.ids
