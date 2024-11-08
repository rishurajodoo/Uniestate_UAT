from odoo import models, api, fields


class CrmLeads(models.Model):
    _inherit = 'crm.lead'

    building = fields.Many2one(comodel_name='property.building', string='Building')
    project = fields.Many2one(comodel_name='project.project', string='Project')
    floor = fields.Many2one(comodel_name='property.floor', string='Floor')
    unit = fields.Many2one(comodel_name='product.product', string='Unit')

