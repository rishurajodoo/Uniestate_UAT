import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class AccountAssets(models.Model):
    _inherit = 'account.asset',
    _description = "Account Asset is inherited"
    approve_by = fields.Many2one(comodel_name='res.users', string='Approved BY', copy=False, readonly = True,)
    # , readonly = True
    approve_stage = fields.Selection([
        ('sent', 'Sent for Approval'),
        ('approved', 'Approved'),
    ], string='Approval Stage', widget='badge', readonly = True, default='')
    approve_date = fields.Date(string="Aprroval On", readonly = True,)

    def action_approve(self):
        # Check if the user is in the appropriate group
        if self.env.user.has_group('marquespoint_overall.group_differed_approval'):
            ten_con = self.env['tenancy.contract'].search([('order_id', '=', self.order_id.id)])
            if self.approve_stage == 'approved':
                raise ValidationError("Differed Already Approved")
            elif self.approve_stage == 'sent':
                self.approve_stage = 'approved'
                self.approve_date = fields.Date.today()
                self.approve_by = self.env.user.id,
                if ten_con:
                    ten_con.approve_stage = self.approve_stage
                    ten_con.approve_by = self.approve_by
                    ten_con.approve_date = self.approve_date
            else:
                self.approve_stage = self.approve_stage