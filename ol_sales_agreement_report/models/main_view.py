from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'


class ResCompanyInherited(models.Model):
    _inherit = 'res.company'

    image = fields.Image(string='Image')


class ResPartnerInherited(models.Model):
    _inherit = 'res.partner'

    name_arabic = fields.Char(string='Name Arabic')
    is_unit = fields.Boolean('Is Unit')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one(comodel_name='res.partner', domain='[("is_unit", "=", False)]')


class PurchaserCompanyInherit(models.Model):
    _inherit = 'purchaser.company'

    purchase_individual = fields.Many2one(comodel_name='res.partner', string='Individual',
                                          domain='[("is_unit", "=", False)]')
