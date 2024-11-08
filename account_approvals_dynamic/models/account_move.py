import ast
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

ACCOUNT_ORDER_STATE = [
    ('draft', "Draft"),
    ('pending_approval', "Pending Approval"),
    ('approved', "Approved"),
    ('posted', "Posted"),
    ('cancel', "Cancelled"),
]

class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection=ACCOUNT_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    account_approval_id = fields.Many2one('account.approvals', compute='_get_account_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_account_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_account_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_account_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_account_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_account_approved_id = fields.Many2one('res.users', string='Level 1 Account Approved', copy=False)
    l2_account_approved_id = fields.Many2one('res.users', string='Level 2 Account Approved', copy=False)
    l3_account_approved_id = fields.Many2one('res.users', string='Level 3 Account Approved', copy=False)

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)
    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    @api.depends('level_of_approval_needed', 'levels_approved', 'l1_account_approver_ids', 'l1_account_approved_id',
                 'l2_account_approver_ids', 'l2_account_approved_id', 'l3_account_approver_ids',
                 'l3_account_approved_id')
    def _get_show_buttons(self):
        for order in self:
            order.show_first = False
            order.show_second = False
            order.show_third = False
            if order.level_of_approval_needed != order.levels_approved:
                if order.l1_account_approver_ids and not order.l1_account_approved_id and self.env.user.id in order.l1_account_approver_ids.ids:
                    order.show_first = True
                if order.l1_account_approved_id and order.l2_account_approver_ids and not order.l2_account_approved_id and self.env.user.id in order.l2_account_approver_ids.ids:
                    order.show_second = True
                if order.l1_account_approved_id and order.l2_account_approved_id and order.l3_account_approver_ids and not order.l3_account_approved_id and self.env.user.id in order.l3_account_approver_ids.ids:
                    order.show_third = True


    # Remove or correct the @depends decorator
    @api.depends('line_ids')
    def _get_account_approval_id(self):
        for rec in self:
            rec.account_approval_id = False
            if rec.state != 'draft':
                account_approval = rec.env['account.approvals'].search([])
                account_domain = ast.literal_eval(account_approval.account_domain)
                account_domain += [('id', '=', self.id)]
                account_records = self.search(account_domain)
                if account_records:
                    rec.account_approval_id = account_approval.id
                else:
                    rec.account_approval_id = False
                # print("rec.account_approval_id.approval_level_ids", rec.account_approval_id.approval_level_ids)
                rec.level_of_approval_needed = len(
                    rec.account_approval_id.approval_level_ids) if rec.account_approval_id else 0

            else:
                rec.level_of_approval_needed = 0
                rec.account_approval_id = False

    @api.depends('line_ids')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_account_approver_ids = False
            record.l2_account_approver_ids = False
            record.l3_account_approver_ids = False
            for level_id in record.account_approval_id.approval_level_ids:
                if level_id.name == 'level1':
                    if level_id.approver_ids:
                        record.l1_account_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_one = True
                if level_id.name == 'level2':
                    if level_id.approver_ids:
                        record.l2_account_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_two = True
                if level_id.name == 'level3':
                    if level_id.approver_ids:
                        record.l3_account_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_three = True

    def _get_all_level_approved(self):
        for rec in self:
            if rec.state == 'pending_approval':
                if rec.level_of_approval_needed == rec.levels_approved:
                    rec.all_level_approved = True
                    rec.state = 'approved'
                else:
                    rec.all_level_approved = False
            else:
                rec.all_level_approved = False


    def write(self, vals):
        res = super(AccountMove, self).write(vals)

        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_account_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_account_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_account_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    self.activity_three = True

        return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.level_of_approval_needed != self.levels_approved:
            raise ValidationError("Please complete the approvals before confirming the order!")
        return res

    def approve_first_discount(self):
        current_user_id = self.env.user
        # self.l1_sale_approved_id = current_user_id.id
        # self.levels_approved = self.levels_approved + 1
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
                break
        if activity:
            activity.button_number = 1
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                'context': {
                    'default_summary': 'Account Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def approve_second_discount(self):
        current_user_id = self.env.user
        # self.l2_sale_approved_id = current_user_id.id
        # self.levels_approved = self.levels_approved + 1
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
                break
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
                    'default_summary': 'Account Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def approve_third_discount(self):
        current_user_id = self.env.user
        # self.l3_sale_approved_id = current_user_id.id
        # self.levels_approved = self.levels_approved + 1
        activity_id = False
        activity = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity = rec
                activity_id = rec.id
                break
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
                    'default_summary': 'Account Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def _complete_activity(self, activity_note):
        activities_to_complete = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('note', '=', activity_note),
            ('note', '=', activity_note),
            ('state', '=', 'pending'),
        ])
        activities_to_complete.action_done()

    def submit_for_account_approval(self):
        if not self.activity_one:
            for user1 in self.l1_account_approver_ids:
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
                        'activity_type_id': self.env.ref('account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'summary': 'Account Approval',
                        'note': user_note
                    })
                    self.activity_one = True

            # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_account_approver_ids:
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
                        'activity_type_id': self.env.ref('account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'summary': 'Account Approval',
                        'note': user_note
                    })
                    self.activity_two = True

            # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_account_approver_ids:
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
                        'activity_type_id': self.env.ref('account_approvals_dynamic.notification_invoice_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'summary': 'Account Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        self.state = 'pending_approval'



class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    button_number = fields.Integer(default=0)

    def action_done(self):
        account_move = self.env['account.move'].search([('id', '=', self.res_id)])
        if self.button_number == 1:
            account_move.l1_account_approved_id = self.env.user.id
            account_move.levels_approved = account_move.levels_approved + 1
        if self.button_number == 2:
            account_move.l2_account_approved_id = self.env.user.id
            account_move.levels_approved = account_move.levels_approved + 1
        if self.button_number == 3:
            account_move.l3_account_approved_id = self.env.user.id
            account_move.levels_approved = account_move.levels_approved + 1
        res = super(MailActivityInherit, self).action_done()
        return res
