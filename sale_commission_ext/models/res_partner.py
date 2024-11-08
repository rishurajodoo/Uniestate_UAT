from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sale_commission_ids = fields.One2many(
        comodel_name="sale.commission.line",
        inverse_name="agent_id",
        readonly=True,
    )


class SaleCommissionLine(models.Model):
    _name = 'sale.commission.line'

    order_id = fields.Many2one('sale.order', string='Order')
    date = fields.Date(string='Date')
    status = fields.Selection(
        related='order_id.state',
        string="Status",
        store=True)
    payment_status = fields.Selection(
        related='order_id.advance_payment_status', string='Payment Status', store=True)
    invoice_status = fields.Selection(
        related='order_id.invoice_status', store=True, string='Invoice Status',
    )
    settlement_status = fields.Selection([("settled", "Settled"), ("un_settled", "UnSettled")],
                                         string="Settlement Status",
                                         default="un_settled")
    commission_amount = fields.Float(string='Commission  Amount')
    agent_id = fields.Many2one('res.partner', string='Agent')
