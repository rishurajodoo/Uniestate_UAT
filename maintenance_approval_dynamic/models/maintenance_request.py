import ast
import datetime
from odoo import models, fields, api, _


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    stage = fields.Selection(
        [('new_req', 'New Request'),('pending_approval', "Pending Approval"),('in_progress', 'In Progress'),('repaired', 'Repaired'), ('scrap', 'Scrap')],
        compute="compute_stage", default='new_req')

    @api.depends('stage_id')
    def compute_stage(self):
        for rec in self:
            if rec.stage_id.name == 'New Request':
                rec.stage = 'new_req'
            elif rec.stage_id.name == 'Pending Approval':
                rec.stage = 'pending_approval'
            elif rec.stage_id.name == 'In Progress':
                rec.stage = 'in_progress'
            elif rec.stage_id.name == 'Repaired':
                rec.stage = 'repaired'
            elif rec.stage_id.name == 'Scrap':
                rec.stage = 'scrap'

    def action_submit_manager_approval_ext(self):
        if self.maintenance_team_id.manager_id:
            new_stage = self.env['maintenance.stage'].search([('name', '=', 'Repaired')], limit=1)
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
            self.is_approve = True
            return activity

    sale_approval_id = fields.Many2one('maintenance.approvals', compute='_get_sale_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_sale_approval_id')
    levels_approved = fields.Integer(defaut=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l1_sale_approved_id = fields.Many2one('res.users', string='Level 1 Sale Approved', copy=False)
    l2_sale_approved_id = fields.Many2one('res.users', string='Level 2 Sale Approved', copy=False)
    l3_sale_approved_id = fields.Many2one('res.users', string='Level 3 Sale Approved', copy=False)

    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)

    pending_flag = fields.Integer(default=0)

    is_correct_user = fields.Boolean(default=False, compute='_get_correct_user')
    is_approve = fields.Boolean(defult=False, copy=False)
    approver_user_id = fields.Many2one('res.users', string='Approver User', compute='_get_current_user', store=True)
    team_manager_id = fields.Many2one(related='maintenance_team_id.manager_id', store=True)
    is_manager_approve = fields.Boolean(defult=False, copy=False)

    @api.depends('team_manager_id')
    def _get_current_user(self):
        for rec in self:
            rec.approver_user_id = self.env.uid

    def _get_correct_user(self):
        if self.l1_sale_approver_ids:
            for user1 in self.l1_sale_approver_ids.ids:
                if user1 == self.env.user.id:
                    self.is_correct_user = True
                else:
                    self.is_correct_user = False
        elif self.l2_sale_approver_ids:
            for user2 in self.l2_sale_approver_ids.ids:
                if user2 == self.env.user.id:
                    self.is_correct_user = True
                else:
                    self.is_correct_user = False
        elif self.l3_sale_approver_ids:
            for user3 in self.l3_sale_approver_ids.ids:
                if user3 == self.env.user.id:
                    self.is_correct_user = True
                else:
                    self.is_correct_user = False
        else:
            self.is_correct_user = False

    def change_request_view(self):
        change_request_id = self.env['mail.activity.type'].search([('name', '=', 'Change Request')], limit=1)
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_user_id': self.l1_sale_approver_ids.ids[0],
                    'default_activity_type_id': change_request_id.id,
                    'default_res_id': self.id,
                    'default_res_model_id': self.env['ir.model']._get('sale.order').id,
                },
                }

    def _get_show_buttons(self):
        for order in self:
            order.show_first = False
            order.show_second = False
            order.show_third = False
            if order.level_of_approval_needed != order.levels_approved:
                if order.l1_sale_approver_ids and not order.l1_sale_approved_id and self.env.user.id in order.l1_sale_approver_ids.ids:
                    order.show_first = True
                if order.l1_sale_approved_id and order.l2_sale_approver_ids and not order.l2_sale_approved_id and self.env.user.id in order.l2_sale_approver_ids.ids:
                    order.show_second = True
                if order.l1_sale_approved_id and order.l2_sale_approved_id and order.l3_sale_approver_ids and not order.l3_sale_approved_id and self.env.user.id in order.l3_sale_approver_ids.ids:
                    order.show_third = True

    @api.depends('maintenance_team_id')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_sale_approver_ids = False
            record.l2_sale_approver_ids = False
            record.l3_sale_approver_ids = False
            for level_id in record.sale_approval_id.sapproval_level_ids:  # Corrected field name
                if level_id.name == 'level1':
                    if level_id.approver_ids:
                        record.l1_sale_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_one = True
                if level_id.name == 'level2':
                    if level_id.approver_ids:
                        record.l2_sale_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_two = True
                if level_id.name == 'level3':
                    if level_id.approver_ids:
                        record.l3_sale_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_three = True

    def _get_sale_approval_id(self):
        for rec in self:
            if rec.stage_id.name != 'New Request':
                if not rec.sale_approval_id:
                    approvals = rec.env['maintenance.approvals'].search([
                        ('maintenance_team_id', '=', rec.maintenance_team_id.id),
                    ])

                    # approval = approvals and approvals[0] or False
                    approval = rec.env['maintenance.approvals'].search(
                        [('id', 'in', approvals.ids),('maintenance_domain', '!=', False)],
                        order='sequence asc', limit=1)

                    if approval:
                        for maintenance_approval in approval:
                            maintenance_domain = ast.literal_eval(maintenance_approval.maintenance_domain)
                            maintenance_domain += [('id', '=', self.id)]
                            maintenance_records = self.search(maintenance_domain)
                            if maintenance_records:
                                rec.sale_approval_id = maintenance_approval.id
                                break
                            else:
                                rec.sale_approval_id = False
                        rec.sale_approval_id = approval
                        rec.level_of_approval_needed = len(approval.sapproval_level_ids)
                    else:
                        rec.sale_approval_id = False
                        rec.level_of_approval_needed = 0
                else:
                    rec.level_of_approval_needed = 0
                    rec.sale_approval_id = False
            else:
                rec.level_of_approval_needed = 0
                rec.sale_approval_id = False

    def _get_all_level_approved(self):
        for rec in self:
            if rec.stage == 'pending_approval':
                if rec.level_of_approval_needed == rec.levels_approved:
                    rec.all_level_approved = True
                else:
                    rec.all_level_approved = False
            else:
                rec.all_level_approved = False

    @api.model_create_multi
    def create(self, vals_list):
        request = super(MaintenanceRequest, self).create(vals_list)
        request.stage_id.name = 'New Request'
        return request

    # @api.model
    def write(self, vals):
        res = super(MaintenanceRequest, self).write(vals)
        if not self.activity_one and self.stage != 'new_req':
            for user1 in self.l1_sale_approver_ids:
                user_note = f'This activity assigned to User: {user1.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user1.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_sale_approver_ids:
                user_note = f'This activity assigned to User: {user2.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user2.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_sale_approver_ids:
                user_note = f'This activity assigned to User: {user3.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user3.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        return res

    def submit_for_approval(self):
        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_sale_approver_ids:
                user_note = f'This activity assigned to User: {user1.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user1.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_sale_approver_ids:
                user_note = f'This activity assigned to User: {user2.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user2.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_sale_approver_ids:
                user_note = f'This activity assigned to User: {user3.name}, please press "Mark AS DONE" to approve.'
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', user_note),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('maintenance_approval_dynamic.notification_maintenance_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('maintenance.request').id,
                        'user_id': user3.id,
                        'summary': 'Maintenance Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        pending_stage = self.env['maintenance.stage'].search([('name', '=', 'Pending Approval')], limit=1)
        if pending_stage:
            if self.stage_id.id != pending_stage.id:
                self.write({'stage_id': pending_stage.id})
        else:
            new_approval = self.env['maintenance.stage'].create({
                'name': 'Pending Approval'
            })
            if new_approval:
                if self.stage_id.id != new_approval.id:
                    self.write({'stage_id': new_approval.id})


    def approve_first_discount(self):
        current_user_id = self.env.user
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
        if activity:
            activity.button_number = 1
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref(
                    'mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                'context': {
                    'default_summary': 'Maintenance Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def approve_second_discount(self):
        current_user_id = self.env.user
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
        if activity:
            activity.button_number = 2
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                'context': {
                    'default_summary': 'Maintenance Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def approve_third_discount(self):
        current_user_id = self.env.user
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
        if activity:
            activity.button_number = 3
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                'context': {
                    'default_summary': 'Sales Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def manager_approval(self):
        current_user_id = self.env.user
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
        if activity:
            activity.button_number = 4
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                'context': {
                    'default_summary': 'Maintenance Manager Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def action_move_to_repaired(self):
        new_stage = self.env['maintenance.stage'].search([('name', '=', 'Repaired')], limit=1)
        if new_stage:
            self.write({'stage_id': new_stage.id})


class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    button_number = fields.Integer(default=0)

    def action_done(self):
        maintenance_request = self.env['maintenance.request'].search([('id', '=', self.res_id)])
        if self.button_number == 1:
            maintenance_request.l1_sale_approved_id = self.env.user.id
            maintenance_request.levels_approved = maintenance_request.levels_approved + 1
        if self.button_number == 2:
            maintenance_request.l2_sale_approved_id = self.env.user.id
            maintenance_request.levels_approved = maintenance_request.levels_approved + 1
        if self.button_number == 3:
            maintenance_request.l3_sale_approved_id = self.env.user.id
            maintenance_request.levels_approved = maintenance_request.levels_approved + 1
        if self.button_number == 4:
            maintenance_request.approve_stage = 'approved'
            maintenance_request.approve_by = self.env.user.id
            maintenance_request.approve_date = fields.Datetime.today()
            maintenance_request.is_manager_approve = True
            if maintenance_request.tenancy_id:
                maintenance_request.tenancy_id.req_approve_stage = 'approved'
                maintenance_request.tenancy_id.req_approve_by = self.env.user.id
                maintenance_request.tenancy_id.req_approve_date = fields.Datetime.today()
        res = super(MailActivityInherit, self).action_done()
        return res
