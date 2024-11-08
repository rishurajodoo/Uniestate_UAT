

from odoo import api, fields, models


class CommissionSettlement(models.Model):
    _inherit = "commission.settlement"

    sale_commission_ids = fields.One2many(
        comodel_name="sale.commission.settlement.line",
        inverse_name="commission_id",
        readonly=True,
    )


class SaleCommissionSettlementLine(models.Model):
    _name = 'sale.commission.settlement.line'

    order_id = fields.Many2one('sale.order', string='Order')
    date = fields.Date(string='Date')
    commission_id = fields.Many2one('commission.settlement', string='Settlement')
    so_amount = fields.Monetary(string='SO Amount', related='order_id.amount_total', store=True)
    invoiced_amount = fields.Float(string='Invoiced Amount', compute='_compute_invoiced_amount', store=True)
    paid_amount = fields.Float(string='Paid Amount',  compute='_compute_paid_amount', store=True)
    outstanding_amount = fields.Float(string='Outstanding Amount', compute='_compute_invoiced_amount', store=True)
    outstanding_percentage = fields.Float(string='Outstanding %', compute='_compute_outstanding_percentage', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, store=True)

    @api.depends('order_id.invoice_ids')
    def _compute_invoiced_amount(self):
        self.invoiced_amount = 0.0
        self.outstanding_amount = 0.0
        for rec in self:
            invoices = self.mapped('order_id.invoice_ids')
            total_amount = sum(invoice.amount_untaxed_signed for invoice in invoices)
            rec.invoiced_amount = total_amount
            outstanding_total_amount = sum(invoice.amount_total_signed for invoice in invoices)
            rec.outstanding_amount = outstanding_total_amount

    @api.depends('invoiced_amount', 'outstanding_amount')
    def _compute_paid_amount(self):
        self.paid_amount = 0.0
        for rec in self:
            invoices = self.mapped('order_id.invoice_ids')
            total_paid_amount = sum(invoice.amount_residual_signed for invoice in invoices)
            rec.paid_amount = total_paid_amount

    @api.depends('invoiced_amount', 'outstanding_amount')
    def _compute_outstanding_percentage(self):
        self.outstanding_percentage = 0.0
        for rec in self:
            if rec.invoiced_amount != 0:
                rec.outstanding_percentage = (rec.outstanding_amount / rec.invoiced_amount) * 100






