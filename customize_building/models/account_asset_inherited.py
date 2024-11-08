from odoo import fields, models, api, _


class AccountAssetInherited(models.Model):
    _inherit = 'account.asset'

    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building', domain="[('project_id', '=', project_id)]")
    floor_id = fields.Many2one("property.floor", string="Floor", domain='[("building_id", "=", building_id)]')
    unit_id = fields.Many2one("product.product", string="Unit",
                              domain="[('state', '=', 'available'), ('floor_id', '=', floor_id)]")
    order_id = fields.Many2one('sale.order', 'Order')
    for_building = fields.Boolean(default=False)
    for_unit = fields.Boolean(default=False)
    # analytic_tag_ids = fields.Many2many('account.analytic.plan', string="Analytic Tag")

    # @api.model
    # def create(self, vals):
    #     res = super(AccountAssetInherited, self).create(vals)
    #     if res.building_id:
    #             res.analytic_tag_ids = res.building_id.analytic_tag_id
    #             res.acquisition_date = res.order_id.start_date
    #     else:
    #         res.acquisition_date = res.order_id.start_date
    #         tags = []
    #         if res.unit_id:
    #             tags = [res.unit_id.analytic_tag_id.id]
    #         if res.building_id:
    #             tags.append(res.building_id.analytic_tag_id.id)
    #         if res.floor_id:
    #             tags.append(res.floor_id.analytic_tag_id.id)
    #         res.analytic_tag_ids = tags
    #     return res
