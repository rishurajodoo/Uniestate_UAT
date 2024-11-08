import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class DefferedCloseAndCreditNoteWizard(models.TransientModel):
    _name = 'deffered.revenue.credit.wizard'
    _description = 'Deffered Revenue Credit Wizard'

    early_termination_period = fields.Selection([
        ('01', '1'),
        ('02', '2'),
        ('03', '3'),
        ('04', '4'),
        ('05', '5'),
        ('06', '6'),
        ('07', '7'),
        ('08', '8'),
        ('09', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12')], string='Early Termination Period', default='01')
    early_termination_penalty_amount = fields.Float(string='Early Termination Penalty')
    refundable_amount = fields.Float(string='Refundable Amount')
    termination_date = fields.Date(string='Termination Date')
    sale_order_id = fields.Many2one('sale.order')
    deffered_revenue_id = fields.Many2one('deffered.revenue')

    def close_and_create_credit(self):
        sale_order = self.sale_order_id
        # if self.approve_stage == 'approved':
        #     raise ValidationError("Mantinance Request Already Approved")
        for tenancy in sale_order.tenancy:
            if tenancy.approve_stage != 'approved':
                tenancy.approve_stage = 'approved'
                tenancy.approve_by = self.env.user.id
                tenancy.approve_date = fields.Date.today()
        for rec in sale_order:
            bill = {
                'partner_id': rec.partner_id.id,
                'invoice_date': rec.date_order,
                'project': rec.project.id,
                'building': rec.building.id,
                'floor': rec.floor.id,
                'unit': rec.unit.ids,
                'order_id': rec.id,
                'state': 'draft',
                'move_type': 'out_refund',
            }
            invoice_line_ids = []
            for line in rec.order_line:
                invoice_line_ids += [(0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'price_unit': self.refundable_amount,
                    'quantity': 1.0,
                    'tax_ids': line.tax_id.ids,
                    # 'account_id': line.account.id,
                })]
                break
            if invoice_line_ids:
                bill.update({'invoice_line_ids': invoice_line_ids})
        record = self.env['account.move'].create(bill)
        if record:
            self.deffered_revenue_id.state = 'close'
        if self.termination_date:
            date_end = self.termination_date + relativedelta(months=int(self.early_termination_period))
            move_ids = list(filter(lambda x: x.date >= date_end and x.state != 'posted',
                                   self.deffered_revenue_id.depreciation_move_ids))
            for move in move_ids:
                move.state = 'cancel'
