import datetime

from odoo import fields, models, api, _


class CancelSaleWizard(models.TransientModel):
    _name = 'cancel.sale.wizard'

    refund_amount = fields.Float(string='Refund Amount')
    cancel_reason_id = fields.Many2one('sale.cancel.reason', string="Cancel Reason")
    cancel_feedback = fields.Html(string="Cancel Feedback")
    total_amount = fields.Float(string='Refund Amount')

    @api.model
    def default_get(self, fields):
        result = super(CancelSaleWizard, self).default_get(fields)
        context = self.env.context
        sale_order_id = self.env[context.get('active_model')].browse(context.get('active_id'))
        if sale_order_id.ins_amount < 0:
            amount = 0.0
        else:
            amount = sale_order_id.paid_amount - (sale_order_id.ins_amount * 0.40)
        if amount < 0:
            self.refund_amount = 0.0
        else:
            self.refund_amount = amount
        return result

    def action_cancel(self):
        context = self.env.context
        sale_order_id = self.env[context.get('active_model')].browse(context.get('active_id'))
        if sale_order_id.for_sale:
            draft_invoice = sale_order_id.invoice_ids.filtered(lambda l: l.state == 'draft')
            for draft_inv in draft_invoice:
                draft_inv.state = 'cancel'
            sale_order_id.state = 'cancel'

            if sale_order_id.order_line:
                vals = [(0, 0, {
                    'product_id': sale_order_id.order_line[0].product_id.id,
                    'price_unit': self.refund_amount,
                    'analytic_distribution': {sale_order_id.order_line[0].product_id.units_analytic_account.id: 100}
                })]

                inv_vals = {
                    'move_type': 'out_refund',
                    'partner_id': sale_order_id.partner_id.id,
                    'invoice_date': datetime.datetime.now(),
                    'invoice_line_ids': vals,
                    'project': sale_order_id.project.id,
                    'building': sale_order_id.building.id,
                    'floor': sale_order_id.floor.id,
                    'unit': [(6, 0, sale_order_id.unit.ids)],
                    "so_ids": sale_order_id.id,
                }
                sale_order_id.order_line[0].product_id.state = 'available'
                self.env['account.move'].create(inv_vals)

    @api.onchange('cancel_reason_id')
    def _onchange_cancel_reason_id(self):
        if self.cancel_reason_id:
            if self.cancel_reason_id.cancellation_charges:
                self.refund_amount = 0
            else:
                self.refund_amount = self.total_amount
