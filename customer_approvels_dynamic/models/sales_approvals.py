import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvoiceApprovals(models.Model):
    _name = 'invoice.approvals'
    _description = 'invoice Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='invoice Bill Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    approval_level_ids = fields.One2many(
        comodel_name='invoice.approvals.levels', inverse_name='approval_id',
        string='Approval Level Details', ondelete='cascade'
    )

class InvoiceApprovalsLevels(models.Model):
    _name = 'invoice.approvals.levels'
    _description = 'invoice bill Approvals Levels'
    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')
         ],
        string='Approval Level',
    )

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(comodel_name='invoice.approvals', string='Approval')

