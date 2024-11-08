from odoo import api, fields, models, api,Command, _
from odoo.exceptions import UserError,ValidationError
from datetime import date


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # state = selection_add = [("booked", "Booked"), ("expired", "Expired")]
    state = fields.Selection(selection_add=[("booked", "Booked"), ("expired", "Expired")])
    is_token_invoice = fields.Boolean(default=False)

    invoice_line_dum_ids = fields.One2many('account.voucher.line','order_id', string="Invoices")
    token_invoice_ids = fields.One2many(
        "account.move", "order_id", string="Token Money Invoices",
        readonly=True
    )

    # def compute_invoice_line_dum_ids(self):
    #     for obj in self:
    #         invoice_ids = []
    #         get_invoice_ids = self.env['account.move'].search(
    #             [('order_id', '=', obj.id), ('is_token_money_obj', '=', True)])
    #         if get_invoice_ids:
    #             invoice_ids = get_invoice_ids.ids
    #         obj.invoice_line_dum_ids = [(6, 0, invoice_ids)]

    # @api.constrains('token_invoice_ids')
    # def constrains_token_invoice_ids(self):
    #     for rec in self:
    #         if len(rec.token_invoice_ids) > 0:
    #             tenancy_payment_plan = self.rent_plan_ids.search([('order_id', '=', rec.id)])
    #             for tenancy_plan in tenancy_payment_plan:
    #                 tenancy_plan.is_token_created = True

    def _can_be_confirmed(self):
        super(SaleOrderInherit, self)._can_be_confirmed()
        return self.state in {'draft', 'sent', 'booked', 'expired', 'approved'}

    def token_money_schedule_run(self):
        orders = self.env['sale.order'].sudo().search([('state', '=', 'booked')])
        today_date = date.today()
        for rec in orders:
            if rec.validity_date < today_date:
                rec.state = 'expired'
            if rec.unit:
                for units in rec.unit:
                    if units.is_unit:
                        units.state = 'available'

class AccountVoucherLine(models.Model):
    _name='account.voucher.line'

    date = fields.Date(string='Date')
    # amount_total = fields.Monetary(string='Amount Total')
    amount_advance = fields.Float(string='Amount Advance')
    due_date = fields.Date(string='Due Date')
    reference_id = fields.Many2one('payment.plan', string='Reference')
    order_id = fields.Many2one('sale.order')
    is_invoiced = fields.Boolean(string="Is Invoiced")


    def button_create_invoice(self):
        self.order_id.is_token_invoice = True
        self.is_invoiced = True
        self.order_id.validity_date = self.due_date
        tenancy_payment_plan = self.order_id.rent_plan_ids.search(
            [('is_token_money', '=', True), ('order_id', '=', self.order_id.id)])

        if tenancy_payment_plan:
            # tenancy_payment_plan.is_token_created = True
            tenancy_payment_plan.token_amount = tenancy_payment_plan.token_amount + self.amount_advance
        else:
            # tenancy_payment_plan.is_token_created = True
            tenancy_payment_plan.token_amount = tenancy_payment_plan.token_amount

        bill = {
            'partner_id': self.order_id.partner_id.id,
            'invoice_date': self.date,
            'date': self.date,
            'state': 'draft',
            'so_ids': self.order_id.id,
            'project': self.order_id.project.id,
            'building': self.order_id.building.id,
            'floor': self.order_id.floor.id,
            'unit': self.order_id.unit.ids,
            # 'source_id': self.order_id.id,
            # 'is_afm': True,
            'is_token_money_obj': True,
            'move_type': 'out_invoice',

        }
        if self.reference_id.is_booked and self.order_id.project:
            bill.update({'reference': self.reference_id.id})
        analytic_distribution = {}
        for rec in self.order_id.order_line:
            analytic_distribution = rec.analytic_distribution
        booking_charge_product = self.env['product.template'].sudo().search([('name', '=', 'Booking Charges')], limit=1)
        if self.order_id.for_sale:
            if self.order_id.project.sales_booking_product:
                if not self.order_id.project.sales_booking_product.property_account_income_id:
                    raise ValidationError(_("Please set income account in %s",
                                            self.order_id.project.sales_booking_product.name))
                invoice_line_ids = [(0, 0, {
                    'product_id': self.order_id.project.sales_booking_product.id,
                    'name': "Booking Charges",
                    'price_unit': 1.0 * self.amount_advance,
                    'quantity': 1.0,
                    'tax_ids': [Command.set(self.order_id.project.sales_booking_product.taxes_id.ids)],
                    'account_id': self.order_id.project.sales_booking_product.property_account_income_id.id,
                    'analytic_distribution': analytic_distribution
                })]
                if invoice_line_ids:
                    bill.update({'invoice_line_ids': invoice_line_ids})
        if self.order_id.for_rent:
            if self.order_id.project.lease_booking_product:
                if not self.order_id.project.lease_booking_product.property_account_income_id:
                    raise ValidationError(_("Please set income account in %s",
                                            self.order_id.project.lease_booking_product.name))
                invoice_line_ids = [(0, 0, {
                    'product_id': self.order_id.project.lease_booking_product.id,
                    'name': "Booking Charges",
                    'price_unit': 1.0 * self.amount_advance,
                    'quantity': 1.0,
                    'tax_ids': [Command.set(self.order_id.project.lease_booking_product.taxes_id.ids)],
                    'account_id': self.order_id.project.lease_booking_product.property_account_income_id.id,
                    'analytic_distribution': analytic_distribution
                })]
                if invoice_line_ids:
                    bill.update({'invoice_line_ids': invoice_line_ids})
        record = self.env['account.move'].create(bill)
        if record:
            self.order_id.token_invoice_ids |= record
            self.order_id.invoice_ids = [(4, record.id)]
        payment_plan = self.env['payment.plan'].search([('is_booked', '=', True)])
        if payment_plan and self.order_id:
            if payment_plan not in self.order_id.plan_ids.mapped('milestone_id'):
                # order_line = self.order_id.order_line.filtered(lambda l: l.product_id.is_booked == True)
                # amount = sum(order_line.mapped('price_subtotal'))
                self.order_id.plan_ids.create({
                    'milestone_id': payment_plan.id,
                    'order_id': self.order_id.id,
                    'start_date': self.order_id.date_order,
                    'end_date': self.order_id.end_date,
                    'amount': self.amount_advance,
                    'percentage': (self.amount_advance / sum(self.order_id.order_line.mapped('price_unit'))) * 100
                })
        return {
            "type": "ir.actions.act_window_close",
        }


class TokenMoneySettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    product_id = fields.Many2one('product.product', string='Product for Token Money',
                                 config_parameter='token_money.product_id')
    # tax_afm = fields.Many2one('account.tax', string='Tax for AFM', config_parameter='ol_property_custom.tax_afm')


class TokenWizardInherit(models.TransientModel):
    _inherit = 'account.voucher.wizard.sale'

    def make_advance_payment(self):
        payment_plan = self.env['payment.plan'].search([('is_booked', '=', True)])
        self.env['account.voucher.line'].create({
            'order_id': self.order_id.id,
            'date': self.date,
            'amount_advance': self.amount_advance,
            'reference_id': payment_plan.id,
        })
        # self.ensure_one()
        # payment_obj = self.env["account.payment"]
        # sale_obj = self.env["sale.order"]
        #
        # sale_ids = self.env.context.get("active_ids", [])
        # if sale_ids:
        #     order_id = fields.first(sale_ids)
        #     sale = sale_obj.browse(order_id)
        #     payment_vals = self._prepare_payment_vals(sale)
        #     payment = payment_obj.create(payment_vals)
        #     sale.account_payment_ids |= payment
        #     # payment.action_post()
        #     product_name = self.order_id.partner_id.name
        #     print(f'product_name: {product_name}')
        #     product_unit = self.env['product.product'].search([('name', '=', self.order_id.partner_id.name)])
        #     print(product_unit)
        #     product_unit.state = 'reserved'

        bill = {}
        # self.order_id.rent_plan_ids.search([('is_token_money', '=', True)])
        # self.order_id.is_token_invoice = True
        # self.order_id.validity_date = self.due_date
        #
        # tenancy_payment_plan = self.order_id.rent_plan_ids.search(
        #     [('is_token_money', '=', True), ('order_id', '=', self.order_id.id)])
        #
        # if tenancy_payment_plan:
        #     # tenancy_payment_plan.is_token_created = True
        #     tenancy_payment_plan.token_amount = tenancy_payment_plan.token_amount + self.amount_advance
        # else:
        #     # tenancy_payment_plan.is_token_created = True
        #     tenancy_payment_plan.token_amount = tenancy_payment_plan.token_amount
        #
        # bill = {
        #     'partner_id': self.order_id.partner_id.id,
        #     'invoice_date': self.date,
        #     'date': self.date,
        #     'state': 'draft',
        #     'so_ids': self.order_id.id,
        #     'project': self.order_id.project.id,
        #     'building': self.order_id.building.id,
        #     'floor': self.order_id.floor.id,
        #     'unit': self.order_id.unit.ids,
        #     # 'source_id': self.order_id.id,
        #     # 'is_afm': True,
        #     'is_token_money_obj': True,
        #     'move_type': 'out_invoice'}
        # analytic_distribution = {}
        # for rec in self.order_id.order_line:
        #     analytic_distribution = rec.analytic_distribution
        # booking_charge_product = self.env['product.template'].sudo().search([('name', '=', 'Booking Charges')], limit=1)
        #
        # if self.order_id.for_sale:
        #     if self.order_id.project.sales_booking_product:
        #         if not self.order_id.project.sales_booking_product.property_account_income_id:
        #             raise ValidationError(_("Please set income account in %s",
        #                                     self.order_id.project.sales_booking_product.name))
        #         invoice_line_ids = [(0, 0, {
        #             'product_id': self.order_id.project.sales_booking_product.id,
        #             'name': "Booking Charges",
        #             'price_unit': 1.0 * self.amount_advance,
        #             'quantity': 1.0,
        #             'tax_ids': [Command.set(self.order_id.project.sales_booking_product.taxes_id.ids)],
        #             'account_id': self.order_id.project.sales_booking_product.property_account_income_id.id,
        #             'analytic_distribution': analytic_distribution
        #         })]
        #         if invoice_line_ids:
        #             bill.update({'invoice_line_ids': invoice_line_ids})
        # if self.order_id.for_rent:
        #     if self.order_id.project.lease_booking_product:
        #         if not self.order_id.project.lease_booking_product.property_account_income_id:
        #             raise ValidationError(_("Please set income account in %s",
        #                                     self.order_id.project.lease_booking_product.name))
        #         invoice_line_ids = [(0, 0, {
        #             'product_id': self.order_id.project.lease_booking_product.id,
        #             'name': "Booking Charges",
        #             'price_unit': 1.0 * self.amount_advance,
        #             'quantity': 1.0,
        #             'tax_ids': [Command.set(self.order_id.project.lease_booking_product.taxes_id.ids)],
        #             'account_id': self.order_id.project.lease_booking_product.property_account_income_id.id,
        #             'analytic_distribution': analytic_distribution
        #         })]
        #         if invoice_line_ids:
        #             bill.update({'invoice_line_ids': invoice_line_ids})
        # record = self.env['account.move'].create(bill)
        # if record:
        #     self.order_id.token_invoice_ids |= record
        #     self.order_id.invoice_ids = [(4, record.id)]
        # payment_plan = self.env['payment.plan'].search([('is_booked', '=', True)])
        # if payment_plan and self.order_id:
        #     if payment_plan not in self.order_id.plan_ids.mapped('milestone_id'):
        #         # order_line = self.order_id.order_line.filtered(lambda l: l.product_id.is_booked == True)
        #         # amount = sum(order_line.mapped('price_subtotal'))
        #         self.order_id.plan_ids.create({
        #             'milestone_id': payment_plan.id,
        #             'order_id': self.order_id.id,
        #             'start_date': self.order_id.date_order,
        #             'end_date': self.order_id.end_date,
        #             'amount': self.amount_advance,
        #             'percentage': (self.amount_advance / sum(self.order_id.order_line.mapped('price_unit'))) * 100
        #         })
        # payment_plan = self.env['payment.plan'].search([('is_oqood', '=', True)])
        # if payment_plan and self.order_id:
        #     if payment_plan not in self.order_id.plan_ids.mapped('milestone_id'):
        #         # order_line = self.order_id.order_line.filtered(lambda l: l.product_id.is_booked == True)
        #         # amount = sum(order_line.mapped('price_subtotal'))
        #         self.order_id.plan_ids.create({
        #             'milestone_id': payment_plan.id,
        #             'order_id': self.order_id.id,
        #             'start_date': self.order_id.date_order,
        #             'end_date': self.order_id.end_date,
        #             'amount': self.amount_advance,
        #             'percentage': (self.amount_advance / sum(self.order_id.order_line.mapped('price_unit'))) * 100
        #         })
        # payment_plan = self.env['payment.plan'].search([('is_dld', '=', True)])
        # if payment_plan and self.order_id:
        #     if payment_plan not in self.order_id.plan_ids.mapped('milestone_id'):
        #         # order_line = self.order_id.order_line.filtered(lambda l: l.product_id.is_booked == True)
        #         # amount = sum(order_line.mapped('price_subtotal'))
        #         self.order_id.plan_ids.create({
        #             'milestone_id': payment_plan.id,
        #             'order_id': self.order_id.id,
        #             'start_date': self.order_id.date_order,
        #             'end_date': self.order_id.end_date,
        #             'amount': self.amount_advance,
        #             'percentage': (self.amount_advance / sum(self.order_id.order_line.mapped('price_unit'))) * 100
        #         })
        return {
            "type": "ir.actions.act_window_close",
        }


class AccountPaymentRegisterInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.order_id:
            for rec in self.order_id:
                if rec.is_token_invoice:
                    rec.state = 'sale'
        if self.order_id.unit:
            for units in self.order_id.unit:
                if units.is_unit:
                    if units.for_rent:
                        units.state = 'reserved'
                    if units.for_sale:
                        units.state = 'booked'
        return vals


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    order_id = fields.Many2one(
        "sale.order",
        "Purchase",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    is_token_money_obj = fields.Boolean(string="Token Money Obj", default=False)


class RentPaymentPlanLines(models.Model):
    _inherit = 'rent.payment.plan.line'

    def create_inv(self):
        record = super(RentPaymentPlanLines, self).create_inv()

        for installment in self:
            if self.is_token_money:
                setting_param = int(self.env['ir.config_parameter'].sudo().get_param('token_money.product_id'))
                product_id = self.env['product.product'].browse(setting_param)
                price_unit = -abs(sum(installment.order_id.invoice_line_dum_ids.mapped('amount_total_signed'))) if installment and installment.order_id and installment.order_id.invoice_line_dum_ids else 0
                # product_variant_id = product_id.product_variant_id
                print("cvvvvvvvvvv", price_unit)
                self.move_id.invoice_line_ids.create({
                    'move_id': self.move_id.id,
                    'product_id': product_id.id,
                    'price_unit': price_unit
                })
