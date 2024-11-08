# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    """Model for Loan Requests for employees."""
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        """ Retrieve default values for specified fields. """
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['partner_id'] = self.env['res.partner'].search(
            [('user_id', '=', ts_user_id)], limit=1).id
        return result

    @api.depends('loan_line_ids.interest_amount', 'loan_line_ids.amount', 'loan_line_ids.paid')
    def _compute_loan_amount(self):
        """ calculate the total amount paid towards the loan. """
        total_paid = 0.0
        total_int_pa_amount = 0.0
        total_int_amount = 0.0
        for loan in self:
            for line in loan.loan_line_ids:
                total_int_pa_amount += line.int_pa_amount
                total_int_amount += line.interest_amount
                if line.paid:
                    total_paid += line.amount + line.interest_amount
            balance_amount = total_int_pa_amount - total_paid
            loan.total_amount = total_int_pa_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid
            loan.total_interest_amount = total_int_amount
            loan.total_principal_amount = loan.loan_amount

    name = fields.Char(string="Loan Name", default="/", readonly=True,
                       help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(),
                       readonly=True, help="Date")
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner",
                                  required=True, help="Contract")
    # department_id = fields.Many2one(comodel_name='hr.department',
    #                                 related="employee_id.department_id",
    #                                 readonly=True,
    #                                 string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1,
                                 help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True,
                               default=fields.Date.today(),
                               help="Date of the payment")
    loan_line_ids = fields.One2many(comodel_name='hr.loan.line',
                                    help="Loan lines",
                                    inverse_name='loan_id', string="Loan Line",
                                    index=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 help="Company",
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  string='Currency', required=True,
                                  help="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id)
    # job_position_id = fields.Many2one(comodel_name='hr.job',
    #                                   related="employee_id.job_id",
    #                                   readonly=True, string="Job Position",
    #                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True,
                               help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True,
                                readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True,
                                  compute='_compute_loan_amount',
                                  help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True,
                                     compute='_compute_loan_amount',
                                     help="Total paid amount")
    total_interest_amount = fields.Float(string="Total Interest Amount", store=True,
                                     compute='_compute_loan_amount',
                                     help="Total Interest amount")
    total_principal_amount = fields.Float(string="Total Principal Amount", store=True,
                                         compute='_compute_loan_amount',
                                         help="Total Principal amount")

    state = fields.Selection([
        ('draft', 'Draft'), ('running', 'Running'), ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'), ('refuse', 'Refused'), ('cancel', 'Canceled'),
    ], string="State", help="states of loan request", default='draft',
        tracking=True, copy=False, )

    principal_product_id = fields.Many2one(comodel_name='product.product', string="Principal Product",
                                 required=True)
    interest_product_id = fields.Many2one(comodel_name='product.product', string="Interest Product",
                                           required=True)
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        required=True)
    move_ids = fields.Many2many('account.move', string='Bills Ref', copy=False)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')

    @api.model
    def create(self, values):
        """creates a new HR loan record with the provided values."""
        loan_count = self.env['hr.loan'].search_count(
            [('partner_id', '=', values['partner_id']),
             ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(
                _("The partner has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    def action_compute_installment(self):
        """This automatically create the installment the employee need to pay
        to company based on payment start date and the no of installments."""
        for loan in self:
            loan.loan_line_ids.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'partner_id': loan.partner_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    # def action_refuse(self):
    #     """Action to refuse the loan"""
    #     return self.write({'state': 'refuse'})

    def action_submit(self):
        """Action to submit the loan"""
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        """Action to cancel the loan"""
        self.write({'state': 'cancel'})

    def action_running(self):
        self.write({'state': 'running'})

    def action_create_bill(self):
        for loan in self:
            if loan.loan_line_ids:
                if loan.invoice_count == 0:
                    for line in loan.loan_line_ids:
                        account_move = self.env['account.move'].create({
                            'partner_id': loan.partner_id.id,
                            'invoice_date': line.date,
                            'move_type': 'in_invoice',
                            'hr_loan_line_id': line.id,
                            'invoice_line_ids':  [
                                Command.create({'product_id': loan.principal_product_id.id, 'price_unit': line.amount,
                                                'account_id': loan.employee_account_id.id,
                                                'analytic_distribution': {loan.account_id.id: 100}, 'quantity': 1}),
                                Command.create({'product_id': loan.interest_product_id.id, 'analytic_distribution': {loan.account_id.id: 100},
                                                'account_id': loan.employee_account_id.id,
                                                'price_unit': line.interest_amount, 'quantity': 1}),
                            ],
                        })
                        self.move_ids = [(4, account_move.id)]
                else:
                    raise ValidationError(
                        _("Bill already generated"),
                    )
            else:
                raise ValidationError(
                    _("No installment lines"),
                )
        self.write({'state': 'waiting_approval_1'})

    def _compute_invoice_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('id', 'in', self.move_ids.ids)])
            rec.invoice_count = count

    def action_get_bill_invoice_jv(self):
        return {
            'name': _('Bills'),
            'domain': [('id', 'in', self.move_ids.ids)],
            'view_type': 'tree',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    # def action_approve(self):
    #     """Approve loan by the manager"""
    #     for data in self:
    #         if not data.loan_line_ids:
    #             raise ValidationError(_("Please Compute installment"))
    #         else:
    #             self.write({'state': 'approve'})

    def unlink(self):
        """Unlink loan lines"""
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or '
                    'cancelled state')
        return super(HrLoan, self).unlink()
