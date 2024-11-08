import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountApprovals(models.Model):
    _name = 'account.approvals'
    _description = 'Account Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Purchase Approval',
        required=True,
        widget='radio'
    )
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    approval_level_ids = fields.One2many(
        comodel_name='account.approval.levels', inverse_name='approval_id',
        string='Approval Level Details', ondelete='cascade'
    )
    account_domain = fields.Char("Account domain")


class AccountApprovalsLevels(models.Model):
    _name = 'account.approval.levels'
    _description = 'Account Dynamic Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')
         ],
        string='Approval Level',
    )

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(comodel_name='account.approvals', string='Approval')


