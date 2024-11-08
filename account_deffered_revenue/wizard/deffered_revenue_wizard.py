import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DefferedRevenueWizard(models.TransientModel):
    _name = 'deffered.revenue.wizard'
    _description = 'Deffered Revenue Wizard'

    is_combined = fields.Boolean(string='Create Combined Deffered Revenue', default=False)
    sale_order_id = fields.Many2one('sale.order', string='Order ID')

    def create_deffered_revenue(self):
        sale_order = self.sale_order_id
        if not self.is_combined:
            no_of_recognitions = 0
            if sale_order.start_date and sale_order.end_date:
                no_of_recognitions = round((sale_order.end_date - sale_order.start_date).days / 30)
            first_depreciation_date = False
            if sale_order.start_date:
                nxt_mnth = sale_order.start_date.replace(day=28) + datetime.timedelta(days=4)
                first_depreciation_date = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)
            sum_of_price_unit = 0.0
            if sale_order.order_line:
                lines = sale_order.order_line.filtered(lambda x: x.product_id.is_unit)
                sum_of_price_unit += sum(map(lambda x: x.price_unit, lines))
            for units in sale_order.unit:
                deffered_revenues = self.env['deffered.revenue'].create({
                    'unit_id': units.ids,
                    'name': units.name,
                    'floor_id': sale_order.floor.id,
                    'building_id': sale_order.building.id,
                    'project_id': sale_order.project.id,
                    'order_id': sale_order.id,
                    'original_value': sum_of_price_unit,
                    'acquisition_date': sale_order.start_date,
                    'first_depreciation_date': first_depreciation_date,
                    'method_number': no_of_recognitions,
                    # 'account_depreciation_id': no_of_recognitions,
                    # 'account_depreciation_expense_id': no_of_recognitions,
                    # 'journal_id': no_of_recognitions,
                    'analytic_distribution': {units.units_analytic_account.id: 100},
                })
                pass
        else:
            no_of_recognitions = 0
            if sale_order.start_date and sale_order.end_date:
                no_of_recognitions = round((sale_order.end_date - sale_order.start_date).days / 30)
            first_depreciation_date = False
            if sale_order.start_date:
                nxt_mnth = sale_order.start_date.replace(day=28) + datetime.timedelta(days=4)
                first_depreciation_date = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)
            sum_of_price_unit = 0.0
            if sale_order.order_line:
                lines = sale_order.order_line.filtered(lambda x: x.product_id.is_unit)
                sum_of_price_unit += sum(map(lambda x: x.price_unit, lines))
            all_unit_names = []
            analytical_dis = {}
            for units in sale_order.unit:
                all_unit_names.append(units.name)
                analytical_dis.update({units.units_analytic_account.id: 100})
            names = ' '.join(map(lambda x: ', ' + str(x), all_unit_names))[2:]
            return {
                'name': _('Deffered Revenue'),
                'res_model': 'deffered.revenue',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'current',
                'domain': [('order_id', '=', sale_order.id)],
                'context': {
                    'default_unit_id': [(6, 0, sale_order.unit.ids)],
                    'default_name': names,
                    'default_floor_id': sale_order.floor.id,
                    'default_building_id': sale_order.building.id,
                    'default_project_id': sale_order.project.id,
                    'default_order_id': sale_order.id,
                    'default_original_value': sum_of_price_unit,
                    'default_acquisition_date': sale_order.start_date,
                    'default_first_depreciation_date': first_depreciation_date,
                    'default_method_number': no_of_recognitions,
                    'default_analytic_distribution': analytical_dis,
                }
            }
            pass
