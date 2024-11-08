from odoo import api, fields, models


class ProjectInherit(models.Model):
    _inherit = 'project.project'

    for_rent = fields.Boolean(default=False)
    for_sale = fields.Boolean(default=True)

    @api.onchange('for_rent', 'for_sale')
    def _onchange_check(self):
        if self.for_sale:
            self.for_rent = False
        elif self.for_rent:
            self.for_sale = False