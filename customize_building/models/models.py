from odoo import api, fields, models, _


class CreateBulidingInherit(models.Model):
    _inherit = 'create.building.wizard'

    building_detail_id = fields.One2many('building.detail', 'building_wizard_id')

    @api.onchange('building_detail_id')
    def _onchange_detail(self):
        i = 0
        for line in self.building_detail_id:
            i += 1
            self.no_of_building = i


class BuildingDetail(models.Model):
    _name = 'building.detail'

    name = fields.Char('Building Name')
    building_wizard_id = fields.Many2one('create.building.wizard')
    building_type_id = fields.Many2one('building.type', 'Type')
    plot_no = fields.Text('Building No')


class BuildingInherit(models.Model):
    _inherit = 'property.building'

    building_type_id = fields.Many2one('building.type', 'Type')

    def create_asset(self):
        asset = self.env['account.asset'].building_id = self.id
        return {
            'name': 'Asset',
            'type': 'ir.actions.act_window',
            'res_model': 'account.asset',
            'view_mode': 'form',
            'view_type': 'form',
            # 'domain': [('asset_type', '=', 'purchase'), ('state', '=', 'model')],
            'domain': [('asset_type', '=', 'purchase')],
            'context': {'default_building_id': self.id,
                        'default_project_id': self.project_id.id,
                        'default_name': self.name,
                        'default_account_analytic_id': self.building_account_analytical.id,
                        'default_method_number': 0,
                        'create': False,
                        'asset_type': 'purchase',
                        'default_asset_type': 'purchase',
                        },
            'view_id': self.env.ref("account_asset.view_account_asset_form").id,
        }

    def action_show_assets(self):
        if self.env['account.asset'].search([('building_id', '=', self.id), ('for_building', '=', 'True')]):
            return {
                'name': _('Assets'),
                'view_mode': 'tree,form',
                'res_model': 'account.asset',
                'domain': [('building_id', '=', self.id),('for_building', '=', 'True')],
                'context': {'default_building_id': self.id,
                            'default_project_id': self.project_id.id,
                            'default_for_building': True,
                            'default_name': self.name,
                            'default_account_analytic_id': self.building_account_analytical.id,
                            'default_method_number': 0,
                            'create': False,
                            'asset_type': 'purchase',
                            'default_asset_type': 'purchase',
                            },
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref("account_asset.view_account_asset_purchase_tree").id, 'tree'),
                          (self.env.ref("account_asset.view_account_asset_form").id, 'form'), ]
            }
        else:
            return {
                'name': 'Asset',
                'type': 'ir.actions.act_window',
                'res_model': 'account.asset',
                'view_mode': 'form',
                'view_type': 'form',
                # 'domain': [('asset_type', '=', 'purchase'), ('state', '=', 'model')],
                'domain': [('asset_type', '=', 'purchase')],
                'context': {'default_building_id': self.id,
                            'default_project_id': self.project_id.id,
                            'default_for_building': True,
                            'default_name': self.name,
                            'default_account_analytic_id': self.building_account_analytical.id,
                            'default_method_number': 0,
                            'create': False,
                            'asset_type': 'purchase',
                            'default_asset_type': 'purchase',
                            },
                'view_id': self.env.ref("account_asset.view_account_asset_form").id,
            }
