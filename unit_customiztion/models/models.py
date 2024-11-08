from odoo import api, fields, models, api, _
from odoo.exceptions import UserError


class ProductVariantsInherit(models.Model):
    _inherit = 'product.product'

    property_size = fields.Float('Property Size (SQF)')
    makani_no = fields.Char('Makani #')
    premise_no = fields.Char('Premise No#')
    unit_location = fields.Char('Location')
    floor_plans_ids = fields.One2many('floor.plans', 'floor_id')
    floor_images_ids = fields.One2many('floor.images', 'floor_id')
    cover_photo = fields.Binary('Cover Photo')
    # for_sale = fields.Boolean(default=False)
    # for_rent = fields.Boolean(default=False)
    no_of_hall = fields.Integer('Hall')
    amenities_id = fields.Many2one('property.amenities', string='Amenities')
    is_maintenance = fields.Selection([
        ('no', 'Included'),
        ('yes', 'Not Included'),
    ], string='Maintenance')
    is_parking = fields.Selection([
        ('no', 'Included'),
        ('yes', 'Not Included'),
    ], string='Parking')
    security_mode = fields.Selection([
        ('cheque', 'Cheque'),
        ('cash', 'Cash'),
        ('translation', 'Translation'),
    ], string='Security Mode')

    @api.constrains('for_sale', 'for_rent')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.for_sale and rec.for_rent:
                raise UserError("You Can't be able to select both Sale and Rent on same time")

    unit_type_id = fields.Many2one('unit.type', 'Unit Type')
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('rented', 'Rented'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
        ('cancel', 'Cancel'),
    ], default='available')

    rent_price = fields.Float('Rent Price')
    sub_unit_id = fields.Many2one('sub.unit.type', 'Sub Unit')

    # @api.onchange('unit_type_id')
    # def mazhar(self):
    #     lst = []
    #     [lst.append(id) for id in self.unit_type_id.mapped('id')]
    #     self.return_ids(lst)

    @api.onchange('unit_type_id')
    def onchange_sale_rent(self):
        if self.unit_type_id:
            sub_group = self.env['sub.unit.type'].sudo().search([
                ('parent_unit_id', 'in', self.unit_type_id.ids)
            ]).ids

            return {
                'domain': {
                    'sub_unit_id': [('id', 'in', sub_group)],
                }
            }

    def got_to_opportunity(self):
        if self.state != 'available':
            state = dict(self.fields_get(allfields=['state'])['state']['selection'])[
                self.state]
            raise UserError(f'The Unit is "{state}"')
        record_ids = [self.id]
        crm = self.env['crm.lead'].unit_id = [(6, 0, record_ids)]
        return {
            'name': 'Pip Line',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.env['crm.lead'].id,
        }

    def create_deferred(self):

        if self.env['deffered.revenue'].search([('unit_id', '=', self.id)]):
            return {
                'name': _('Deferred Revenues'),
                'view_mode': 'tree,form',
                'res_model': 'deffered.revenue',
                'domain': [('order_id', '=', self.sale_order.id), ('unit_id', '=', self.id)],
                'context': {
                    'default_name': self.name,
                    'default_unit_id': self.id,
                    'default_floor_id': self.floor_id.id,
                    'default_building_id': self.building.id,
                    'default_project_id': self.project.id,
                    'default_account_analytic_id': self.units_analytic_account.id,
                    'default_method_number': 12,
                    'default_for_unit': True,
                    'create': False,
                    'asset_type': 'sale',
                    'default_asset_type': 'sale',
                },
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref("account_deffered_revenue.view_account_deffered_revenue_tree").id, 'tree'),
                          (self.env.ref("account_deffered_revenue.view_account_deffered_revenue_form").id, 'form'), ]
            }
        else:
            return {
                'name': 'Deferred Revenues',
                'type': 'ir.actions.act_window',
                'res_model': 'deffered.revenue',
                'view_mode': 'form',
                'view_type': 'form',
                'domain': [('order_id', '=', self.sale_order.id), ('unit_id', '=', self.id)],
                'context': {
                    'default_name': self.name,
                    'default_unit_id': self.id,
                    'default_floor_id': self.floor_id.id,
                    'default_building_id': self.building.id,
                    'default_project_id': self.project.id,
                    'default_account_analytic_id': self.units_analytic_account.id,
                    'default_for_unit': True,
                    'default_method_number': 12,
                    'asset_type': 'sale',
                    'default_asset_type': 'sale',
                    # 'create': False
                },
                'view_id': self.env.ref("account_deffered_revenue.view_account_deffered_revenue_form").id,
            }


class FloorPlansModel(models.Model):
    _name = 'floor.plans'

    name = fields.Char('Document Name')
    photos = fields.Binary('Photos')
    floor_id = fields.Many2one('property.floor')


class FloorImageModel(models.Model):
    _name = 'floor.images'

    name = fields.Char('Description')
    photo = fields.Binary('Photo')
    floor_id = fields.Many2one('property.floor')


class UnitType(models.Model):
    _name = 'unit.type'

    name = fields.Char('Name')


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    for_sale = fields.Boolean(default=False)
    for_rent = fields.Boolean(default=False)


class SubUnitType(models.Model):
    _name = 'sub.unit.type'

    name = fields.Char('Name')
    parent_unit_id = fields.Many2one('unit.type', 'Parent Unit')


class AccountTax(models.Model):
    _inherit = 'account.tax'

    unit_type = fields.Many2one('unit.type', string='Unit Type')


class PropertyAmenities(models.Model):
    _name = 'property.amenities'
    name = fields.Char('Name')
