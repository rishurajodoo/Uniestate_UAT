import datetime
from re import U

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import requests
import datetime


class CreateBuildingWizard(models.Model):
    _name = "create.building.wizard"

    no_of_building = fields.Integer("No of Buildings")

    def create_building(self):
        active_id = self._context.get('active_id')
        no = self._context['no_of_build']
        obj = self.env['property.building'].search([('project_id', '=', active_id)])
        obj_project = self.env['project.project'].search([('id', '=', active_id)])
        print("obj_project", obj_project)
        print("obj", obj)
        j = 0
        for i in self.building_detail_id:
            print("iiiiiii", i)
            j += 1
            if obj:
                analytic_tag = self.env['account.analytic.plan'].create({
                    'name': obj_project.code + "-" + f'{len(obj.ids) + j:02}',
                })
                analytic_account = self.env['account.analytic.account'].create({
                    'name': obj_project.code + "-" + f'{len(obj.ids) + j:02}',
                    'plan_id': analytic_tag.id
                })
                building = self.env['property.building'].create({
                    'project_id': active_id,
                    'name': i.name,
                    'building_type_id': i.building_type_id.id,
                    'plot_no': i.plot_no,
                    'code': obj_project.code + "-" + f'{len(obj.ids) + j:02}',
                    'building_account_analytical': analytic_account.id,
                    'analytic_tag_id': analytic_tag.id,
                })
                analytic_account.building_id = building.id
                analytic_tag.building_id = building.id
                building.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id
            else:
                analytic_tag = self.env['account.analytic.plan'].create({
                    'name': obj_project.code + "-" + f'{j:02}',
                })
                analytic_account = self.env['account.analytic.account'].create({
                    'name': obj_project.code + "-" + f'{j:02}',
                    'plan_id': analytic_tag.id
                })
                building = self.env['property.building'].create({
                    'project_id': active_id,
                    'code': obj_project.code + "-" + f'{j:02}',
                    'plot_no': i.plot_no,
                    'name': i.name,
                    'building_type_id': i.building_type_id.id,
                    'building_account_analytical': analytic_account.id,
                    'analytic_tag_id': analytic_tag.id,
                })
                analytic_account.building_id = building.id
                analytic_tag.building_id = building.id
                building.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id


# create floor
class CreatFloor(models.Model):
    _name = "create.floor.wizard"

    no_of_floor = fields.Integer("No of Floors")

    def create_floor(self):
        active_id = self._context.get('active_id')
        no = self._context['floor']
        model = self.env.context.get('active_model')
        obj = self.env['property.floor'].search([('building_id.id', '=', active_id)])
        obj_project = self.env['property.building'].search([('id', '=', active_id)])
        j = 0
        for i in self.floor_detail_ids:
            j += 1
            if obj:
                analytic_tag = self.env['account.analytic.plan'].create({
                    'name': obj_project.code + "-" + f'{len(obj.ids) + j:01}'
                })
                # analytic_account = self.env['account.analytic.account'].create({
                #     'name': obj_project.code + "-" + f'{len(obj.ids) + j:01}',
                #     'plan_id': analytic_tag.id
                # })
                floor = self.env['property.floor'].create({
                    'building_id': active_id,
                    'code': obj_project.code + "-" + f'{len(obj.ids) + j:01}',
                    # 'floor_analytic_account': analytic_account.id,
                    'analytic_tag_id': analytic_tag.id,
                    'name': i.name.id,
                    'floor_type_id': i.floor_type_id.id,
                })
                # analytic_account.floor_id = floor.id
                analytic_tag.floor_id = floor.id
                floor.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id
            else:
                method2 = obj_project.code + "-" + f'{j:01}'
                analytic_tag = self.env['account.analytic.plan'].create({
                    'name': obj_project.code + "-" + f'{j:01}'
                })
                # analytic_account = self.env['account.analytic.account'].create({
                #     'name': obj_project.code + "-" + f'{j:01}',
                #     'plan_id': analytic_tag.id
                # })
                floor = self.env['property.floor'].create({
                    'building_id': active_id,
                    'code': obj_project.code + "-" + f'{j:01}',
                    # 'floor_analytic_account': analytic_account.id,
                    'analytic_tag_id': analytic_tag.id,
                    'name': i.name.id,
                    'floor_type_id': i.floor_type_id.id,
                })
                # analytic_account.floor_id = floor.id
                analytic_tag.floor_id = floor.id
                floor.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id


# create units
class CreateUnits(models.Model):
    _name = "create.units.wizard"

    no_of_unit = fields.Integer("No of Units")
    for_sale = fields.Boolean(default=False)

    def create_units(self):
        active_id = self._context.get('active_id')
        no = self._context['units']
        obj = self.env['product.product'].search([('floor_id.id', '=', active_id)])
        obj_project = self.env['property.floor'].search([('id', '=', active_id)])
        no = no + 1
        for i in range(1, no):
            if obj:
                # analytic_tag = self.env['account.analytic.plan'].create({
                #     'name': obj_project.code + f'{len(obj.ids) + i:02}',
                # })
                analytic_account = self.env['account.analytic.account'].create({
                    'name': obj_project.code + f'{len(obj.ids) + i:02}',
                    'plan_id': obj_project.analytic_tag_id.id
                })
                tax_ids = self.env['account.tax'].search([('unit_type', '=', self.unit_type_id.id)])
                print(f'tax: {tax_ids}')
                print(f'tax: {tax_ids.ids}')
                if tax_ids:
                    print(f'last tax: {tax_ids[-1]}')
                else:
                    print('No taxes found.')
                unit = self.env['product.product'].create({
                    'name': obj_project.code + f'{len(obj.ids) + i:02}',
                    'floor_id': active_id,
                    'building': obj_project.building_id.id,
                    'project': obj_project.project_name.id,
                    'units_analytic_account': analytic_account.id,
                    # 'analytic_tag_id': analytic_tag.id,
                    'for_sale': self.for_sale,
                    'for_rent': self.for_rent,
                    'unit_type_id': self.unit_type_id.id,
                    'sub_unit_id': self.sub_unit_id.id,
                    'rent_price': 0.0,
                    'lst_price': 0.0,
                    'property_price': 0.0,
                    'sale_ok': True if self.for_sale or self.for_rent else False,
                    'detailed_type': 'service',
                    'taxes_id': tax_ids,
                    'code': obj_project.code + f'{len(obj.ids) + i:02}',
                    'floor_name': obj_project.name.id
                })

                partner = self.env['res.partner'].create({
                    'name': unit.name,
                    'is_unit': True,
                    'for_sale': self.for_sale,
                    'for_rent': self.for_rent,
                })
                analytic_account.unit_id = unit.id
                # obj_project.analytic_tag_id.unit_id = unit.id
                unit.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id
            else:
                # analytic_tag = self.env['account.analytic.plan'].create({
                #     'name': obj_project.code + f'{i:02}',
                # })
                analytic_account = self.env['account.analytic.account'].create({
                    'name': obj_project.code + f'{i:02}',
                    'plan_id': obj_project.analytic_tag_id.id
                })
                tax_ids = self.env['account.tax'].search([('unit_type', '=', self.unit_type_id.id)])
                if tax_ids:
                    print(f'last tax: {tax_ids[-1]}')
                else:
                    print('No taxes found.')
                unit = self.env['product.product'].create({
                    'name': obj_project.code + f'{i:02}',
                    'floor_id': active_id,
                    'units_analytic_account': analytic_account.id,
                    # 'analytic_tag_id': analytic_tag.id,
                    'building': obj_project.building_id.id,
                    'project': obj_project.project_name.id,
                    'for_sale': self.for_sale,
                    'for_rent': self.for_rent,
                    'unit_type_id': self.unit_type_id.id,
                    'sub_unit_id': self.sub_unit_id.id,
                    'rent_price': 0.0,
                    'lst_price': 0.0,
                    'property_price': 0.0,
                    'sale_ok': True if self.for_sale or self.for_rent else False,
                    'detailed_type': 'service',
                    'taxes_id': tax_ids,
                    'code': obj_project.code + f'{i:02}',
                    'floor_name': obj_project.name.id
                })
                partner = self.env['res.partner'].create({
                    'name': unit.name,
                    'is_unit': True,
                    'for_sale': self.for_sale,
                    'for_rent': self.for_rent,
                })
                analytic_account.unit_id = unit.id
                # analytic_tag.unit_id = unit.id
                unit.analytic_tag_id.parent_id = obj_project.analytic_tag_id.id
