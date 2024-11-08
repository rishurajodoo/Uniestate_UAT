from odoo import api, fields, models, _


class SaleOrderFields(models.Model):
    _inherit = 'sale.order'

    building = fields.Many2one('property.building', string='Building')
    project = fields.Many2one('project.project', string='Project')
    floor = fields.Many2one(comodel_name='property.floor', string='Floor')
    unit = fields.Many2many(comodel_name='product.product', string='Unit')


class AccountMoveInvoice(models.Model):
    _inherit = 'account.move'

    project = fields.Many2one('project.project', string='Project')
    building = fields.Many2one('property.building', string='Building', domain="[('project_id', '=', project)]")
    floor = fields.Many2one("property.floor", string="Floor", domain='[("building_id", "=", building)]')
    # unit = fields.Many2one("product.product", string="Unit",
    #                        domain="[('state', '=', 'available'), ('floor_id', '=', floor)]"
    unit = fields.Many2many("product.product", string="Unit",
                            domain="[('state', '=', 'available'), ('floor_id', '=', floor)]")
    order_id = fields.Many2one('sale.order', 'Order')
    is_afm = fields.Boolean(string="Is Afm", default=False)
    pdc_recall_id = fields.Many2one('pdc.payment')


class TransferDataFields(models.Model):
    _inherit = 'stock.picking'

    building = fields.Many2one(comodel_name='property.building', string='Building')
    project = fields.Many2one(comodel_name='project.project', string='Project')
    floor = fields.Many2one(comodel_name='property.floor', string='Floor')
    unit = fields.Many2one(comodel_name='product.product', string='Unit')


class prodvar_Data(models.Model):
    _inherit = 'product.product'

    project = fields.Many2one(comodel_name='project.project', string='Project')
