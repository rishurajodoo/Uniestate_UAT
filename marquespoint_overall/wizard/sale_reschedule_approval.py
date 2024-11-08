from datetime import datetime

from odoo import models, fields, api, _


class SaleRescheduleApprovalLine(models.Model):
    _name = 'sales.reschedule.approval.line'

    approval_stages = fields.Selection(
        [("first", "First Level Approval"), ("second", "Second Level Approval"), ("third", "Third Level Approval")],
        string="Approval Stages"
    )
    user_ids = fields.Many2many('res.users', string="Users")
    approval_id = fields.Many2one('sales.reschedule.approval', string="Approval ID")


class SaleRescheduleApproval(models.Model):
    _name = 'sales.reschedule.approval'
    _description = 'Sale Reschedule Approval'
    _rec_name = 'title'

    user_id = fields.Many2one('res.users', string="Schedule Approval User", required=False)
    title = fields.Char(string="Title")
    line_ids = fields.One2many('sales.reschedule.approval.line', 'approval_id', string="Lines")


class RescheduleWizardData(models.Model):
    _name = 'reschedule.wizard.data'
    _description = 'Reschedule Wizard Data'
    _rec_name = 'milestone_id'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    installment_period = fields.Selection([
        ('month', 'Month'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('bi_annual', 'Bi-Annual'),
    ], string='Installment Period')
    installment_no = fields.Integer('Revised Installments No')
    order_id = fields.Many2one('sale.order', string="Order")
    installments_due = fields.Float('Installment Due')
    amounts_due = fields.Float('Amount Due')
    is_submitted = fields.Boolean(default=False)
    is_approved = fields.Boolean(default=False)

    approval_line_ids = fields.Many2many(
        'sales.reschedule.approval.line', compute='_compute_approval_lines', string="Approval Levels", readonly=True)

    required_approvals = fields.Integer(compute='_compute_total_approval_stages', string="Required Approvals")
    current_approvals = fields.Integer(string="Current Approvals", readonly=True)
    is_approval_button_visible = fields.Boolean(string="Is Approve button visible ?",compute='_compute_is_approval_button_visible')

    def _compute_total_approval_stages(self):
        """Compute the total number of approval stages based on the approval lines."""
        for record in self:
            record.required_approvals = len(record.approval_line_ids)  # Count the number of approval lines

    def _compute_is_approval_button_visible(self):
        """Compute the visibility of the approve button."""
        for record in self:
            # Check if current approvals are less than required approvals
            record.is_approval_button_visible = record.current_approvals < record.required_approvals

            # Check if any of the approval users are currently logged in
            logged_in_users = self.env['res.users'].search([('id', 'in', record.approval_line_ids.mapped('user_ids.id')),
                                                            ('active', '=', True)])
            record.is_approval_button_visible = record.is_approval_button_visible and bool(logged_in_users)

    def action_approve(self):
        """Increment the approval count when approved."""
        for record in self:
            if record.current_approvals < record.required_approvals:
                record.current_approvals += 1

                # Optionally, add logic here to notify users or perform actions related to the approval

                # Check if all approvals are completed
                if record.current_approvals == record.required_approvals:
                    # Logic for when all approvals are received
                    pass  # Replace with your logic, e.g., updating order status or notifying stakeholders

    def _compute_approval_lines(self):
        for record in self:
            if record.order_id:
                approval = self.env['sales.reschedule.approval'].search([],
                                                                        limit=1)
                if approval:
                    record.approval_line_ids = approval.line_ids
                else:
                    record.approval_line_ids = False
