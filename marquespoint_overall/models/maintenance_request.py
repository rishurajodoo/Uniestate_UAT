import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request',
    _description = "Maintenance Request is inherited"

    approve_by = fields.Many2one(comodel_name='res.users', string='Closed BY', copy=False, readonly = True,)
    # , readonly = True
    approve_stage = fields.Selection([
        ('sent', 'Sent for Approval'),
        ('approved', 'Closed'),
    ], string='Closed Stage', widget='badge', readonly = True, default='')
    approve_date = fields.Date(string="Closed On", readonly = True,)

    is_closed = fields.Boolean(string='Is Closed', default=False, compute='_check_is_closed')

    stage = fields.Selection(
        [('new_req', 'New Request'), ('in_progress', 'In Progress'), ('repaired', 'Repaired'), ('scrap', 'Scrap')],
        compute="compute_stage")

    @api.depends('stage_id')
    def compute_stage(self):
        for rec in self:
            if rec.stage_id.name == 'New Request':
                rec.stage = 'new_req'
            elif rec.stage_id.name == 'In Progress':
                rec.stage = 'in_progress'
            elif rec.stage_id.name == 'Repaired':
                rec.stage = 'repaired'
            elif rec.stage_id.name == 'Scrap':
                rec.stage = 'scrap'

    def action_manager_approval(self):
        if self.maintenance_team_id.manager_id:
            new_stage = self.env['maintenance.stage'].search([('name', '=', 'In Progress')], limit=1)
            if new_stage:
                self.write({'stage_id': new_stage.id})
                # self.state = 'draft'
            activity = self.env['mail.activity'].create({
                'activity_type_id': self.env.ref(
                    'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                'user_id': self.maintenance_team_id.manager_id.id,
                # 'activity_user_id': self.maintenance_team_id.manager_id.id,
                'note': 'Approval Request has been sent to the user : {}!!'.format(
                    self.maintenance_team_id.manager_id.name)
            })
            self.approve_stage = 'sent'
            return activity

    def action_customer_acceptance(self):
        if self.sale_order_id.partner_id:
            new_stage = self.env['maintenance.stage'].search([('name', '=', 'Repaired')], limit=1)
            if new_stage:
                self.write({'stage_id': new_stage.id})
            activity = self.env['mail.activity'].create({
                'activity_type_id': self.env.ref(
                    'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                'user_id': self.user_id.id,
                # 'activity_user_id': user_id.id,
                'note': 'Approval Request has been Approved by the Manager: {}!!'.format(
                    self.env.user.name)
            })
            self.approve_stage = 'approved'
            return activity

    @api.depends('approve_stage')
    def _check_is_closed(self):
        tenancy = self.tenancy_id
        if tenancy.show_refund_close_tab or tenancy.show_standard_close_tab:
            self.is_closed = True
        else:
            self.is_closed = False

    def action_sent_approve(self):
        for rec in self:
            if not rec.approve_stage:
                rec.approve_stage = 'sent'
                if rec.tenancy_id:
                    rec.tenancy_id.req_approve_stage = rec.approve_stage
                group_users = self.env['res.users'].search(
                    [('groups_id', 'in', self.env.ref('marquespoint_overall.group_differed_approval').id)])

                # Send notification to users in the group
                display_msg = "Mantinance Request approval has been sent. Please review and approve."
                for user in group_users:
                    post = self.env.user.partner_id.message_post(body=display_msg, message_type='notification',
                                                                 subtype_xmlid='mail.mt_comment',
                                                                 author_id=self.env.user.partner_id.id)

                    if post:
                        notification_ids = [(0, 0, {'res_partner_id': user.partner_id.id, 'mail_message_id': post.id})]
                        post.write({'notification_ids': notification_ids})
            elif rec.approve_stage == 'sent':
                raise ValidationError("Already Sent for Approval")
            else:
                raise ValidationError("Already Approved")


    def action_approve(self):
        # Check if the user is in the appropriate group
        if self.env.user.has_group('marquespoint_overall.group_differed_approval'):
            # ten_con = self.env['tenancy.contract'].search([('order_id', '=', self.order_id.id)])
            if self.approve_stage == 'approved':
                raise ValidationError("Mantinance Request Already Approved")
            elif self.approve_stage == 'sent':
                self.approve_stage = 'approved'
                self.approve_date = fields.Date.today()
                self.approve_by = self.env.user.id,
                if self.tenancy_id:
                    self.tenancy_id.req_approve_stage = self.approve_stage
                    self.tenancy_id.req_approve_by = self.approve_by
                    self.tenancy_id.req_approve_date = self.approve_date

                # if ten_con:
                #     ten_con.approve_stage = self.approve_stage
                #     ten_con.approve_by = self.approve_by
                #     ten_con.approve_date = self.approve_date
            else:
                self.approve_stage = self.approve_stage


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    manager_id = fields.Many2one('res.users', string="Manager")
