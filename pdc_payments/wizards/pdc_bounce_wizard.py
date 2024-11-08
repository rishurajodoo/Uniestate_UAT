from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PDCBounceWizard(models.TransientModel):
    _name = 'pdc.bounce.wizard'
    _description = 'PDC Bounce'

    product_id = fields.Many2one('product.product')
    penalty_amount = fields.Float(string="Panelty Amount")
    cheque_no = fields.Char(string="Cheque No")
    invoice_policy = fields.Selection([('to_be_invoiced_separately', 'To Be Invoiced Separately'),
                                       ('to_be_invoiced_in_existing', 'To Be Invoiced In Existing')],
                                      string="Invoicing Policy", required=True)
    previous_cheque_ids = fields.Many2many('pdc.payment',string="Previous Bounced Cheque")
    pdc_cheque_id = fields.Many2one('pdc.payment')

    def create_bounce(self):
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
                move_id.write({'pdc_recall_id':self.pdc_cheque_id.id})
                line_lst = []
                move_line = {}
                move_line['product_id'] = self.product_id.id
                move_line['price_unit'] = self.penalty_amount
                line_lst.append((0, 0, move_line))
                # move_id.invoice_line_ids.write(move_line)
                move_id.write({'invoice_line_ids': line_lst})
                account_invoive_id = move_id
        self.pdc_cheque_id.write({'state':'bounced'})
        if self.pdc_cheque_id.state == 'bounced':
            self.pdc_cheque_id.action_bounce_jv()
        jv_ids = self.env['account.move'].search([('pdc_registered_id', '=', self.id)])
        for jv in jv_ids:
            jv.write({'state':'cancel'})


    @api.depends('pdc_cheque_id')
    def _compute_cheque_domain(self):
        self.previous_cheque_ids = False
        domain = []
        # if self.department_ids:
        #     domain.append(('department_id', 'in', self.department_ids.ids))
        # if self.category_ids:
        domain.append(('id', '=', 1))
        return {'domain': {'previous_cheque_ids': domain}}

    @api.onchange('cheque_no')
    def update_panality_amount(self):
        if self.previous_cheque_ids:
            match = False
            for rec in self.previous_cheque_ids:
                if rec.cheque_no == self.cheque_no:
                    match = True
                    break
            if match:
                self.penalty_amount = self.env['ir.config_parameter'].sudo().get_param('pdc_payments.pdc_already_bounce_check')
            else:
                self.penalty_amount = self.env['ir.config_parameter'].sudo().get_param('pdc_payments.pdc_first_bounce')

        else:
            self.penalty_amount = self.env['ir.config_parameter'].sudo().get_param('pdc_payments.pdc_first_bounce')
