# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PDCPayment(models.Model):
    _inherit = 'pdc.payment'

    is_overwrite = fields.Boolean(string="Overwrite Receivables/Payables Account")
    overwite_account_id = fields.Many2one(comodel_name='account.account', string='Account')

    @api.model
    def create(self, vals):
        record = super(PDCPayment, self).create(vals)
        move_id = self.env['account.move'].search([('pdc_registered_id', '=', record.id)])
        for rec in move_id.line_ids:
            if record.partner_id and record.overwite_account_id :
                if record.pdc_type == 'received':
                    if record.partner_id.property_account_receivable_id == rec.account_id:
                        rec.write({'account_id': record.overwite_account_id.id})
                if record.pdc_type == 'sent':
                    if record.partner_id.property_account_payable_id == rec.account_id:
                        rec.write({'account_id': record.overwite_account_id.id})
        return record

    def write(self, vals):
        result = super(PDCPayment, self).write(vals)
        for record in self:
            if record.overwite_account_id and record.move_id.line_ids:
                for rec in record.move_id.line_ids:
                    if record.pdc_type == 'received':
                        if record.partner_id.property_account_receivable_id == rec.account_id:
                            rec.write({'account_id':record.overwite_account_id.id})
                    if record.pdc_type == 'sent':
                        if record.partner_id.property_account_payable_id == rec.account_id:
                            rec.write({'account_id': record.overwite_account_id.id})
        return result
