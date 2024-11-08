# -*- coding: utf-8 -*-

from odoo import fields,models
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    booking_amount = fields.Char(string="Booking amount", copy=False)
    # TODO: FOR Validation
    def action_confirm(self):
        for rec in self:
            if (rec.for_rent or rec.is_renewed) and not rec.rent_plan_ids:
                raise ValidationError("Tenancy Payment Plan is Left Empty, Kindly fill it out first before confirming the order.")
            elif rec.for_sale and not rec.plan_ids:
                raise ValidationError("Payment Plan is Left Empty, Kindly fill it out first before confirming the order.")
        super().action_confirm()


