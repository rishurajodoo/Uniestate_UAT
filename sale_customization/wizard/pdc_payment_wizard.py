from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PDCPaymentWizard(models.TransientModel):
    _name = 'pdc.sale.wizard'
    _description = 'PDC Payment'

    partner_id = fields.Many2one('res.partner', string='Partner', )
    payment_amount = fields.Float(string='Payment Amount')
    # cheque_ref = fields.Char(string='Commercial Name')
    commercial_bank_id = fields.Many2one('pdc.commercial.bank', string='Commercial Bank Name', tracking=True)
    memo = fields.Char(string='Memo')
    destination_account_id = fields.Many2one('account.account', string='Bank')
    journal_id = fields.Many2one('account.journal', string='Journal')
    currency_id = fields.Many2one('res.currency', string='Currency')
    pdc_type = fields.Selection([('sent', 'Sent'),
                                 ('received', 'Received'),
                                 ], string='PDC Type', )

    date_payment = fields.Date(string='Due Date')
    date_registered = fields.Date(string='Registered Date')
    cheque_no = fields.Char()
    move_id = fields.Many2one('account.move', string='Invoice/Bill Ref')
    move_ids = fields.Many2many('account.move', string='Invoices/Bills Ref')
    cheque_type_id = fields.Many2one('cheque.type', string='Cheque Type')
    unit_id = fields.Many2one('product.product', string='Unit')
    floor_id = fields.Many2one('property.floor', string='Floor')
    building_id = fields.Many2one('property.building', string='Building')
    project_id = fields.Many2one('project.project', string='Project')
    purchaser_id = fields.Many2one(comodel_name='res.partner', string='Purchaser')


    @api.onchange('journal_id')
    def _onchange_journal(self):
        for rec in self:
            if rec.journal_id:
                rec.destination_account_id = rec.journal_id.default_account_id.id

    def create_pdc_payments(self):
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        for record in self:
            if record.pdc_type == 'received':
                self.env['rent.installment.line'].search(
                    [('milestone_id', '=', active_id.milestone_id.id),
                     ('order_id', '=', active_id.order_id.id)]).unlink()
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    # 'move_id': active_id.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    # 'destination_account_id': record.journal_id.default_account_id.id,
                    'destination_account_id': record.destination_account_id.id,
                    'currency_id': record.currency_id.id,
                    'commercial_bank_id': record.commercial_bank_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'received',
                    'cheque_type_id': record.cheque_type_id.id,
                    'unit_id': record.unit_id.id,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'order_id': active_id.order_id.id
                }
                record = self.env['pdc.payment'].create(vals)
                active_id.pdc_payment_id = record.id
                vals = {
                    'milestone_id': active_id.milestone_id.id,
                    # 'amount': self.amount / self.no_of_cheques,
                    'order_id': active_id.order_id.id,
                    'pdc_payment_id': record.id,
                    # 'date': inv_date
                }
                self.env['rent.installment.line'].create(vals)
            elif record.pdc_type == 'sent':
                vals = {
                    'partner_id': record.partner_id.id,
                    'journal_id': record.journal_id.id,
                    # 'move_id': active_id.id,
                    'move_ids': record.move_ids.ids,
                    'date_payment': record.date_payment,
                    'date_registered': record.date_registered,
                    'destination_account_id': record.journal_id.default_account_id.id,
                    'currency_id': record.currency_id.id,
                    'payment_amount': record.payment_amount,
                    'cheque_no': record.cheque_no,
                    'pdc_type': 'sent',
                    'purchaser_id': record.purchaser_id.id,
                    'unit_id': record.unit_id.id,
                    'floor_id': record.floor_id.id,
                    'building_id': record.building_id.id,
                    'project_id': record.project_id.id,
                    'cheque_type_id': record.cheque_type_id.id,
                }
                record = self.env['pdc.payment'].create(vals)
                active_id.pdc_payment_id = record.id
