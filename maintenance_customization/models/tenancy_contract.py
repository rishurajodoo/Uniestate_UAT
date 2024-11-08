# -*- coding: utf-8 -*-

import datetime
from odoo import fields, models, api, _
from odoo.fields import Command

from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class TenancyContract(models.Model):
    _inherit = "tenancy.contract"

    def create_invoice(self):
        maintenance_req = self.env['maintenance.request'].search([('tenancy_id', '=', self.id)])
        inv_lines = []
        for line in maintenance_req.sparepart_ids:
            if self.req_approve_stage != 'approved':
                raise ValidationError("Maintenance Request not approved please check")
            if self.approve_stage != 'approved':
                raise ValidationError("Deferred Revenue not closed please check")
            if self.order_id:
                invoices = self.env['account.move'].search([('so_ids', 'in', [self.order_id.id])])
                if invoices:
                    for rec in invoices:
                        if rec.state == 'draft':
                            rec.state = 'cancel'
                self.order_id.state = 'cancel'
                self.state = 'closed'
            if self.unit_id:
                for unit in self.unit_id:
                    unit.state = 'available'
            if not line.property_account_income_id:
                raise ValidationError(_("Please set income account in %s", line.product_id.name))
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.product_id.id,
                    'quantity': line.Qty,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': line.cost,
                     'tax_ids': [Command.set(line.taxes_id.ids)],
                    'account_id': line.property_account_income_id.id
                },
            )
            )
        for line in self.project_id.early_termination_product:
            if not line.property_account_income_id:
                raise ValidationError(_("Please set income account in %s", line.name))
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.id,
                    'quantity': 1,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': self.early_termination_penalty_amount,
                    'tax_ids': [Command.set(line.taxes_id.ids)],
                    'account_id': line.property_account_income_id.id
                },
            )
            )
        for line in self.unit_id:
            if not line.property_account_income_id:
                raise ValidationError(_("Please set income account in %s", line.name))
            inv_lines.append((
                0,
                0,
                {
                    'product_id': line.id,
                    'quantity': 1,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': self.payable_amount,
                    'tax_ids': [Command.set(line.taxes_id.ids)],
                    'account_id': line.property_account_income_id.id
                },
            )
            )

        inv_vals = {
            'partner_id': self.order_id.partner_id.id,
            'invoice_date': self.start_date or datetime.today().date(),
            # 'invoice_date_due': date.today(),
            'invoice_date_due': self.start_date or datetime.today().date(),
            'invoice_payment_term_id': self.order_id.payment_term_id.id,
            'invoice_line_ids': inv_lines,
            'move_type': 'out_invoice',
            'so_ids': self.order_id.id,
            'state': 'draft',
            'project': self.project_id.id,
            'building': self.building_id.id,
            'floor': self.floor_id.id,
            'unit': self.unit_id.ids,
            'invoice_origin': self.name,
            # 'unit': installment.order_id.unit.id,
        }
        self.env['account.move'].create(inv_vals)
