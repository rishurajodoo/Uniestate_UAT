# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentTerms(models.Model):
    """ Module for extending account.payment.term model to add interest
    computation configuration features for computation of Interest in overdue
    invoices."""

    _inherit = "account.payment.term"

    interest_overdue_act = fields.Boolean(default=False,
                                          string="Interest on Overdue Invoices",
                                          help="Activate Interest computation "
                                               "for this Payment term.")
    interest_type = fields.Selection(
        string='Interest Type', help="Base duration for interest calculation",
        selection=[('daily', 'Daily'),
                   ('weekly', 'Weekly'),
                   ('monthly', 'Monthly')], default='daily', copy=False)
    interest_percentage = fields.Float(string="Interest Percentage",
                                       default="0", digits=(12, 6),
                                       help="Interest percentage ratio per"
                                            " selected Interest type duration.")
    interest_product_ids = fields.Many2many('product.product',
                                          string='Product for Interest',
                                          help="Account used for creating "
                                               "accounting entries.")
    account_payment_interest_ids = fields.One2many('account.payment.interest','account_payment_term_id')

    @api.constrains('interest_percentage')
    def _check_interest_percentage(self):
        """ check constrains for validating the interest rate in percentage
        is not negative"""
        for rec in self:
            if rec.interest_overdue_act and rec.interest_percentage <= 0:
                raise ValidationError(_('Enter Positive value as Interest '
                                      'percentage'))


class AccountPaymentInterest(models.Model):
    _name = 'account.payment.interest'

    interest_payment_type = fields.Selection(
        string='Interest Payment Type',
        selection=[('percentage', 'percentage(%)'),
                   ('fixed', 'Fixed'),
                   ],  default='percentage', copy=False)
    interest_duration = fields.Selection(
        string='Interest Type', help="Base duration for interest calculation",
        selection=[('daily', 'Daily'),
                   ('weekly', 'Weekly'),
                   ('monthly', 'Monthly')], default='daily', copy=False)
    sequence = fields.Integer(string='Sequence')
    amount_percentage = fields.Float(string='Amount / %')
    start_day = fields.Integer(string='Start Day')
    end_day = fields.Integer(string='End Day')
    account_payment_term_id = fields.Many2one('account.payment.term')