# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from num2words import num2words


class AccountMove(models.Model):
    _inherit = 'account.move'

    # payment_ref = fields.Char('Payment Reference')
    attendant = fields.Many2one('res.partner', string="Attendant")
    project_name = fields.Many2one('project.project', 'Project Name')
    project_shipment = fields.Char('Project Shipment')
    project_code = fields.Char('Project Code')
    po_no = fields.Many2one('purchase.order', 'PO No')
    invoice_name = fields.Char('Invoice Name')
    invoice_arabic_name = fields.Char('Invoice Arabic Name')
    total_wd = fields.Char('Total work done')
    total_wd_arabic = fields.Char('Total work done Arabic')
    po_type = fields.Selection([
        ('project', 'Project'),
        ('other', 'Other')
    ], string='PO Type')

    confirmation_date = fields.Datetime('Confirmation Date')
    sub_contractor = fields.Many2one('res.partner', 'Sub-Contractor')
    works = fields.Char('WORKS')
    period = fields.Char('PERIOD')
    contract_order = fields.Char('Contract/Order')
    retention = fields.Float('Retention (%)')
    retention_amount = fields.Float('Retention Amount', compute='_compute_retention_amount')
    advance = fields.Float('Advance (%)')
    advance_amount = fields.Float('Advance Amount', compute='_compute_advance_amount')
    advance_vat = fields.Float('Advance Vat', compute='_compute_advance_vat')
    recoverable = fields.Float('Recoverable')
    nature_of_work = fields.Char('Nature of Work')
    type_of_contract = fields.Char('Type of Contract')
    type = fields.Char("Type")
    location = fields.Char("Location")
    assessment_date = fields.Date("Assessment Date")
    po_total_value = fields.Float(string="Total Value", compute='_compute_po_total_value')
    # int_final = fields.Char(string="Int/Final")

    def amount_to_text(self, amount):
        return num2words(amount)

    @api.depends('retention')
    def _compute_retention_amount(self):
        for rec in self:
            if rec.retention:
                rec.retention_amount = rec.amount_untaxed * (rec.retention / 100)
            else:
                rec.retention_amount = 0

    @api.depends('advance')
    def _compute_advance_amount(self):
        for rec in self:
            if rec.advance:
                rec.advance_amount = rec.amount_untaxed * (rec.advance / 100)
            else:
                rec.advance_amount = 0

    @api.depends('advance_amount')
    def _compute_advance_vat(self):
        for rec in self:
            if rec.advance_amount:
                # rec.advance_vat = rec.amount_tax * rec.advance_amount
                rec.advance_vat = 0
            else:
                rec.advance_vat = 0

    @api.onchange('po_no')
    def _on_change_po_no(self):
        if self.po_no:
            self.purchase_id = self.po_no.id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id:
            return

        # Copy data from PO
        invoice_vals = self.purchase_id.with_company(self.purchase_id.company_id)._prepare_invoice()
        invoice_vals['currency_id'] = self.invoice_line_ids and self.currency_id or invoice_vals.get('currency_id')
        del invoice_vals['ref']
        del invoice_vals['company_id']  # avoid recomputing the currency
        self.update(invoice_vals)

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
        print(po_lines)
        for line in po_lines.filtered(lambda l: not l.display_type):
            print('line is create')
            invoice_line = self.env['account.move.line'].new(line._prepare_account_move_line(self))
            invoice_line.update({
                'contract_per_amount': line.contract_per_amount,
                'contract_amount': line.price_subtotal
            })
            invoice_line.quantity = line.product_qty
            # invoice_line.contract_per_amount = line.contract_per_amount
            # invoice_line.contract_amount= line.price_subtotal
            invoice_line.currency_id = line.currency_id.id
            self.invoice_line_ids += invoice_line
        self.invoice_line_ids = self.invoice_line_ids[:-1]

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)

        # Compute payment_reference.
        if len(refs) == 1:
            self.payment_reference = refs[0]

        self.purchase_id = False

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        if self.purchase_vendor_bill_id.vendor_bill_id:
            self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id:
            return

        # Copy data from PO
        invoice_vals = self.purchase_id.with_company(self.purchase_id.company_id)._prepare_invoice()
        invoice_vals['currency_id'] = self.line_ids and self.currency_id or invoice_vals.get('currency_id')
        del invoice_vals['ref']
        self.update(invoice_vals)

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')

        # Custom

        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            print('line is create')
            new_line = new_lines.new(line._prepare_account_move_line(self))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_line.update({
                'contract_per_amount': line.contract_per_amount,
                'contract_amount': line.price_subtotal,
            })
            new_line.quantity = line.product_qty
            new_lines += new_line
        new_lines._onchange_mark_recompute_taxes()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)

        # Compute payment_reference.
        if len(refs) == 1:
            self.payment_reference = refs[0]

        self.purchase_id = False
        self._onchange_currency()
        self.partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]

    #     Working for Report Totals
    def get_contract_per_amount(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.contract_per_amount:
                total += float(rec.contract_per_amount.replace('%', ''))
        return f'{round(float(total), 2)}%'

    def get_contract_amount(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.contract_amount:
                total += rec.contract_amount
        return total

    def get_previous_percentage(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.previous_percentage:
                total += float(rec.previous_percentage.replace('%', ''))
        return total

    def get_this_month_percentage(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.this_month_percentage:
                total += float(rec.this_month_percentage.replace('%', ''))
        return total

    def get_total_percentage(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.total_percentage:
                total += float(rec.total_percentage.replace('%', ''))
        return total

    def get_percentage_total_amount(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.percentage_total_amount:
                total += float(rec.percentage_total_amount.replace('%', ''))
        return total

    def get_total_bill_amount(self):
        total = 0
        for rec in self.invoice_line_ids:
            if rec.total_bill_amount:
                total += rec.total_bill_amount
        return total

    @api.depends('invoice_line_ids')
    def _compute_po_total_value(self):
        self.po_total_value = 0.0
        for rec in self:
            origins = sum(self.line_ids.mapped('purchase_line_id.order_id.amount_total'))
            if origins:
                rec.po_total_value = origins
            # po_ids = self.line_ids.mapped('purchase_line_id.order_id')
            # if po_ids:
            #     for po_order in po_ids:
            #         if po_order.order_line[0].qty_received == po_order.order_line[0].qty_invoiced:
            #             rec.int_final = 'Final'
            #         else:
            #             rec.int_final = 'Interim'




class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'
    # contract_per_amount = fields.Char('% Contract Amount', compute='_compute_contract_per_amount')
    contract_per_amount = fields.Char('% Contract Amount')
    contract_amount = fields.Float('Contract Amount')
    previous_percentage = fields.Char('Previous', compute='_compute_previous')
    this_month_percentage = fields.Char('This Month', compute='_compute_this_month_percentage')
    total_percentage = fields.Char('Total', compute='_compute_total')
    percentage_total_amount = fields.Char('% Total Amount', compute='_compute_total_percentage')
    previous_bill_amount = fields.Float('Previous Bill', compute='_compute_previous')
    current_bill_amount = fields.Float('Current Bill')
    total_bill_amount = fields.Float('Total Bill', compute='_compute_total')

    is_bill = fields.Boolean(compute='_compute_is_bill')
    is_project = fields.Boolean(compute='_compute_is_project')

    def _compute_is_bill(self):
        for rec in self:
            if rec.move_id.move_type == 'in_invoice':
                rec.is_bill = True
            else:
                rec.is_bill = False

    def _compute_is_project(self):
        for rec in self:
            if rec.move_id.po_type == 'project':
                rec.is_project = True
            else:
                rec.is_project = False

    def _compute_previous(self):
        for rec in self:
            previous_bill = self.env['account.move.line'].search(
                [('purchase_line_id', '=', rec.purchase_line_id.id), ('move_id', '<', rec.move_id.id)])
            if previous_bill:
                current_per = sum([float(line.this_month_percentage.replace('%', '')) for line in previous_bill])
                current_amount = sum([line.current_bill_amount for line in previous_bill])
                if current_per and current_amount:
                    rec.previous_percentage = f'{round(float(current_per), 2)}%'
                    rec.previous_bill_amount = current_amount
                else:
                    rec.previous_percentage = f'0.00%'
                    rec.previous_bill_amount = 0.0
            else:
                rec.previous_percentage = f'0.00%'
                rec.previous_bill_amount = 0.0

    @api.depends('current_bill_amount', 'contract_amount')
    def _compute_this_month_percentage(self):
        for rec in self:
            if rec.current_bill_amount:
                try:
                    temp = rec.current_bill_amount / rec.contract_amount * 100
                    rec.this_month_percentage = f'{round(float(temp), 2)}%'
                except:
                    rec.this_month_percentage = f'0.00%'
            else:
                rec.this_month_percentage = f'0.00%'

    @api.depends('previous_percentage', 'this_month_percentage', 'previous_bill_amount', 'current_bill_amount')
    def _compute_total(self):
        for rec in self:
            if rec.previous_percentage and rec.this_month_percentage:
                previous = float(rec.previous_percentage.replace('%', ''))
                current = float(rec.this_month_percentage.replace('%', ''))
                temp = previous + current
                total = rec.previous_bill_amount + rec.current_bill_amount
                print(f'{previous} + {current} = {temp}')
                if temp and total:
                    rec.total_percentage = f'{round(float(temp), 2)}%'
                    rec.total_bill_amount = total

                else:
                    rec.total_percentage = f'0.00%'
                    rec.total_bill_amount = 0.0
            else:
                rec.total_percentage = f'0.00%'
                rec.total_bill_amount = 0.0

    @api.depends('total_bill_amount')
    def _compute_total_percentage(self):
        for rec in self:
            if rec.total_bill_amount:
                total = 0
                for line in rec.move_id.invoice_line_ids:
                    total += line.total_bill_amount
                print(total)
                if total:
                    temp = (rec.total_bill_amount / total) * 100
                    rec.percentage_total_amount = f'{round(float(temp), 2)}%'
                else:
                    rec.percentage_total_amount = f'0.00%'
            else:
                rec.percentage_total_amount = f'0.00%'

    @api.onchange('current_bill_amount')
    def _on_change_current_bill_amount(self):
        for rec in self:
            if rec.current_bill_amount:
                try:
                    qty = rec.current_bill_amount / rec.contract_amount
                    rec.quantity = qty
                    # rec.price_unit = rec.current_bill_amount
                except:
                    rec.quantity = 0
                    # rec.price_unit = 0

    @api.constrains('current_bill_amount', 'total_bill_amount')
    def get_current_bill_amount(self):
        for rec in self:
            if rec.total_bill_amount > rec.contract_amount:
                raise UserError('Amount exceeded from contract amount')
