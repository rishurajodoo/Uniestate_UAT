from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError


class ProductProductInherited(models.Model):
    _inherit = 'product.product'

    def go_to_maintenance(self):
        if self.is_maintenance_request_allowed:
            raise ValidationError("Maintenance Request is not allowed")
        # if self.state != 'rented':
        #     raise UserError('Unit must be "Rented"')
        print('Maintenance of product')
        return {
            'name': 'Maintenance Request',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'res_id': self.env['maintenance.request'].id,
            'context': {
                'default_name': self.name,
                'default_unit_id': self.id,
                'default_floor_id': self.floor_id.id,
                'default_building_id': self.building.id,
                'default_project_id': self.project.id,
                'default_tenancy_id': self.tenancy_id.id,
                'default_tenancy_state': self.tenancy_state,
                'default_start_date': self.start_date,
                'default_end_date': self.end_date,
            }
        }
