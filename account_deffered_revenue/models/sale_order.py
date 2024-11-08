# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models
import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def create_deffered_revenue(self):
        deffered_revenues = self.env['deffered.revenue'].search([('order_id', '=', self.id)])
        if deffered_revenues:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Deffered Revenues',
                'view_mode': 'tree,form',
                'res_model': 'deffered.revenue',
                'domain': [('id', 'in', deffered_revenues.ids)],
                'context': {'create': False}
            }
        if len(self.unit.ids) > 1:
            invoice_ids = self.env['account.move'].search(
                [('so_ids', '=', self.id), ('reference.is_invoice', '=', True)])
            # default_invoice_ids
            # if invoice_ids:
            #     default_invoice_ids
            return {
                'name': _("Deffered Revenue"),
                'type': 'ir.actions.act_window',
                'res_model': 'deffered.revenue.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_sale_order_id': self.id,
                            'default_invoice_ids': [(6, 0, [x.id for x in invoice_ids])]}
            }
        no_of_recognitions = 0
        if self.start_date and self.end_date:
            no_of_recognitions = round((self.end_date - self.start_date).days / 30)
        first_depreciation_date = False
        if self.start_date:
            nxt_mnth = self.start_date.replace(day=28) + datetime.timedelta(days=4)
            first_depreciation_date = nxt_mnth - datetime.timedelta(days=nxt_mnth.day)
        sum_of_price_unit = 0.0
        if self.order_line:
            lines = self.order_line.filtered(lambda x: x.product_id.is_unit)
            sum_of_price_unit += sum(map(lambda x: x.price_unit, lines))
        return {
            'name': _('Deffered Revenue'),
            'res_model': 'deffered.revenue',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'current',
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_unit_id': [(6, 0, self.unit.ids)],
                'default_name': self.unit.name,
                'default_floor_id': self.floor.id,
                'default_building_id': self.building.id,
                'default_project_id': self.project.id,
                'default_order_id': self.id,
                'default_original_value': sum_of_price_unit,
                'default_acquisition_date': self.start_date,
                'default_first_depreciation_date': first_depreciation_date,
                'default_method_number': no_of_recognitions,
                'default_analytic_distribution': {self.unit.units_analytic_account.id: 100},
            }
        }
