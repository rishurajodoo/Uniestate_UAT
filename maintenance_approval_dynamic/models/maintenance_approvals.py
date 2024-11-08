from odoo import models, fields, api, _


class MaintenanceApprovals(models.Model):
    _name = 'maintenance.approvals'
    _description = 'Maintenance Dynamic Approvals'
    _inherit = ['mail.thread']

    sequence = fields.Integer(string='Sequence', default=10, help="Priority of the discount")
    name = fields.Char(string='Approval Name', required=True, tracking=True)
    maintenance_team_id = fields.Many2one(comodel_name='maintenance.team', string='Maintenance Team')
    companies_ids = fields.Many2many(comodel_name='res.company', string="Allowed Companies")
    sapproval_level_ids = fields.One2many(comodel_name='maintenance.approvals.levels', inverse_name='approval_id', string='Approval Level Details')
    maintenance_domain = fields.Char("Purchase domain")


class MaintenanceApprovalsLevels(models.Model):
    _name = 'maintenance.approvals.levels'
    _description = 'Maintenance Dynamic Approvals Levels'

    name = fields.Selection(
        [('level1', 'Level 1'),
         ('level2', 'Level 2'),
         ('level3', 'Level 3')],
        string='Approval Level',
    )
    active = fields.Boolean(default=True)
    approver_ids = fields.Many2many(comodel_name='res.users', string="Approver")
    approval_id = fields.Many2one(
        comodel_name='maintenance.approvals',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Approval'
    )
