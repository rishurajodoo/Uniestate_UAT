from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PDCRecallWizard(models.TransientModel):
    _name = 'pdc.recall.wizard'
    _description = 'PDC Recall'

    product_id = fields.Many2one('product.product', string="Product")
    penalty_amount = fields.Float(string="Panelty Amount")
    invoice_policy = fields.Selection([('to_be_invoiced_separately', 'To Be Invoiced Separately'),
                                       ('to_be_invoiced_in_existing', 'To Be Invoiced In Existing')],
                                      string="Invoicing Policy", required=True)
    pay_by = fields.Selection([('cash', 'Cash'),
                               ('cheque', 'Cheque')], string="Pay By", required=True)
    time_interval = fields.Char(string="Time Interval", readonly=True)
    cheque_date = fields.Date(string="Cheque Date")
    pdc_cheque_id = fields.Many2one('pdc.payment')

    @api.onchange('cheque_date')
    def compute_timeInterval(self):
        interval = self.cheque_date - datetime.today().date()
        self.time_interval = str(interval.days)

    def create_pdc_recall(self):
        account_invoive_id = False
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if self.invoice_policy == 'to_be_invoiced_separately':
            move_dict = {}
            move_dict['partner_id'] = self.pdc_cheque_id.partner_id.id
            move_dict['journal_id'] = journal.id
            move_dict['move_type'] = 'out_invoice'
            move_dict['unit'] = self.pdc_cheque_id.unit_id.ids
            move_dict['project'] = self.pdc_cheque_id.project_id.id
            move_dict['floor'] = self.pdc_cheque_id.floor_id.id
            move_dict['building'] = self.pdc_cheque_id.building_id.id
            move_dict['so_ids'] = self.pdc_cheque_id.order_id.id
            move_dict['pdc_recall_id'] = self.pdc_cheque_id.id
            invoice_id = self.env['account.move'].create(move_dict)
            line_lst = []
            move_line = {}
            move_line['product_id'] = self.product_id.id
            move_line['price_unit'] = self.penalty_amount
            line_lst.append((0, 0, move_line))
            invoice_id.invoice_line_ids = line_lst
            account_invoive_id = invoice_id
            self.pdc_cheque_id.move_ids = [(4, invoice_id.id)]
        else:
            if not self.pdc_cheque_id:
                raise ValidationError(_("No Invoice Is Attached!"))
            elif not self.pdc_cheque_id.move_ids.filtered(lambda x: x.state == 'draft'):
                raise ValidationError(_("No Invoice Is In Draft!"))
            else:
                move_lst = []
                for rec in self.pdc_cheque_id.move_ids:
                    move_lst.append(rec.id)
                invoice_id = min(move_lst)
                move_id = self.env['account.move'].search([('id', '=', invoice_id)])
                move_id.write({'pdc_recall_id': self.pdc_cheque_id.id})
                line_lst = []
                move_line = {}
                move_line['product_id'] = self.product_id.id
                move_line['price_unit'] = self.penalty_amount
                line_lst.append((0, 0, move_line))
                # move_id.invoice_line_ids.write(move_line)
                move_id.write({'invoice_line_ids': line_lst})
                account_invoive_id = move_id
        # if self.pay_by == 'cash':
        #     account_invoive_id.action_post()
        #     return account_invoive_id.action_register_payment()
        # else:
        return account_invoive_id.action_pdc_payment_wizard(amount=self.penalty_amount)

    def register_full_amount_by_cash(self):
        # self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id')).journal_id
        active_id = self.env.context.get('active_id')
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        pdc_payment_id = self.env[self.env.context.get('active_model')].browse(active_id)
        if pdc_payment_id:
            pdc_payment_id.move_ids.filtered(lambda l: l.state == 'draft')
            if self.pay_by == 'cash' and self.invoice_policy == 'to_be_invoiced_separately':
                move_dict = {}
                move_dict['partner_id'] = self.pdc_cheque_id.partner_id.id
                move_dict['journal_id'] = journal.id
                move_dict['move_type'] = 'out_invoice'
                move_dict['unit'] = self.pdc_cheque_id.unit_id.ids
                move_dict['project'] = self.pdc_cheque_id.project_id.id
                move_dict['floor'] = self.pdc_cheque_id.floor_id.id
                move_dict['building'] = self.pdc_cheque_id.building_id.id
                move_dict['so_ids'] = self.pdc_cheque_id.order_id.id
                move_dict['pdc_recall_id'] = self.pdc_cheque_id.id
                invoice_id = self.env['account.move'].create(move_dict)
                line_lst = []
                move_line = {}
                move_line['product_id'] = self.product_id.id
                move_line['price_unit'] = self.penalty_amount
                line_lst.append((0, 0, move_line))
                invoice_id.invoice_line_ids = line_lst
                account_invoive_id = invoice_id
                self.pdc_cheque_id.move_ids = [(4, invoice_id.id)]
                pdc_payment_id.state = 'cancel'
                return {
                    'name': _('Invoice'),
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', pdc_payment_id.move_ids.ids)],
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                }
            # pdc_payment_id.journal_id
        print("Hello")
