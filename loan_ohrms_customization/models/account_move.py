# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    hr_loan_line_id = fields.Many2one('hr.loan.line', string='Hr Loan Line')
