from odoo import fields, models, api, _


class SaleCancelReason(models.Model):
    _name = 'sale.cancel.reason'

    name = fields.Char(string="Name")
    cancellation_charges = fields.Boolean(
        help="Select this if you want to apply cancellation charges",string='Charges Applicable'
    )
