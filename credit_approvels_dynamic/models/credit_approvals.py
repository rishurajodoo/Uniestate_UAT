import base64
import os
from odoo import models, fields, api, _


class CreditApprovals(models.Model):
    _name = 'credit.approvals'
    _description = 'Credit Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='Approval Name', required=True, tracking=True)
    credit_discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Refund Bill Approval',
        required=True,
        widget='radio'
    )
    credit_minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    credit_minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    credit_companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    credit_approval_level_ids = fields.One2many(
        comodel_name='credit.approvals.levels', inverse_name='credit_id',
        string='Approval Level Details', ondelete='cascade'
    )

class CreditApprovalsLevels(models.Model):
    _name = 'credit.approvals.levels'
    _description = 'Credit Approvals Levels'
    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')
         ],
        string='Approval Level',
    )

    credit_approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    credit_id = fields.Many2one(comodel_name='credit.approvals', string='Approval')

