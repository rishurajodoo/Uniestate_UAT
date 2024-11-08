import base64
import os
from odoo import models, fields, api, _


class VendorrApprovals(models.Model):
    _name = 'vendorr.approvals'
    _description = 'Vendor Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10)

    name = fields.Char(string='Approval Name', required=True, tracking=True)
    vendorr_discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Vendor Bill Approval',
        required=True,
        widget='radio'
    )
    vendorr_minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    vendorr_minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    vendorr_companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    vendorr_approval_level_ids = fields.One2many(
        comodel_name='vendorr.approvals.levels', inverse_name='vendorr_id',
        string='Approval Level Details', ondelete='cascade'
    )

class VendorrApprovalsLevels(models.Model):
    _name = 'vendorr.approvals.levels'
    _description = 'Credit Approvals Levels'
    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')
         ],
        string='Approval Level',
    )

    vendorr_approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    vendorr_id = fields.Many2one(comodel_name='vendorr.approvals', string='Approval')

