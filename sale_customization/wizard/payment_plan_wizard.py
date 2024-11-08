from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class PaymentPlanWizard(models.TransientModel):
    _name = 'payment.plan.wizard'
    _description = 'Payment Plan'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    number_of_installments = fields.Integer(string='Number of Installments')
    is_chiller_charges = fields.Boolean('Is Chiller Charge Included', default=False)
    chiller_charge_config = fields.Boolean('Chiller Charge Config')
    is_booking_adjusted = fields.Boolean(string="Is Booking Adjusted", copy=False)

    def create_payment_plan(self):
        start_date = self.start_date
        end_date = self.end_date
        number_of_installments = self.number_of_installments
        if number_of_installments <= 0:
            raise UserError('Number of installments must be greater than 0')
        if not self.start_date or not self.end_date:
            raise UserError("Please select start date and end date into the wizard")
        if self.end_date < self.start_date:
            raise UserError("End Date is small than Start Date")

        total_days = (end_date - start_date).days
        total_month = round(total_days / (365 / 12))
        diff_month = total_month / number_of_installments
        month_convert_into_days = diff_month * (365 / 12)

        days_per_installment = total_days // number_of_installments

        sale_order_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        milestone_ids = self.env['payment.plan'].search([('is_invoice', '=', True)], order='sequence asc',
                                                        limit=number_of_installments)

        if sale_order_id.state == 'sale':
            raise UserError("You are not able to create Tenancy payment plan after confirm the sale order")

        is_invoice_tenancy_payment_plan_ids = sale_order_id.rent_plan_ids.filtered(
            lambda l: l.milestone_id.is_invoice == True)

        for is_invoice_tenancy_payment_plan_id in is_invoice_tenancy_payment_plan_ids:
            is_invoice_tenancy_payment_plan_id.unlink()

        if len(milestone_ids) < number_of_installments:
            raise UserError("Milestone is not available as per your requirement for installment")
        first_milestone = True  # Flag to track the first milestone
        for milestone_id in milestone_ids:
            if diff_month == int(diff_month):
                end_date = start_date + (relativedelta(months=int(diff_month)) - relativedelta(days=1))
            else:
                end_date = (start_date + relativedelta(days=days_per_installment))
            sale_order_line_id = sale_order_id.order_line.filtered(lambda l: l.product_id.is_unit == True)
            if self.is_chiller_charges:
                sale_order_line_id += sale_order_id.order_line.filtered(
                    lambda l: l.product_id.is_chiller_charges == True)
            amount = sum(sale_order_line_id.mapped('price_subtotal')) / number_of_installments
            percentage = 0.0
            if sale_order_line_id:
                percentage = amount / sum(sale_order_line_id.mapped('price_subtotal')) * 100
            if first_milestone and sale_order_id.for_rent and self.is_booking_adjusted:
                amount -= float(sale_order_id.advance_booking_amount)
                first_milestone = False
            vals = {
                'milestone_id': milestone_id.id,
                'start_date': start_date,
                'end_date': end_date,
                'order_id': sale_order_id.id,
                'amount': amount,
                'percentage': percentage,
                'is_chiller_charges': self.is_chiller_charges
            }
            self.env['rent.payment.plan.line'].create(vals)
            start_date = end_date + relativedelta(days=1)
        return True
