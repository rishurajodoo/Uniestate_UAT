from odoo import api, fields, models, api, _
from odoo.exceptions import UserError
from datetime import date


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    custom_admin_fees_product_id = fields.Many2one('product.product', string='Admin Fees Product',
                                 config_parameter='unietstate_sale_transfer_process.custom_admin_fees_product_id')
