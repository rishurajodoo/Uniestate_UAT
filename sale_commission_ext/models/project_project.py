
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    sale_internal_agent_commission = fields.Many2one('commission', string='Internal Agent Commission')
    sale_external_agent_commission = fields.Many2one('commission', string='External Agent Commission')
    sale_freelance_agent_commission = fields.Many2one('commission', string='Freelance Agent Commission')

    rent_internal_agent_commission = fields.Many2one('commission', string='Internal Agent Commission')
    rent_external_agent_commission = fields.Many2one('commission', string='External Agent Commission')
    rent_freelance_agent_commission = fields.Many2one('commission', string='Freelance Agent Commission')

