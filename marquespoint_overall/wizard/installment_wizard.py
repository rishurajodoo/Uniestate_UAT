from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class RescheduledWizard(models.TransientModel):
    _name = 'reschedulement.wizard'
    _description = 'Reschedulement Wizard'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    installment_period = fields.Selection([
        ('month', 'Month'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('bi_annual', 'Bi-Annual'),
    ], 'Installment Period')
    installment_no = fields.Integer('Revised Installments No', compute='_compute_installment_no')
    order_id = fields.Many2one('sale.order')
    installments_due = fields.Float(string="Installment Due.", readonly=True)
    amounts_due = fields.Float(string="Amount Due.", readonly=True)
    payment_plan_line = fields.Many2one('payment.plan.line', string='Payment Plan Line')
    is_submitted = fields.Boolean(default=False, copy=False)
    is_approved = fields.Boolean(default=False, copy=False)

    def submit_for_approval_schedule(self):
        reschedule_approval = self.env['sales.reschedule.approval'].search([], limit=1)
        if not self.payment_plan_line.is_approved:
            if reschedule_approval:
                for approval_line in reschedule_approval.line_ids:
                    for user in approval_line.user_ids:
                        user_note = f'This activity assigned to User: {user.name}, please press "Mark AS DONE" to approve.'
                        existing_activity = self.env['mail.activity'].search([
                            ('res_id', '=', self.order_id.id),
                            ('user_id', '=', user.id),
                            ('note', '=', user_note),
                            ('payment_plan_line', '=', self.payment_plan_line.id),
                            ('state', 'in', ['pending', 'done']),
                        ], limit=1)

                        if not existing_activity:
                            print("Creating Reschedule activity for user:", user.id)
                            new_activity = self.env['mail.activity'].create({
                                'activity_type_id': self.env.ref(
                                    'marquespoint_overall.notification_schedule_approval').id,
                                'res_id': self.order_id.id,
                                'res_model_id': self.env['ir.model']._get('sale.order').id,
                                'user_id': user.id,
                                'payment_plan_line': self.payment_plan_line.id,
                                'summary': 'Reschedule Approval',
                                'note': user_note
                            })
                            print("Activity created for user:", new_activity.user_id.id)
                            self.order_id.schedule_activity_one = True

            # Save the wizard data in the reschedule.wizard.data model without Many2one link to the transient model
            self.env['reschedule.wizard.data'].create({
                'milestone_id': self.milestone_id.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'installment_period': self.installment_period,
                'installment_no': self.installment_no,
                'order_id': self.order_id.id,
                'installments_due': self.installments_due,
                'amounts_due': self.amounts_due,
                'is_submitted': True,
                'is_approved': False
            })

        self.payment_plan_line.submit_approval = True

    def create_installments(self):
        if self.amounts_due == 0 or self.installment_no == 0:
            raise UserError('Amount or Installment No are Missing')
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        installment_ids = self.env['installment.line'].search(
            [('order_id', '=', active_id.order_id.id), ('inv_status', '=', 'draft'),
             ('payment_status', '=', 'Not Paid'),
             ('milestone_id', '=', active_id.milestone_id.id)])
        for install in installment_ids:
            install.move_id.button_cancel()
            # install.unlink()
        active_id.write({
            'installments_due': self.installments_due,
            'amounts_due': self.amounts_due,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'installment_no': self.installment_no,
            'installment_period': self.installment_period,
        })
        # Validations
        # amount = self.amount / self.installment_no
        for _ in range(self.installment_no):
            inv_date = self.start_date
            if self.installment_period == 'month':
                inv_date += relativedelta(months=_)
                print(f'inv date: {inv_date}')
            elif self.installment_period == 'quarterly':
                inv_date += relativedelta(months=_ * 3)
            elif self.installment_period == 'annual':
                inv_date += relativedelta(months=_ * 12)
            elif self.installment_period == 'bi_annual':
                bi_annual_date = self.start_date + relativedelta(months=6)
                inv_date = bi_annual_date + relativedelta(months=_ * 6) + relativedelta(days=-1)
            vals = {
                'milestone_id': self.milestone_id.id,
                'amount': self.amounts_due / self.installment_no,
                'order_id': self.order_id.id,
                'date': inv_date,
                # ''
            }
            installment = self.env['installment.line'].create(vals)
            inv_lines = [
                (
                    0,
                    0,
                    {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'commission_status': line.commission_status,
                        'quantity': line.product_uom_qty,
                        'product_uom_id': line.product_uom.id,
                        'price_unit': self.amounts_due / self.installment_no,
                        'tax_ids': line.tax_id,
                        'sale_line_ids': line,
                    },
                )
                for line in self.order_id.order_line
            ]
            inv_vals = {
                'partner_id': self.order_id.partner_id.id,
                'invoice_date': installment.date,
                'invoice_line_ids': inv_lines,
                'move_type': 'out_invoice',
                'so_ids': self.order_id.id,
                'state': 'draft',
                'project': self.order_id.project.id,
                'building': self.order_id.building.id,
                'floor': self.order_id.floor.id,
                'invoice_origin': self.order_id.name,
                # 'unit': self.unit.id,
                'unit': self.order_id.unit,
                'reference': self.milestone_id.id
            }
            invoice = self.env['account.move'].create(inv_vals)
            invoice.reference = self.milestone_id.id
            installment.move_id = invoice.id
        # for plan in self.order_id.plan_ids:
        # for installment in self.order_id.installment_ids:
        # if plan.milestone_id == installment.milestone_id:
        # invoice = None
        # if self.order_id.order_line:
        # inv_lines = [
        #     (
        #         0,
        #         0,
        #         {
        #             'product_id': line.product_id.id,
        #             'name': line.name,
        #             'quantity': line.product_uom_qty,
        #             'product_uom_id': line.product_uom.id,
        #             'price_unit': installment.amount,
        #             'tax_ids': line.tax_id,
        #             'sale_line_ids': line,
        #         },
        #     )
        #     for line in self.order_id.order_line
        # ]
        # inv_vals = {
        #     'partner_id': self.order_id.partner_id.id,
        #     'invoice_date': installment.date,
        #     'invoice_line_ids': inv_lines,
        #     'move_type': 'out_invoice',
        #     'so_ids': self.order_id.id,
        #     'state': 'draft',
        #     'project': self.order_id.project.id,
        #     'building': self.order_id.building.id,
        #     'floor': self.order_id.floor.id,
        #     'invoice_origin': self.order_id.name,
        #     # 'unit': self.unit.id,
        #     'unit': self.order_id.unit,
        # }
        # invoice = self.env['account.move'].create(inv_vals)
        # installment.move_id = invoice.id
        print('installment created')

    @api.depends('installment_period', 'start_date', 'end_date')
    def _compute_installment_no(self):
        delta = relativedelta(self.end_date, self.start_date)
        res_months = delta.months + (delta.years * 12)
        res_quarters = res_months // 3
        res_years = delta.years
        res_bi_annual = res_months // 6
        if self.installment_period == 'annual':
            self.installment_no = res_years + 1
        elif self.installment_period == 'quarterly':
            self.installment_no = res_quarters + 1
        elif self.installment_period == 'month':
            self.installment_no = res_months + 1
        elif self.installment_period == 'bi_annual':
            self.installment_no = res_bi_annual + 1
        else:
            self.installment_no = 0



class InstallmentWizard(models.TransientModel):
    _name = 'installment.wizard'
    _description = 'Installment Wizard'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    trigger_dates_later = fields.Boolean(string="Trigger Dates Later")
    is_booked = fields.Boolean()
    percentage = fields.Float('Percentage')
    amount = fields.Float('Amount', compute='_compute_amount')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    installment_period = fields.Selection([
        ('month', 'Month'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('bi_annual', 'Bi-Annual'),
    ], 'Installment Period')
    installment_no = fields.Integer('Installment No', compute='_compute_installment_no')
    order_id = fields.Many2one('sale.order')
    is_token_money = fields.Boolean('Token Money Included')
    is_admin = fields.Boolean()
    is_admin_fee = fields.Boolean('DLD+Admin Fee')
    admin_fee = fields.Float('Amount')

    # @api.onchange('is_token_money')
    # def _onchange_token(self):
    #     print(self.is_token_money)
    #     print(self.order_id)
    #     print(self.order_id.account_payment_ids)

    @api.depends('percentage', 'order_id.amount_untaxed', 'milestone_id.amount', 'is_token_money', 'is_admin_fee',
                 'admin_fee')
    def _compute_amount(self):
        if self.is_admin_fee:
            self.amount = self.admin_fee
            self.percentage = 0
        # elif self.percentage:
        #     self.amount = sum(self.order_id.order_line.filtered(lambda l: l.product_id.is_unit).mapped('price_unit'))
        elif self.percentage and self.order_id.amount_untaxed:
            amount = sum(self.order_id.order_line.filtered(lambda l: l.product_id.is_unit).mapped('price_unit'))
            self.amount = amount * (self.percentage / 100.0)
            # self.amount = self.order_id.amount_untaxed * (self.percentage / 100.0)
            if self.is_token_money:
                if temp := sum(
                        payment.amount
                        for payment in self.order_id.account_payment_ids
                        if payment.state == 'post'
                ):
                    self.amount -= temp
                    product_unit = self.env['product.template'].search(
                        [('name', '=', self.order_id.partner_id.name)])
                    product_unit.state = 'reserved'
        elif self.percentage and self.milestone_id.amount:
            self.amount = self.milestone_id.amount * (self.percentage / 100.0)
            if self.is_token_money:
                if temp := sum(
                        payment.amount
                        for payment in self.order_id.account_payment_ids
                        if payment.state == 'post'
                ):
                    self.amount -= temp
                    product_unit = self.env['product.product'].search(
                        [('name', '=', self.order_id.partner_id.name)])
                    product_unit.state = 'reserved'
        elif not self.milestone_id.is_oqood:
            self.percentage = 100
            self.amount = sum(
                self.order_id.order_line.filtered(lambda l: l.product_id.is_unit == True).mapped('price_unit'))
        elif not self.milestone_id.is_dld:
            self.percentage = 100
            self.amount = sum(
                self.order_id.order_line.filtered(lambda l: l.product_id.is_unit == True).mapped('price_unit'))
        elif not self.milestone_id.is_service_charges:
            self.percentage = 100
            self.amount = sum(
                self.order_id.order_line.filtered(lambda l: l.product_id.is_unit == True).mapped('price_unit'))
        else:
            self.amount = 0.0

    @api.depends('installment_period', 'start_date', 'end_date', 'trigger_dates_later')
    def _compute_installment_no(self):
        if not self.trigger_dates_later:
            delta = relativedelta(self.end_date, self.start_date)
            res_months = delta.months + (delta.years * 12)
            res_quarters = res_months // 3
            res_years = delta.years
            res_bi_annual = res_months // 6
            if self.installment_period == 'annual':
                self.installment_no = res_years + 1
            elif self.installment_period == 'quarterly':
                self.installment_no = res_quarters + 1
            elif self.installment_period == 'month':
                self.installment_no = res_months + 1
            elif self.installment_period == 'bi_annual':
                self.installment_no = res_bi_annual + 1
            else:
                self.installment_no = 0
        else:
            self.installment_no = 1

    def create_installments(self):
        if self.amount == 0 or self.installment_no == 0:
            raise UserError('Amount or Installment No are Missing')
        if self.percentage < 0:
            raise ValidationError('Please Enter Positive value for Percentage')
        model = self.env.context.get('active_model')
        active_id = self.env[model].browse(self.env.context.get('active_id'))
        self.env['installment.line'].search(
            [('milestone_id', '=', self.milestone_id.id), ('order_id', '=', self.order_id.id)]).unlink()
        active_id.write({
            'amount': self.amount,
            'percentage': self.percentage,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'installment_no': self.installment_no,
            'installment_period': self.installment_period,
            'is_admin_fee': self.is_admin_fee,
        })
        # Validations
        plan_ids = active_id.order_id.plan_ids.filtered(
            lambda l: l.milestone_id.is_dld == False and l.milestone_id.is_oqood == False)
        if plan_ids:
            # total_percentage = sum(percen.percentage for percen in plan_ids)
            total_percentage = 0
            for percen in plan_ids:
                if percen.milestone_id.is_dld or percen.milestone_id.is_service_charges or percen.milestone_id.is_oqood:
                    total_percentage = total_percentage + percen.percentage
            total_amount = sum(line.amount for line in plan_ids if not line.is_admin_fee)
            print(f'total_percentage: {total_percentage}')
            print(f'total_amount: {total_amount}')
            print(f'self.order_id.amount_untaxed: {active_id.order_id.amount_untaxed}')
            remaining_percentage = 100 - (total_percentage - self.percentage)
            if total_amount > active_id.order_id.amount_untaxed:
                raise ValidationError('The amount is Exceeding the sale order')
            if total_percentage > 100:
                raise ValidationError(
                    f'Capacity: 100%\nFilled: {total_percentage - self.percentage}% \nRemaining: {remaining_percentage}%')
        #     End validations
        # amount = self.amount / self.installment_no
        for _ in range(self.installment_no):
            inv_date = self.start_date
            if self.installment_period == 'month':
                inv_date += relativedelta(months=_)
                print(f'inv date: {inv_date}')
            elif self.installment_period == 'quarterly':
                inv_date += relativedelta(months=_ * 3)
            elif self.installment_period == 'annual':
                inv_date += relativedelta(months=_ * 12)
            elif self.installment_period == 'bi_annual':
                bi_annual_date = self.start_date + relativedelta(months=6)
                inv_date = bi_annual_date + relativedelta(months=_ * 6) + relativedelta(days=-1)
            vals = {
                'milestone_id': self.milestone_id.id,
                # 'amount': amount,
                'order_id': self.order_id.id,
                'date': inv_date
            }
            self.env['installment.line'].create(vals)
        print('installment created')

    @api.constrains('is_token_money')
    def _is_token_money(self):
        if self.is_token_money:
            temp = sum(
                payment.amount for payment in self.order_id.account_payment_ids if payment.state == 'post')
            # if not temp:
            #     raise UserError('Please Create a Token Money for Adjustment')

