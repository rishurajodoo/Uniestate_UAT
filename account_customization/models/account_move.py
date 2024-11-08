from odoo import models, api, fields, _
import json
import logging

class AccountMove(models.Model):
    _inherit = 'account.move'


    def reconcile_line_payment(self, line_id):
        self.ensure_one()
        lines = self.env['account.move.line'].browse(line_id)
        lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
        lines.reconcile()
        return True


    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type == 'out_invoice':
            payment = self.env['account.payment'].search([('partner_id', '=', self.partner_id.id),
                                                          ('ref', '=', self.name)], limit=1)
            if payment:
                self.reconcile_line_payment(payment.line_ids.ids[-1])


        return res

