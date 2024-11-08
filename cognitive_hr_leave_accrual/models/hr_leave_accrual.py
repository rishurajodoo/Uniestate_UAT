from odoo import fields, models, api

from odoo.addons.resource.models.utils import HOURS_PER_DAY

class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    allocate_leaves = fields.Boolean(string="Allocate Leaves Automatically")
    accrual_plan_id = fields.Many2one('hr.leave.accrual.plan', string="Accrual Plan")

class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    number_of_days = fields.Float(
        'Number of Days', compute='_compute_from_holiday_status_id', store=False, readonly=False, tracking=True,
        default=1,
        help='Duration in days. Reference field to use when necessary.')


class HrContract(models.Model):
    _inherit = "hr.contract"

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        leave_types = self.env['hr.leave.type'].search([('allocate_leaves', '=', True)])
        for type in leave_types:
            allocation = self.env['hr.leave.allocation'].create({
                'employee_id': res.employee_id.id,  # Employee associated with the contract
                'allocation_type': 'accrual',
                'accrual_plan_id': type.accrual_plan_id.id,
                'holiday_status_id': type.id,
                'date_from': vals['date_start']
            })
        return res

    # allocation = self.env['hr.leave.allocation'].create({
    #     'employee_id': self.employee_emp_id,
    #     'allocation_type': 'accrual',
    #     'accrual_plan_id': self.accrual_plan.id,
    #     'holiday_status_id': self.leave_type.id,
    #     'date_from': date(2000, 1, 1),
    #     'number_of_days': 0,
    # })
    #
