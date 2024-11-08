from odoo import fields, models


class Purchase(models.Model):
    _inherit = 'purchase.order'

    site_contact = fields.Many2one('res.partner', string='Site Contact')
