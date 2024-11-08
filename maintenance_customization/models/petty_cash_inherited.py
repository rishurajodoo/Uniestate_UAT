from odoo import fields, models, api, _


class PettyCash(models.Model):
    _inherit = 'snd.petty.cash'

    request_id = fields.Many2one('maintenance.request', string='Maintenance ID')

    unit_id = fields.Many2one('product.product', 'Unit')
    floor_id = fields.Many2one('property.floor', 'Floor')
    building_id = fields.Many2one('property.building', 'Building')
    project_id = fields.Many2one('project.project', 'Project')

    @api.model
    def create(self, vals_list):
        res = super(PettyCash, self).create(vals_list)
        if res.request_id:
            petty_ids = self.env['snd.petty.cash'].search([('request_id', '=', res.request_id.id)])
            if petty_ids:
                res.request_id.petty_cash_ids = petty_ids.ids
        return res
