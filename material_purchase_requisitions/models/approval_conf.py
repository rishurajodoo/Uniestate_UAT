from odoo import models, fields, api, _


####General Limit Approval Configuration####
class GeneralLimitApprovals(models.Model):
    _name = 'general.limit.approvals'
    _description = 'General Limit Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Sales Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")

    sapproval_level_ids = fields.One2many(comodel_name='general.limit.levels', inverse_name='approval_id', string='Approval Level Details')


class GeneralLimitLevels(models.Model):
    _name = 'general.limit.levels'
    _description = 'General Limit Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='general.limit.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )

############################################

####Special Limit Approval Configuration####
class SpecialLimitApprovals(models.Model):
    _name = 'special.limit.approvals'
    _description = 'Special Limit Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Sales Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")

    sapproval_level_ids = fields.One2many(comodel_name='special.limit.levels', inverse_name='approval_id', string='Approval Level Details')


class SpecialLimitLevels(models.Model):
    _name = 'special.limit.levels'
    _description = 'Special Limit Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='special.limit.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )

################################################

####Special Expense Approval Configuration####
class SpecialExpenseApprovals(models.Model):
    _name = 'special.expense.approvals'
    _description = 'Special Expense Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Sales Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")

    sapproval_level_ids = fields.One2many(comodel_name='special.expense.levels', inverse_name='approval_id', string='Approval Level Details')


class SpecialExpenseLevels(models.Model):
    _name = 'special.expense.levels'
    _description = 'Special Expense Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='special.expense.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )

#################################################
####General Expense Approval Configuration####
class GeneralExpenseApprovals(models.Model):
    _name = 'general.expense.approvals'
    _description = 'General Expense Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    discount_approval = fields.Selection(
        [('amount base', 'Total Base'), ('base', 'Margin %Base')],
        default='amount base',
        string='Sales Approval',
        required=True,
        widget='radio'
    )
    minimum_percent = fields.Float(string='Minimum%', digits=(6, 2), help="")
    minimum_amount = fields.Float(string='Minimum Amount', digits=(6, 2), help="")
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")

    sapproval_level_ids = fields.One2many(comodel_name='general.expense.levels', inverse_name='approval_id', string='Approval Level Details')


class GeneralExpenseLevels(models.Model):
    _name = 'general.expense.levels'
    _description = 'General Expense Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)

    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='general.expense.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )

########################################################
