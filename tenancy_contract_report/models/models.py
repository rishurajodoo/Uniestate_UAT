from odoo import api, fields, models, api, _
from odoo.exceptions import UserError

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    tenant_id = fields.Many2one('res.partner', string='Tenant')

class ProductInherit(models.Model):
    _inherit = 'product.product'

    parking_space = fields.Integer(string='Parking Space')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    grace_period = fields.Char(string='Grace Period') 
