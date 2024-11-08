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
from odoo import fields, models, api


class HrLoanLine(models.Model):
    """
        Class for creating installment details
    """
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True,
                       help="Date of the payment")
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner",
                                  help="Employee")
    amount = fields.Float(string="Principal Amount", required=True, help="Principal Amount")
    interest_amount = fields.Float(string="Interest Amount", help="Interest Amount")
    paid = fields.Boolean(string="Paid", help="Paid", compute='_compute_paid', store=True)
    loan_id = fields.Many2one(comodel_name='hr.loan', string="Loan Ref.",
                              help="Loan")
    payslip_id = fields.Many2one(comodel_name='hr.payslip',
                                 string="Payslip Ref.",
                                 help="Payslip")
    int_pa_amount = fields.Float(string="Total Amount", compute="_compute_int_pa_amount", store=True)

    @api.depends('amount', 'interest_amount')
    def _compute_int_pa_amount(self):
        self.int_pa_amount = 0
        for rec in self:
            rec.int_pa_amount = rec.amount + rec.interest_amount

    @api.depends('loan_id.move_ids.state')
    def _compute_paid(self):
        for rec in self:
            posted_moves = rec.loan_id.move_ids.filtered(lambda x: x.state == 'posted')
            if posted_moves:
                for move in posted_moves:
                    if rec.id == move.hr_loan_line_id.id:
                        rec.paid = True
                    else:
                        rec.paid = False
            else:
                rec.paid = False
