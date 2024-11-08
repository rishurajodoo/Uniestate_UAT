# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError
from datetime import datetime, date
from datetime import timedelta


class SaleOrderModelInherit(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        'res.partner', string='Customer')
    confirmation_of_order = fields.Char(string="Confirmation of order")
    token_received = fields.Char(string="Token Received / Commission Received")
    # leased_unit = fields.Integer(string="Leased Unit")
    # unit_number = fields.Integer(string="Unit Number")
    # location = fields.Char(string="Location")
    # land_no = fields.Integer(string="Land No")
    # dm_no = fields.Integer(string="DM No")
    # premise_no = fields.Integer(string="DEWA No (Premise No.)")
    # sub_type = fields.Char(string="Sub Type")
    # floor_no = fields.Integer(string="Floor No")
    # unit_size_sqft = fields.Integer(string="Unit Size (SQFT)")
    # property_type = fields.Integer(string="Property Type")
    # makani_number = fields.Integer(string="Makani Number")
    tenancy = fields.Many2one('tenancy.contract', sttring='Tenancy Contract ID')
    tenancy_state = fields.Selection([
        ('new', 'New'),
        ('renew', 'Renew'),
        ('open', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Tenancy State', default='new')
    start_date = fields.Date(string="Start Date", compute='_compute_tenancy_contract_period')
    end_date = fields.Date(string="End Date", compute='_compute_tenancy_contract_period')
    analytic_tag_ids = fields.Many2many('account.analytic.plan', string="Analytic Tag")
    is_crm = fields.Boolean(default=False)

    def _compute_tenancy_contract_period(self):
        for rec in self:
            print('Tenancy Contract Period')
            if rec.rent_plan_ids:
                print('onchange TC Period automation')
                for pp in rec.rent_plan_ids:
                    if pp.start_date:
                        print(f'Start Date: {pp.start_date}')
                        rec.start_date = pp.start_date
                        break
                    else:
                        rec.start_date = False
                for pp in reversed(rec.rent_plan_ids):
                    if pp.end_date:
                        print(f'End Date: {pp.end_date}')
                        rec.end_date = pp.end_date
                        break
                    else:
                        rec.end_date = False
            else:
                rec.start_date = False
                rec.end_date = False

    @api.onchange('for_rent', 'for_sale')
    def onchange_sale_rent(self):
        lst = []
        if self.for_sale:
            ids = self.partner_id.sudo().search([
                ('for_sale', '=', True)
            ]).ids

            return {
                'domain': {
                    'partner_id': [('id', 'in', ids)],
                }
            }
        elif self.for_rent:
            ids = self.partner_id.sudo().search([
                ('for_rent', '=', True)
            ]).ids
            return {
                'domain': {
                    'partner_id': [('id', 'in', ids)],
                }
            }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'crm.lead':
            crm = self.env['crm.lead'].browse(self._context.get('active_id'))
            if self.invoice_count == 0:
                if crm.for_rent:
                    res['partner_id'] = crm.partner_id.id
                    res['project'] = crm.project_id.id
                    res['building'] = crm.building_id.id
                    res['floor'] = crm.floor_id.id
                    res['unit'] = [(6, 0, crm.unit_id.ids)]
                    res['for_rent'] = crm.for_rent
                    res['for_sale'] = crm.for_sale
                    res['is_crm'] = True
                elif crm.for_sale:
                    res['project'] = crm.project_id.id
                    res['building'] = crm.building_id.id
                    res['floor'] = crm.floor_id.id
                    res['unit'] = [(6, 0, crm.unit_id.ids)]
                    res['for_rent'] = crm.for_rent
                    res['for_sale'] = crm.for_sale
                    res['is_crm'] = True
                    res['purchaser_ids'] = [(0, 0, {
                        'purchase_individual': crm.partner_id.id,
                        'purchase_company': crm.company_id.id or crm.env.company.id,
                    })],
                    # res['order_line'] = [(0, 0, {
                    #     'product_id': unit.id,
                    #     'name': f'Building: {crm.building_id.name if crm.floor_id else ""} Floor: {crm.floor_id.name if crm.floor_id else ""} Unit: {(unit.name).split("-")[-1] if unit else ""}',
                    #     'product_uom_qty': 1,
                    #     'price_unit': unit.property_price,
                    #     'product_uom': unit.uom_id.id,
                    #     'tax_id': False,
                    #     'analytic_tag_ids': unit.analytic_tag_id,
                    # })]`
        return res

    # @api.onchange('rent_plan_ids', 'rent_plan_ids.start_date', 'rent_plan_ids.end_date')
    # def on_change_date_order(self):
    #     for rec in self:
    #         print('onchange TC Period automation')
    #         for pp in rec.rent_plan_ids:
    #             if pp.start_date:
    #                 print(f'Start Date: {pp.start_date}')
    #                 rec.start_date = pp.start_date
    #                 break
    #         for pp in reversed(rec.rent_plan_ids):
    #             if pp.end_date:
    #                 print(f'End Date: {pp.end_date}')
    #                 rec.end_date = pp.end_date
    #                 break
    #         # if rec.date_order:
    #         #     rec.start_date = rec.date_order.date()
    #         #     rec.end_date = (rec.date_order.date()).replace(rec.date_order.year + 1) - timedelta(days=1)


# class InstallmentLineInherit(models.Model):
#     _inherit = 'installment.line'
#
#     def create_inv(self):
#         for pl in self:
#             for plan in pl.order_id.plan_ids:
#                 for installment in pl.order_id.installment_ids:
#                     if plan.milestone_id == installment.milestone_id:
#                         invoice = None
#                         if pl.order_id.order_line:
#                             inv_lines = [
#                                 (0, 0, {
#                                     'product_id': line.product_id.id,
#                                     'name': line.name,
#                                     'quantity': line.product_uom_qty,
#                                     'product_uom_id': line.product_uom.id,
#                                     'price_unit': installment.amount,
#                                     'tax_ids': line.tax_id,
#                                     'sale_line_ids': line,
#                                 },)
#                                 for line in pl.order_id.order_line
#                             ]
#                             inv_vals = {
#                                 'partner_id': pl.order_id.partner_id.id,
#                                 'invoice_date': installment.date,
#                                 'invoice_line_ids': inv_lines,
#                                 'move_type': 'out_invoice',
#                                 'so_ids': pl.order_id.id,
#                                 'state': 'draft',
#                                 'project': pl.order_id.project.id,
#                                 'building': pl.order_id.building.id,
#                                 'floor': pl.order_id.floor.id,
#                                 'invoice_origin': pl.order_id.name,
#                                 'unit': pl.order_id.unit.id,
#                             }
#                             invoice = self.env['account.move'].create(inv_vals)
#                             installment.move_id = invoice.id
#
#     def create_pdc(self):
#         for line in self:
#             self.env['pdc.payment'].create({
#                 'partner_id': line.order_id.partner_id.id,
#                 'payment_amount': line.amount,
#                 'date_payment': line.invoice_payment_date,
#                 'date_registered': line.invoice_payment_date,
#             })

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.unit:
            tenancy = self.unit.filtered(lambda x: x.tenancy_id.state in ('renew', 'open'))
            if tenancy:
                raise ValidationError("Order not confirmed Tenancy contract state in Renew or In-progress")
        return res

    @api.onchange('partner_id')
    def on_partner_id_change(self):
        if not self.opportunity_id:
            if self.for_sale:
                var = self.env["product.product"].search([('name', '=', self.partner_id.name)])
                self.write({
                    'project': var.project.id,
                    'building': var.building.id,
                    'floor': var.floor_id.id,
                    'unit': var.id,
                    'relevent_unit_no': var.id,
                })
                product_ids = []
                for p in var:
                    product_ids.append((0, 0, {
                        'product_id': p.id,
                        'name': p.name,
                        'product_uom_qty': 1,
                        'price_unit': p.property_price,
                        'product_uom': p.uom_id.id,
                        'order_id': self.id,
                        'product_uom_qty': p.uom_id.id if p.uom_id else False,
                        'tax_id': p.taxes_id.ids,
                        'analytic_tag_ids': p.analytic_tag_id,
                    }))
                    print(product_ids)
                self.write({
                    'order_line': product_ids
                })
