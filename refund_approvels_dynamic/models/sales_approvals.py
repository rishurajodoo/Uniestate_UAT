import base64
import os
from odoo import models, fields, api, _


class RefundApprovals(models.Model):
    _name = 'refund.approvals'
    _description = 'Refund Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='Approval Name', required=True, tracking=True)
    refund_discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Refund Bill Approval',
        required=True,
        widget='radio'
    )
    refund_minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    refund_minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    refund_companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    refund_approval_level_ids = fields.One2many(
        comodel_name='refund.approvals.levels', inverse_name='refund_id',
        string='Approval Level Details', ondelete='cascade'
    )

class RefundApprovalsLevels(models.Model):
    _name = 'refund.approvals.levels'
    _description = 'Refund bill Approvals Levels'
    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')
         ],
        string='Approval Level',
    )

    refund_approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    refund_id = fields.Many2one(comodel_name='refund.approvals', string='Approval')

