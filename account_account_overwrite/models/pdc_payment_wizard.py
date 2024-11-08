# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PDCPaymentWizard(models.TransientModel):
    _inherit = 'pdc.payment.wizard'

    is_overwrite = fields.Boolean(string="Overwrite Receivables/Payables Account")
    overwite_account_id = fields.Many2one(comodel_name='account.account', string='Account')

    def create_pdc_payments(self):
        for record in self:
            if record.pdc_type == 'received':
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    'destination_account_id': record.destination_account_id.id,
                    'currency_id': record.currency_id.id,
                    'commercial_bank_id': record.commercial_bank_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'received',
                    'is_overwrite': record.is_overwrite,
                    'overwite_account_id': record.overwite_account_id.id,
                    'purchaser_id': record.purchaser_id.id,
                    'memo': record.memo,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'cheque_type_id': record.cheque_type_id.id,
                    'order_id': record.order_id.id,
                }
                record = self.env['pdc.payment'].create(vals)
                if record.unit_id:
                    for unit in record.unit_id:
                        record.write({'unit_id': unit})
                if record:
                    if self.pdc_payment_id:
                        self.pdc_payment_id.write({'state': 'cancel'})
                        for rec in self.pdc_payment_id.get_jv:
                            rec.button_draft()
                            rec.button_cancel()
            elif record.pdc_type == 'sent':
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    'destination_account_id': record.journal_id.default_account_id.id,
                    'currency_id': record.currency_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'sent',
                    'memo': record.memo,
                    'is_overwrite': record.is_overwrite,
                    'overwite_account_id': record.overwite_account_id.id,
                    'purchaser_id': record.purchaser_id.id,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'cheque_type_id': record.cheque_type_id.id,
                    'order_id': record.order_id.id,
                }
                record = self.env['pdc.payment'].create(vals)
                if record.unit_id:
                    for unit in record.unit_id:
                        record.write({'unit_id': unit.id})
                if record:
                    if self.pdc_payment_id:
                        self.pdc_payment_id.write({'state': 'cancel'})
                        for rec in self.pdc_payment_id.get_jv:
                            rec.button_draft()
                            rec.button_cancel()
            for r in self.move_ids:
                r.is_pdc_created = True