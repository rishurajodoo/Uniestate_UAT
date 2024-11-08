from odoo import models, fields, api, _

class SalesApprovals(models.Model):
    _name = 'sales.approvals'
    _description = 'Sales Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base'), ('discount', 'Discount')],
        default='amount base',
        string='Sales Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Less Than%', digits=(6, 2), help="")
    maximum_percent = fields.Float(string='Greater Than%', digits=(6, 2), help="")

    minimum_amount = fields.Float(string='Lesser Than', digits=(6, 2), help="")
    maximum_amount = fields.Float(string='Greater Than', digits=(6, 2), help="")

    minimum_discount = fields.Float(string='Lesser Than', digits=(6, 2), help="")
    maximum_discount = fields.Float(string='Greater Than', digits=(6, 2), help="")

    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")

    sapproval_level_ids = fields.One2many(comodel_name='approvals.levels', inverse_name='approval_id', string='Approval Level Details')
    sale_domain = fields.Char("Sale domain")

class ApprovalsLevels(models.Model):
    _name = 'approvals.levels'
    _description = 'Sales Dynamic Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='sales.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )
