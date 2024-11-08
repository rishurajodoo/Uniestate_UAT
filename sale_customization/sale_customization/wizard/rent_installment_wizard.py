from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class InstallmentWizard(models.TransientModel):
    _name = 'rent.installment.wizard'
    _description = 'Installment Wizard For Rent'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    # percentage = fields.Float('Percentage')
    percentage = fields.Float('Percentage', compute='_compute_percentage')
    # amount = fields.Float('Amount', compute='_compute_amount')
    amount = fields.Float('Amount')
    type = fields.Selection([
        ('cheque', 'Cheque'),
        ('cash_bank', 'Cash/Bank'),
    ], string='Payment Mode', default='cheque')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    order_id = fields.Many2one('sale.order')
    # no_of_cheques = fields.Integer('Cheques')
    is_post_cheque = fields.Boolean('Security Cheque', default=False)
    post_amount = fields.Float('Security Cheque Amount')
    is_ejari = fields.Boolean('Ejari', default=False)
    is_utility_charge = fields.Boolean('Utility Charge', default=False)
    is_renewal = fields.Boolean('Renewal', default=False)
    is_tax_include = fields.Boolean('Tax included', default=False, help='Tax will calculate only if this is checked')
    tax_amount = fields.Float(string="Tax Amount", compute='_compute_tax_amount')
    is_booked = fields.Boolean('Is Booked')
    is_token_money = fields.Boolean(string="Token Money")

    # @api.onchange('is_token_money')
    # def onchnage_token_money(self):
    #     for rec in self:
    #         print(rec)

    @api.depends('amount', 'is_tax_include')
    def _compute_tax_amount(self):
        for rec in self:
            # if rec.milestone_id.is_post_cheque == False and rec.milestone_id.is_ejari == False:
            if rec.is_tax_include == True:
                order_liness = rec.order_id.order_line
                for record in order_liness:
                    if record.product_id.is_unit == True and record.is_debit == False and rec.milestone_id.is_post_cheque == False and rec.milestone_id.is_ejari == False and rec.milestone_id.is_debit == False and rec.milestone_id.is_renewal == False and rec.milestone_id.is_utility_charge == False:
                        # if record.is_unit == True:
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    elif record.product_id.is_unit == True and record.is_debit == True and rec.milestone_id.is_debit == True and rec.milestone_id.is_post_cheque == False and rec.milestone_id.is_ejari == False and rec.milestone_id.is_renewal == False and rec.milestone_id.is_utility_charge == False:
                        # if record.is_unit == True:
                        # record.product_id.is_unit == True and
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    elif record.product_id.is_sec == True and rec.milestone_id.is_post_cheque == True:
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    elif record.product_id.is_ejari == True and rec.milestone_id.is_ejari == True:
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    elif record.product_id.is_renewal == True and rec.milestone_id.is_renewal == True:
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    elif record.product_id.is_utility_charge == True and rec.milestone_id.is_utility_charge == True:
                        tax = (rec.amount * record.tax_id.amount) / 100
                        rec.tax_amount = tax
                        break
                    # elif record:
                    #     tax = (rec.amount * record.tax_id.amount) / 100
                    #     rec.tax_amount = tax
                    else:
                        rec.tax_amount = 0

                # for record in order_liness:
                #     if record:
                #         tax = (rec.amount * record.tax_id.amount)/100
                #         rec.tax_amount = tax
                #     else:
                #         rec.tax_amount = 0
            else:
                rec.tax_amount = 0

    @api.depends('amount')
    def _compute_percentage(self):
        for record in self:
            order_lines = record.order_id.order_line
            amount_total = sum(line.price_subtotal for line in order_lines)
            amount_total_is_unit = sum(line.price_subtotal for line in order_lines if line.product_id.is_unit)

            if amount_total_is_unit != 0:  # Check if amount_total_is_unit is zero to avoid ZeroDivisionError
                record.percentage = (record.amount / amount_total_is_unit) * 100
            else:
                record.percentage = 0

        #     self.percentage = self.amount * 100 / self.order_id.order_line[0].price_unit
        # @api.depends('percentage', 'order_id.amount_untaxed', 'milestone_id.amount', 'is_post_cheque', 'post_amount')

    # def _compute_amount(self):
    #     if self.is_post_cheque:
    #         self.amount = self.post_amount
    #         self.percentage = 0
    #     elif self.percentage and self.order_id.amount_untaxed:
    #         self.amount = self.order_id.amount_untaxed * (self.percentage / 100.0)
    #     elif self.percentage and self.milestone_id.amount:
    #         self.amount = self.milestone_id.amount * (self.percentage / 100.0)
    #     else:
    #         self.amount = 0

    def create_installments(self):
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        # if self.amount == 0:
        #     raise UserError("Amount can't be Empty")
        # if self.percentage < 0:
        #     raise ValidationError('Please Enter Positive value for Percentage')
        # self.env['rent.installment.line'].search(
        #     [('milestone_id', '=', self.milestone_id.id), ('order_id', '=', self.order_id.id)]).unlink()
        if active_id.order_id.rent_plan_ids:
            total_percentage = sum(percen.percentage for percen in active_id.order_id.rent_plan_ids)
            # total_percentage = sum(percen.percentage for percen in active_id.order_id.rent_plan_ids if not percen.milestone_id.is_post_cheque)
            total_amount = sum(line.amount for line in active_id.order_id.rent_plan_ids)
            # total_amount = sum(line.amount for line in active_id.order_id.rent_plan_ids if not line.milestone_id.is_post_cheque)
            print(f'total_percentage: {total_percentage}')
            print(f'total_amount: {total_amount}')
            print(f'self.order_id.amount_untaxed: {active_id.order_id.amount_untaxed}')
            remaining_percentage = 100 - (total_percentage)
            print(f'remaining_percentage: {remaining_percentage}')
            print(f'self.order_id.amount_tax: {self.order_id.amount_tax}')
            # if total_amount > active_id.order_id.amount_untaxed:
            #     raise ValidationError('The amount is Exceeding the sale order')
            if total_amount >= self.order_id.amount_untaxed:
                raise ValidationError('The amount is Exceeding the sale order')
            # or total_percentage > 100
            # else:
            #     if total_percentage > 100:
            #         raise ValidationError('The amount is Exceeding the sale order')
            # f'Capacity: 100%\nFilled: {total_percentage - self.percentage}% \nRemaining: {remaining_percentage}%')
        #     End validations
        if self.is_ejari == False or self.is_post_cheque == False or self.is_renewal == False or self.is_utility_charge == False:
            active_id.write({
                'amount': self.amount or self.post_amount,
                'percentage': self.percentage,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'is_tax_include': self.is_tax_include,
                'tax_amount': self.tax_amount,
                'is_token_money': self.is_token_money,
                'type': self.type,
                # 'no_of_cheques': self.no_of_cheques,
            })
        else:
            active_id.write({
                'amount': self.amount or self.post_amount,
                'percentage': 0,
                'type': self.type,
                'tax_amount': self.tax_amount,
                'is_token_money': self.is_token_money,
                # 'no_of_cheques': self.no_of_cheques,
            })
        # Validations
        # if active_id.order_id.rent_plan_ids:
        #     total_percentage = sum(percen.percentage for percen in active_id.order_id.rent_plan_ids if not percen.milestone_id.is_post_cheque)
        #     total_amount = sum(line.amount for line in active_id.order_id.rent_plan_ids if not line.milestone_id.is_post_cheque)
        #     print(f'total_percentage: {total_percentage}')
        #     print(f'total_amount: {total_amount}')
        #     print(f'self.order_id.amount_untaxed: {active_id.order_id.amount_untaxed}')
        #     remaining_percentage = 100 - (total_percentage)
        #     print(f'remaining_percentage: {remaining_percentage}')
        #     print(f'self.order_id.amount_tax: {self.order_id.amount_tax}')
        #     # if total_amount > active_id.order_id.amount_untaxed:
        #     #     raise ValidationError('The amount is Exceeding the sale order')
        #     if self.order_id.amount_tax > 0:
        #         if total_percentage > 105:
        #             raise ValidationError('The amount is Exceeding the sale order')
        #     else:
        #         if total_percentage > 100:
        #             raise ValidationError('The amount is Exceeding the sale order')
        #             # f'Capacity: 100%\nFilled: {total_percentage - self.percentage}% \nRemaining: {remaining_percentage}%')
        # #     End validations

    @api.onchange('is_ejari')
    def onchange_is_ejari(self):
        for rec in self:
            rec.is_ejari = rec.milestone_id.is_ejari

    @api.onchange('is_renewal')
    def onchange_is_renewal(self):
        for rec in self:
            rec.is_renewal = rec.milestone_id.is_renewal

    @api.onchange('is_utility_charge')
    def onchange_is_utility_charge(self):
        for rec in self:
            rec.is_utility_charge = rec.milestone_id.is_utility_charge
