from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        existing_sale_orders = self.search(
            [('id', '!=', self.id), ('for_sale', '=', True), ('unit', '=', self.unit.id),
             ('state', 'in', ['sale', 'booked'])])
        if existing_sale_orders:
            raise ValidationError("Another Sale Order exists with the same unit , in sale or booked state !!!!!!")
        for line in self.order_line:
            line.product_id.sale_order = self.id
            line.product_id.so_amount = line.price_unit
        return res

    @api.model
    def _get_next_sequence(self):
        # Choose sequence based on for_sale or for_rent flags
        if self.for_sale:
            sequence_code = 'sale.order.for_sale'
        elif self.for_rent:
            sequence_code = 'sale.order.for_rent'
        else:
            sequence_code = 'sale.order'  # Fallback to default sequence if neither is set

        # Generate the sequence number based on the code
        sequence = self.env['ir.sequence'].next_by_code(sequence_code)
        return sequence

    @api.model
    def create(self, vals):
        # Assign the sequence on creation
        order = super(SaleOrder, self).create(vals)
        order.name = order._get_next_sequence()
        return order
