from email.policy import default

# from pyarrow import string

from odoo import fields, models, api, _
from odoo.tools import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    for_sale = fields.Boolean(default=False)
    for_rent = fields.Boolean(default=False)
    is_renewed = fields.Boolean(default=False)
    is_sale_installments = fields.Boolean(compute='_compute_is_sale_installments')
    is_rent_installments = fields.Boolean(compute='_compute_is_rent_installments')
    outstanding_amount = fields.Float(string="Outstanding Amount", compute="compute_outstanding_amount")
    paid_amount = fields.Float(string="Paid Amount", compute="compute_paid_amount")
    outstanding_percentage = fields.Float(string="Outstanding Amount %", compute="compute_outstanding_amount")
    paid_amount_percentage = fields.Float(string="Paid %", compute="compute_paid_amount")
    schedule_activity_one = fields.Boolean(default=False, copy=False)

    reschedule_count = fields.Integer(compute='_compute_reschedule_count', string='Reschedule Count')


    def action_open_reschedule_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reschedule Requests',
            'view_mode': 'tree,form',
            'res_model': 'reschedule.wizard.data',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def _compute_reschedule_count(self):
        for order in self:
            order.reschedule_count = self.env['reschedule.wizard.data'].search_count([('order_id', '=', order.id)])

    @api.constrains('order_line')
    def create_payment_dld_line(self):
        for rec in self._origin:
            for line in rec.order_line:
                if rec.for_sale:
                    if line.price_subtotal <= 0.0:
                        raise UserError("Please set the price before the save records!")
                    if line.product_id.is_dld:
                        payment_plan_id = self.env['payment.plan'].search([('is_dld', '=', True)])
                        rent_payment_plan_id = self.env['payment.plan.line'].search(
                            [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                        if rent_payment_plan_id:
                            rent_payment_plan_id.unlink()
                        if line.price_subtotal > 0:
                            percentage = (line.price_subtotal / line.price_unit) * 100
                        else:
                            percentage = 0.0
                        if payment_plan_id:
                            payment_plan_line = self.env['payment.plan.line'].create({
                                'milestone_id': payment_plan_id.id,
                                'amount': line.price_subtotal,
                                'start_date': rec.date_order,
                                'order_id': rec.id,
                                'percentage': percentage,
                                'installment_no': 1,
                                'installment_period': 'month'
                            })
                            installment_no = payment_plan_line.installment_no
                            installment_period = payment_plan_line.installment_period
                            for _ in range(installment_no):
                                inv_date = rec.date_order
                                if installment_period == 'month':
                                    inv_date += relativedelta(months=_)
                                    print(f'inv date: {inv_date}')
                                elif installment_period == 'quarterly':
                                    inv_date += relativedelta(months=_ * 3)
                                elif installment_period == 'annual':
                                    inv_date += relativedelta(months=_ * 12)
                                vals = {
                                    'milestone_id': payment_plan_id.id,
                                    'amount': line.price_subtotal / installment_no,
                                    'order_id': rec.id,
                                    'date': inv_date,
                                }
                                self.env['installment.line'].create(vals)
                    if line.product_id.is_oqood:
                        payment_plan_id = self.env['payment.plan'].search([('is_oqood', '=', True)])
                        rent_payment_plan_id = self.env['payment.plan.line'].search(
                            [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                        if rent_payment_plan_id:
                            rent_payment_plan_id.unlink()
                        if line.price_subtotal > 0:
                            percentage = (line.price_subtotal / line.price_unit) * 100
                        else:
                            percentage = 0.0
                        if payment_plan_id:
                            payment_plan_line = self.env['payment.plan.line'].create({
                                'milestone_id': payment_plan_id.id,
                                'amount': line.price_subtotal,
                                'order_id': rec.id,
                                'start_date': rec.date_order,
                                'percentage': percentage,
                                'installment_no': 1,
                                'installment_period': 'month'
                            })
                            installment_no = payment_plan_line.installment_no
                            installment_period = payment_plan_line.installment_period
                            for _ in range(installment_no):
                                inv_date = rec.date_order
                                if installment_period == 'month':
                                    inv_date += relativedelta(months=_)
                                    print(f'inv date: {inv_date}')
                                elif installment_period == 'quarterly':
                                    inv_date += relativedelta(months=_ * 3)
                                elif installment_period == 'annual':
                                    inv_date += relativedelta(months=_ * 12)
                                vals = {
                                    'milestone_id': payment_plan_id.id,
                                    'amount': line.price_subtotal / installment_no,
                                    'order_id': rec.id,
                                    'date': inv_date,
                                }
                                self.env['installment.line'].create(vals)
                    if line.product_id.is_service_charges:
                        payment_plan_id = self.env['payment.plan'].search([('is_service_charges', '=', True)])
                        rent_payment_plan_id = self.env['payment.plan.line'].search(
                            [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                        if rent_payment_plan_id:
                            rent_payment_plan_id.unlink()
                        if line.price_subtotal > 0:
                            percentage = (line.price_subtotal / line.price_unit) * 100
                        else:
                            percentage = 0.0
                        if payment_plan_id:
                            payment_plan_line = self.env['payment.plan.line'].create({
                                'milestone_id': payment_plan_id.id,
                                'amount': line.price_subtotal,
                                'start_date': rec.date_order,
                                'order_id': rec.id,
                                'percentage': percentage,
                                'installment_no': 1,
                                'installment_period': 'month'
                            })
                            installment_no = payment_plan_line.installment_no
                            installment_period = payment_plan_line.installment_period
                            for _ in range(installment_no):
                                inv_date = rec.date_order
                                if installment_period == 'month':
                                    inv_date += relativedelta(months=_)
                                    print(f'inv date: {inv_date}')
                                elif installment_period == 'quarterly':
                                    inv_date += relativedelta(months=_ * 3)
                                elif installment_period == 'annual':
                                    inv_date += relativedelta(months=_ * 12)
                                vals = {
                                    'milestone_id': payment_plan_id.id,
                                    'amount': line.price_subtotal / installment_no,
                                    'order_id': rec.id,
                                    'date': inv_date,
                                }
                                self.env['installment.line'].create(vals)

    def action_open_voucher_wizard(self):
        sale_unit = self.search(
            [('for_sale', '=', True), ('unit', 'in', self.unit.ids), ('state', '=', 'sale')])
        if sale_unit:
            # if self.state in ['approved', 'sale', 'booked']:
            raise ValidationError("Another Sale Order exists with the same unit , in sale or booked state !!!!!!")
            # else:
            #     action = self.env["ir.actions.actions"]._for_xml_id(
            #         "marquespoint_overall.action_view_account_voucher_wizard")
            # self.env['payment.plan.line'].search([]).is_booked
        else:
            # action = self.env["ir.actions.actions"]._for_xml_id(
            #     "marquespoint_overall.action_view_account_voucher_wizard")
            # Added booking Id and return via action and set default ref as booking
            booking_id = self.env['payment.plan'].search([
                ("name", "=", "Booking"),
                ("is_booked", "=", True)
            ], limit=1)
            return {
                'name': 'Advance Payment',
                'type': 'ir.actions.act_window',
                'res_model': 'account.voucher.wizard.sale',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_reference_id': booking_id.id},
            }

        # return action

    def compute_outstanding_amount(self):
        for rec in self:
            draft_invoice = rec.invoice_ids.filtered(lambda l: l.payment_state == 'not_paid')
            partial_posted_invoice = rec.invoice_ids.filtered(lambda l: l.state == 'posted' and l.payment_state == 'partial')
            if partial_posted_invoice:
                draft_invoice_amount = sum(draft_invoice.mapped('amount_residual_signed'))
                partial_invoice_amount = sum(partial_posted_invoice.mapped('amount_residual'))
                rec.outstanding_amount = draft_invoice_amount + partial_invoice_amount
                if rec.ins_amount:
                    rec.outstanding_percentage = (rec.outstanding_amount / rec.ins_amount) * 100
                else:
                    rec.outstanding_percentage = rec.outstanding_percentage
            elif draft_invoice:
                rec.outstanding_amount = sum(draft_invoice.mapped('amount_residual_signed'))
                if rec.ins_amount:
                    rec.outstanding_percentage = (rec.outstanding_amount / rec.ins_amount) * 100
                else:
                    rec.outstanding_percentage = rec.outstanding_percentage
            else:
                rec.outstanding_amount = rec.outstanding_amount
                rec.outstanding_percentage = rec.outstanding_percentage

    def compute_paid_amount(self):
        for rec in self:
            draft_invoice = rec.invoice_ids.filtered(lambda l: l.state == 'draft')
            partial_posted_invoice = rec.invoice_ids.filtered(lambda l: l.state == 'posted' and l.payment_state in ('partial', 'not_paid'))
            if partial_posted_invoice:
                partial_posted_invoice = sum(partial_posted_invoice.mapped('amount_residual'))
                if self.ins_amount != 0:
                    rec.paid_amount = self.ins_amount - partial_posted_invoice
                else:
                    rec.paid_amount = partial_posted_invoice
                if rec.ins_amount:
                    rec.paid_amount_percentage = (rec.paid_amount / rec.ins_amount) * 100
                else:
                    rec.paid_amount_percentage = rec.paid_amount_percentage
            elif draft_invoice:
                rec.paid_amount = sum(draft_invoice.mapped('amount_total_signed'))
                if rec.ins_amount:
                    rec.paid_amount_percentage = (rec.paid_amount / rec.ins_amount) * 100
                else:
                    rec.paid_amount_percentage = rec.paid_amount_percentage
            else:
                rec.paid_amount = rec.paid_amount
                rec.paid_amount_percentage = rec.paid_amount_percentage

    def action_cancel_marquespoint_overall(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Order',
            'view_id': self.env.ref('marquespoint_overall.view_cancel_sale_wizard_form', False).id,
            'target': 'new',
            'res_model': 'cancel.sale.wizard',
            'context': {
                'default_refund_amount': self.paid_amount - (
                        (self.project.cancellation_percentage * self.amount_total) / 100),
                'default_total_amount':  self.paid_amount - (
                        (self.project.cancellation_percentage * self.amount_total) / 100)
            },
            'view_mode': 'form',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['is_crm'] = False
        return super().create(vals_list)

    @api.depends('state', 'for_sale')
    def _compute_is_sale_installments(self):
        for rec in self:
            if rec.unit and rec.for_sale and rec.is_crm:
                price_per_unit = rec.opportunity_id.expected_revenue / len(rec.unit)
                rec.write({
                    'purchaser_ids': [(0, 0, {
                        'purchase_individual': rec.opportunity_id.partner_id.id,
                        'purchase_company': rec.opportunity_id.company_id.id or rec.opportunity_id.env.company.id,
                    })]
                })
                for unit in rec.unit:
                    rec.write({
                        #'partner_id': self.env['res.partner'].search([('name', '=', unit.name)], limit=1).id,
                        'partner_id': rec.opportunity_id.partner_id.id,
                        'order_line': [(0, 0, {
                            'product_id': unit.id,
                            'product_uom_qty': 1,
                            'price_unit': price_per_unit,
                            'product_uom': unit.uom_id.id,
                            'tax_id': False,
                            'analytic_distribution': {unit.units_analytic_account.id: 100}
                        })]
                    })
            if rec.state == 'sale' and rec.for_sale:
                rec.is_sale_installments = True
                print('--------------------------Pass')
            else:
                rec.is_sale_installments = False
                print('--------------------------False')

    @api.depends('state', 'for_rent')
    def _compute_is_rent_installments(self):
        for rec in self:
            if rec.unit and rec.for_rent and rec.is_crm:
                price_per_unit = self.opportunity_id.expected_revenue / len(rec.unit)
                for unit in rec.unit:
                    rec.write({
                        'order_line': [(0, 0, {
                            'product_id': unit.id,
                            'product_uom_qty': 1,
                            'price_unit': price_per_unit,
                            'product_uom': unit.uom_id.id,
                            'tax_id': False,
                            'is_ejari': True,
                            'analytic_distribution': {unit.units_analytic_account.id: 100}
                        })]
                    })
            if rec.state == 'sale' and rec.for_rent:
                rec.is_rent_installments = True
                print('--------------------------Pass')
            else:
                rec.is_rent_installments = False
                print('--------------------------False')

    @api.constrains('for_sale', 'for_rent')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.for_sale and rec.for_rent:
                raise UserError("You Can't be able to select both Sale and Rent on same time")

    account_payment_ids = fields.One2many(
        "account.payment", "order_id", string="Pay purchase advanced", readonly=True
    )
    amount_residual = fields.Float(
        "Residual amount",
        readonly=True,
        compute="_compute_sale_advance_payment",
        store=True,
    )
    payment_line_ids = fields.Many2many(
        "account.move.line",
        string="Payment move lines",
        compute="_compute_sale_advance_payment",
        store=True,
    )
    advance_payment_status = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute="_compute_sale_advance_payment",
    )

    @api.depends(
        "currency_id",
        "company_id",
        "amount_total",
        "account_payment_ids",
        "account_payment_ids.state",
        "account_payment_ids.move_id",
        "account_payment_ids.move_id.line_ids",
        "account_payment_ids.move_id.line_ids.date",
        "account_payment_ids.move_id.line_ids.debit",
        "account_payment_ids.move_id.line_ids.credit",
        "account_payment_ids.move_id.line_ids.currency_id",
        "account_payment_ids.move_id.line_ids.amount_currency",
        "order_line.invoice_lines.move_id",
        "order_line.invoice_lines.move_id.amount_total",
        "order_line.invoice_lines.move_id.amount_residual",
    )
    def _compute_sale_advance_payment(self):
        for order in self:
            mls = order.account_payment_ids.mapped("move_id.line_ids").filtered(
                lambda x: x.account_id.account_type == "asset_receivable"
                          and x.parent_state == "posted"
            )
            advance_amount = 0.0
            for line in mls:
                line_currency = line.currency_id or line.company_id.currency_id
                # Exclude reconciled pre-payments amount because once reconciled
                # the pre-payment will reduce bill residual amount like any
                # other payment.
                line_amount = (
                    line.amount_residual_currency
                    if line.currency_id
                    else line.amount_residual
                )
                if line_currency != order.currency_id:
                    advance_amount += line.currency_id._convert(
                        line_amount,
                        order.currency_id,
                        order.company_id,
                        line.date or fields.Date.today(),
                    )
                else:
                    advance_amount += line_amount
            # Consider payments in related invoices.
            invoice_paid_amount = 0.0
            for inv in order.invoice_ids:
                invoice_paid_amount += inv.amount_total - inv.amount_residual
            amount_residual = order.amount_total + advance_amount - invoice_paid_amount
            payment_state = "not_paid"
            if mls or order.invoice_ids:
                has_due_amount = float_compare(
                    amount_residual, 0.0, precision_rounding=order.currency_id.rounding
                )
                if has_due_amount <= 0:
                    payment_state = "paid"
                elif has_due_amount > 0:
                    payment_state = "partial"
            order.payment_line_ids = mls
            order.amount_residual = amount_residual
            order.advance_payment_status = payment_state

    # ------------------------------------------------------------------

    def _prepare_invoice(self, ):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'project': self.project.id,
            'building': self.building.id,
            'floor': self.floor.id,
            'unit': self.unit.id,
            'so_ids': self.id,
        })
        return invoice_vals

    plan_ids = fields.One2many('payment.plan.line', 'order_id')
    installment_ids = fields.One2many('installment.line', 'order_id')
    ins_amount = fields.Float('Total', compute='_compute_installment_amount')

    def _compute_installment_amount(self):
        for rec in self:
            records = self.env['installment.line'].search([('order_id', '=', rec.id)])
            amount = sum(line.amount for line in records)
            rec.ins_amount = amount

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.for_sale:
            product_unit = self.env['product.product'].search([('name', '=', self.partner_id.name)])
            if product_unit:
                product_unit.state = 'available'
            if self.plan_ids:
                self.plan_ids.unlink()
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.for_sale:
            if product_unit := self.env['product.product'].search(
                    [('name', '=', self.partner_id.name)]
            ):
                product_unit.state = 'sold'

            for plan in self.plan_ids:
                for installment in self.installment_ids:
                    if plan.milestone_id == installment.milestone_id:
                        if not plan.milestone_id.is_dld and not plan.milestone_id.is_oqood and not plan.milestone_id.is_service_charges:
                            invoice = None
                            if self.order_line.filtered(
                                    lambda l: l.product_id.is_dld == False and l.product_id.is_oqood == False):
                                inv_lines = [
                                    (
                                        0,
                                        0,
                                        {
                                            'product_id': line.product_id.id,
                                            'name': line.name,
                                            'quantity': line.product_uom_qty,
                                            'product_uom_id': line.product_uom.id,
                                            'price_unit': installment.amount,
                                            'tax_ids': line.tax_id,
                                            'sale_line_ids': line,
                                        },
                                    )
                                    for line in self.order_line.filtered(
                                        lambda
                                            l: l.product_id.is_dld == False and l.product_id.is_oqood == False and l.product_id.is_service_charges == False)
                                ]
                                inv_vals = {
                                    'partner_id': self.partner_id.id,
                                    'invoice_date': installment.date,
                                    'invoice_date_due': installment.date,
                                    'invoice_payment_term_id': installment.order_id.payment_term_id.id,
                                    'invoice_line_ids': inv_lines,
                                    'move_type': 'out_invoice',
                                    'so_ids': self.id,
                                    'state': 'draft',
                                    'project': self.project.id,
                                    'building': self.building.id,
                                    'floor': self.floor.id,
                                    'invoice_origin': self.name,
                                    # 'unit': self.unit.id,
                                    'unit': self.unit,
                                    'reference': plan.milestone_id.id
                                }
                                invoice = self.env['account.move'].create(inv_vals)
                                installment.move_id = invoice.id
                        if plan.milestone_id.is_dld and not plan.milestone_id.is_oqood:
                            invoice = None
                            if self.order_line.filtered(
                                    lambda l: l.product_id.is_dld == True and l.product_id.is_oqood == False):
                                inv_lines = [
                                    (
                                        0,
                                        0,
                                        {
                                            'product_id': line.product_id.id,
                                            'name': line.name,
                                            'quantity': line.product_uom_qty,
                                            'product_uom_id': line.product_uom.id,
                                            'price_unit': installment.amount,
                                            'tax_ids': line.tax_id,
                                            'sale_line_ids': line,
                                        },
                                    )
                                    for line in self.order_line.filtered(
                                        lambda l: l.product_id.is_dld == True and l.product_id.is_oqood == False)
                                ]
                                inv_vals = {
                                    'partner_id': self.partner_id.id,
                                    'invoice_date': installment.date,
                                    'invoice_date_due': installment.date,
                                    'invoice_payment_term_id': installment.order_id.payment_term_id.id,
                                    'invoice_line_ids': inv_lines,
                                    'move_type': 'out_invoice',
                                    'so_ids': self.id,
                                    'state': 'draft',
                                    'project': self.project.id,
                                    'building': self.building.id,
                                    'floor': self.floor.id,
                                    'invoice_origin': self.name,
                                    # 'unit': self.unit.id,
                                    'unit': self.unit,
                                    'reference': plan.milestone_id.id
                                }
                                invoice = self.env['account.move'].create(inv_vals)
                                installment.move_id = invoice.id
                        if not plan.milestone_id.is_dld and plan.milestone_id.is_oqood:
                            invoice = None
                            if self.order_line.filtered(
                                    lambda l: l.product_id.is_dld == False and l.product_id.is_oqood == True):
                                inv_lines = [
                                    (
                                        0,
                                        0,
                                        {
                                            'product_id': line.product_id.id,
                                            'name': line.name,
                                            'quantity': line.product_uom_qty,
                                            'product_uom_id': line.product_uom.id,
                                            'price_unit': installment.amount,
                                            'tax_ids': line.tax_id,
                                            'sale_line_ids': line,
                                        },
                                    )
                                    for line in self.order_line.filtered(
                                        lambda l: l.product_id.is_dld == False and l.product_id.is_oqood == True)
                                ]
                                inv_vals = {
                                    'partner_id': self.partner_id.id,
                                    'invoice_date': installment.date,
                                    'invoice_date_due': installment.date,
                                    'invoice_payment_term_id': installment.order_id.payment_term_id.id,
                                    'invoice_line_ids': inv_lines,
                                    'move_type': 'out_invoice',
                                    'so_ids': self.id,
                                    'state': 'draft',
                                    'project': self.project.id,
                                    'building': self.building.id,
                                    'floor': self.floor.id,
                                    'invoice_origin': self.name,
                                    # 'unit': self.unit.id,
                                    'unit': self.unit,
                                    'reference': plan.milestone_id.id
                                }
                                invoice = self.env['account.move'].create(inv_vals)
                                installment.move_id = invoice.id

                        if not plan.milestone_id.is_dld and not plan.milestone_id.is_oqood and plan.milestone_id.is_service_charges:
                            invoice = None
                            if self.order_line.filtered(
                                    lambda l: l.product_id.is_dld == False and l.product_id.is_oqood == False and l.product_id.is_service_charges == True):
                                inv_lines = [
                                    (
                                        0,
                                        0,
                                        {
                                            'product_id': line.product_id.id,
                                            'name': line.name,
                                            'quantity': line.product_uom_qty,
                                            'product_uom_id': line.product_uom.id,
                                            'price_unit': installment.amount,
                                            'tax_ids': line.tax_id,
                                            'sale_line_ids': line,
                                        },
                                    )
                                    for line in self.order_line.filtered(
                                        lambda
                                            l: l.product_id.is_dld == False and l.product_id.is_oqood == False and l.product_id.is_service_charges == True)
                                ]
                                inv_vals = {
                                    'partner_id': self.partner_id.id,
                                    'invoice_date': installment.date,
                                    'invoice_date_due': installment.date,
                                    'invoice_payment_term_id': installment.order_id.payment_term_id.id,
                                    'invoice_line_ids': inv_lines,
                                    'move_type': 'out_invoice',
                                    'so_ids': self.id,
                                    'state': 'draft',
                                    'project': self.project.id,
                                    'building': self.building.id,
                                    'floor': self.floor.id,
                                    'invoice_origin': self.name,
                                    # 'unit': self.unit.id,
                                    'unit': self.unit,
                                    'reference': plan.milestone_id.id
                                }
                                invoice = self.env['account.move'].create(inv_vals)
                                installment.move_id = invoice.id

        return res

    def token_money_scheduler(self):
        today_date = date.today()
        sale_orders = self.env['sale.order'].search([])
        print(sale_orders)
        for rec in sale_orders:
            print('token money scheduler')
            if rec.account_payment_ids:
                print(rec.account_payment_ids)
                for payment in rec.account_payment_ids:
                    print(payment)
                    if payment.state == 'draft':
                        print('Draft')
                        print(payment.due_date)
                        print(today_date)
                        print(self.env['product.template'].search(
                            [('name', '=', rec.partner_id.name)]))
                        if payment.due_date == today_date:
                            product_unit = self.env['product.product'].search(
                                [('name', '=', rec.partner_id.name)])
                            if product_unit:
                                product_unit.state = 'available'
                                payment.state = 'cancel'

    def unlink(self):
        for rec in self:
            if rec.plan_ids:
                rec.plan_ids.unlink()
        return super(SaleOrder, self).unlink()

    @api.onchange('order_line')
    def _on_order_line_change(self):
        print('_on_order_line_change')
        for rec in self:
            if rec.amount_untaxed:
                for plan in rec.plan_ids:
                    if plan.percentage:
                        plan.amount = rec.amount_untaxed * (plan.percentage / 100.0)

    #     These functions are used for sale quote report
    def get_is_installments_available(self, milestone):
        return any(
            installment.milestone_id == milestone
            for installment in self.installment_ids
        )

    def action_cancel_renew_order(self):
        deffered_revenues = self.env['deffered.revenue'].search([('order_id', '=', self.id),('state', '=', 'open')])
        if deffered_revenues:
            raise ValidationError("There seems to be Posted Accounting entry linked with this order Kindly ask the relevant team to make it as draft")
        invoice_ids = self.env['account.move'].search(
            [('so_ids', 'in', [self.id]), ('state', '=', 'posted')])
        if invoice_ids:
            raise ValidationError("Invoices In Posted State")
        for line in self.unit:
            line.write({
                'state': 'available'
            })
        draft_invoices = self.env['account.move'].search(
            [('so_ids', 'in', [self.id]), ('state', '=', 'draft')])
        for draft_invoice in draft_invoices:
            draft_invoice.write({
                'state': 'cancel'
            })
        deffered_revenue_close = self.env['deffered.revenue'].search([('order_id', '=', self.id)])
        for revenue in deffered_revenue_close:
            revenue.write({
                'state': 'close'
            })
        if self.tenancy:
            self.tenancy.state = 'closed'
        self.write({
            'state': 'cancel'
        })

#
# # -----------------------------------------
# # This function is used to attach custom reportd in email
#     def _find_mail_template(self, force_confirmation_template=False):
#         self.ensure_one()
#         template_id = False
#         if self.state == 'sale':
#             # template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
#             # template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
#             if not template_id:
#                 template_id = self.env['ir.model.data']._xmlid_to_res_id('marquespoint_overall.mail_template_sale_confirmation', raise_if_not_found=False)
#         if not template_id:
#             template_id = self.env['ir.model.data']._xmlid_to_res_id('marquespoint_overall.email_template_edi_sale', raise_if_not_found=False)
#
#         return template_id
class PaymentPlanLines(models.Model):
    _name = 'payment.plan.line'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    order_id = fields.Many2one('sale.order')
    state = fields.Selection(
        related='order_id.state',
        string="Order Status",
        copy=False, store=True, precompute=True)
    percentage = fields.Float('Percentage')
    amount = fields.Float('Amount')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    installment_no = fields.Integer('Installment No')
    installment_period = fields.Char('Installment Period')
    ac_date_eng = fields.Char('Anticipated completion Date (English)', size=60)
    ac_date_arabic = fields.Char('Anticipated completion Date (Arabic)', size=60)
    is_admin_fee = fields.Boolean('DLD+Admin Fee')
    installments_due = fields.Float(string="Installment Due.", compute='_get_dues')
    amounts_due = fields.Float(string="Amount Due.", compute='_get_dues')
    submit_approval = fields.Boolean(default=False, copy=False)
    is_approved = fields.Boolean(default=False, copy=False)
    is_available_for_reschedule = fields.Boolean(string="Is Available for reschedule ?",
                                                 compute='_get_is_available_for_reschedule')
    milestone_visible = fields.Boolean(string="Milestone visiblity",related="milestone_id.is_booked")


    def _get_is_available_for_reschedule_1(self):
        for rec in self:
            rec.is_available_for_reschedule = False
            if rec.state == 'state' or rec.milestone_id.is_booked == True:
                rec.is_available_for_reschedule = True

    def _get_is_available_for_reschedule(self):
        for rec in self:
            rec.is_available_for_reschedule = False
            # Set to True if booking is True
            if rec.milestone_id.is_booked == True:
                rec.is_available_for_reschedule = True
            # Also set to True if state is 'sale'
            elif rec.state == 'sale':
                rec.is_available_for_reschedule = True

    # cheque_no = fields.Char(string="Check No")
    # bank_name = fields.Char(string="Bank Name")
    # cheque_date = fields.Date(string="Check Date")

    def _get_dues(self):
        for rec in self:
            records = self.env['installment.line'].search(
                [('milestone_id', '=', rec.milestone_id.id), ('order_id', '=', rec.order_id.id),
                 ('inv_status', '=', 'draft'), ('payment_status', '=', 'Not Paid')])
            amount = sum(line.amount for line in records)
            rec.amounts_due = amount
            rec.installments_due = len(records)

    def action_reschedule(self):
        is_submitted = False
        if self.submit_approval:
            is_submitted = True
        activity = self.env['mail.activity'].search([
            ('res_id', '=', self.order_id.id),
            ('payment_plan_line', '=', self.id),
        ], limit=1)
        print("activity", activity)
        print("activity", activity.payment_plan_line)
        if activity:
            self.is_approved = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reschedule Wizard',
            'view_id': self.env.ref('marquespoint_overall.view_reschedulement_wizard_form', False).id,
            'context': {
                'default_milestone_id': self.milestone_id.id,
                'default_order_id': self.order_id.id,
                'default_installments_due': self.installments_due,
                'default_payment_plan_line': self.id,
                'default_start_date': self.start_date,
                'default_installment_period': self.installment_period,
                'default_installment_no': self.installment_no,
                'default_amounts_due': self.amounts_due,
                'default_submit_approval': is_submitted,
                'default_is_approved': self.is_approved,

            },
            'target': 'new',
            'res_model': 'reschedulement.wizard',
            'view_mode': 'form',
        }

    # def open_payment_plan_wizard(self):
    #     percentage = self.milestone_id.percentage
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Create Installment Lines',
    #         'view_id': self.env.ref('marquespoint_overall.view_installment_wizard_form', False).id,
    #         'context': {
    #             'default_milestone_id': self.milestone_id.id,
    #             'default_is_booked': self.milestone_id.is_booked,
    #             'default_is_admin': self.milestone_id.is_admin_fee,
    #             'default_order_id': self.order_id.id,
    #             'default_percentage': percentage,
    #         },
    #         'target': 'new',
    #         'res_model': 'installment.wizard',
    #         'view_mode': 'form',
    #     }

    def unlink(self):
        for rec in self:
            self.env['installment.line'].search(
                [('milestone_id', '=', rec.milestone_id.id), ('order_id', '=', rec.order_id.id)]).unlink()
        return super(PaymentPlanLines, self).unlink()

    def action_booking_milestone(self):
        # if self.id:
        #     print("selfffff", self)
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'name': 'Installment Lines',
        #         'view_id': self.env.ref('marquespoint_overall.view_plan_line_wizard_form', False).id,
        #         'target': 'new',
        #         'res_model': 'payment.plan.line',
        #         'res_id': self.id,
        #         'view_mode': 'form',
        #     }
        percentage = self.milestone_id.percentage
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Installment Lines',
            'view_id': self.env.ref('marquespoint_overall.view_installment_wizard_form', False).id,
            'context': {
                'default_milestone_id': self.milestone_id.id,
                'default_is_booked': self.milestone_id.is_booked,
                'default_is_admin': self.milestone_id.is_admin_fee,
                'default_order_id': self.order_id.id,
                'default_percentage': percentage,
            },
            'target': 'new',
            'res_model': 'installment.wizard',
            'view_mode': 'form',
        }


class InstallmentLines(models.Model):
    _name = 'installment.line'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    amount = fields.Float('Amount', compute='_compute_amount')
    move_id = fields.Many2one('account.move', string='Invoice')
    invoice_date = fields.Date('Inv Date', related='move_id.invoice_date')
    invoice_payment_date = fields.Date('Payment Due Date', compute="_compute_payment_date")
    invoice_status = fields.Char(compute='_compute_invoice_status', string='Inv Status')
    inv_status = fields.Selection(related='move_id.state')
    payment_status = fields.Char(compute='_compute_payment_status', string='Payment Status')
    pymt_status = fields.Selection(related='move_id.payment_state')
    order_id = fields.Many2one('sale.order')
    date = fields.Date('Installment Date')

    @api.depends('move_id')
    def _compute_payment_date(self):
        for rec in self:
            if rec.move_id:
                print(self.env['account.payment'].search([('ref', '=', rec.move_id.name)]))
                payments = self.env['account.payment'].search([('ref', '=', rec.move_id.name)])
                if payments:
                    rec.invoice_payment_date = payments[-1].date
                else:
                    rec.invoice_payment_date = False
            else:
                rec.invoice_payment_date = False

    @api.depends('inv_status')
    def _compute_invoice_status(self):
        for rec in self:
            if rec.inv_status:
                print(dict(self.fields_get(allfields=['inv_status'])['inv_status']['selection'])[rec.inv_status])
                # print(dict(self._fields['move_id.state'].selection).get(self.move_id.state))
                rec.invoice_status = dict(self.fields_get(allfields=['inv_status'])['inv_status']['selection'])[
                    rec.inv_status]
            else:
                rec.invoice_status = ''

    @api.depends('pymt_status')
    def _compute_payment_status(self):
        for rec in self:
            if rec.pymt_status:
                rec.payment_status = dict(self.fields_get(allfields=['pymt_status'])['pymt_status']['selection'])[
                    rec.pymt_status]
            else:
                rec.payment_status = ''

    def _compute_amount(self):
        for rec in self:
            if rec.order_id.plan_ids:
                for plan in rec.order_id.plan_ids:
                    if plan.milestone_id == rec.milestone_id:
                        if plan.installment_no != 0:
                            rec.amount = plan.amount / plan.installment_no
                        break
                    else:
                        rec.amount = 0
            else:
                rec.amount = 0

    def unlink(self):
        if self.move_id:
            self.move_id.unlink()
        return super(InstallmentLines, self).unlink()

class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    payment_plan_line = fields.Many2one('payment.plan.line', string='Payment Plan Line')

    def action_done(self):
        print("xcxcxcx", self.payment_plan_line)
        if self.payment_plan_line:
            self.payment_plan_line.is_approved = True
        res = super(MailActivityInherit, self).action_done()
        return res
