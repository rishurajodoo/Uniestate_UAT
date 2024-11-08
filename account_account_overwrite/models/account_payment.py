# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_overwrite = fields.Boolean(string="Overwrite Receivables/Payables Account")
    overwite_account_id = fields.Many2one(comodel_name='account.account', string='Account')

    @api.model
    def create(self, vals):
        record = super(AccountPayment, self).create(vals)
        if record.overwite_account_id and record.move_id.line_ids and len(record.move_id.line_ids) > 1:
            line_id = record.move_id.line_ids[1]
            line_id.sudo().write({'account_id': record.overwite_account_id.id})
        return record

    def write(self, vals):
        result = super(AccountPayment, self).write(vals)
        for record in self:
            if record.overwite_account_id and record.move_id.line_ids and len(record.move_id.line_ids) > 1:
                line_id = record.move_id.line_ids[1]
                line_id.sudo().write({'account_id': record.overwite_account_id.id})
        return result
