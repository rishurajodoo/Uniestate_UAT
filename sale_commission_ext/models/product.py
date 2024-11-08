from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_maintenance_request_allowed = fields.Boolean(string="Block Maintenance")

