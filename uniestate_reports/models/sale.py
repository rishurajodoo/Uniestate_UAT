from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    advance_booking_amount = fields.Float(string='Advance Booking Amount')


class TokenWizardInherit(models.TransientModel):
    _inherit = 'account.voucher.wizard.sale'

    def make_advance_payment(self):
        res = super(TokenWizardInherit, self).make_advance_payment()
        sale_obj = self.env["sale.order"]

        sale_ids = self.env.context.get("active_ids", [])
        records = sale_obj.browse(sale_ids)
        if records:
            records.write({
                'advance_booking_amount': self.amount_advance
            })
        return res



class ProductProductInherited(models.Model):
    _inherit = 'product.product'

    parking_price = fields.Float(string="Parking Price")

    # @api.onchange('parking_price')
    # def _on_parking_price_change(self):
    #     # super(ProductProductInherited, self)._on_parking_price_change()
    #     for rec in self:
    #         if self.parking_price:
    #             rec.lst_price = self.property_price + self.parking_price
