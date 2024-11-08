from odoo import models, fields, api, _
from odoo.exceptions import ValidationError




class AccountMove(models.Model):
    _inherit = 'account.move'

    in_credit_approval_id = fields.Many2one('credit.approvals', compute='_compute_in_credit_approval_id')
    level_of_credit_approval_needed = fields.Integer(compute='_compute_in_credit_approval_id')
    credit_levels_approved = fields.Integer(default=0, copy=False)
    credit_all_level_approved = fields.Boolean(compute='_compute_all_credit_level_approved')

    l1_in_credit_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_credit_approver_ids')
    l2_in_credit_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_credit_approver_ids')
    l3_in_credit_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_credit_approver_ids')

    l1_in_credit_approved_id = fields.Many2one('res.users', string='Level 1 In Credit Approved', copy=False)
    l2_in_credit_approved_id = fields.Many2one('res.users', string='Level 2 In Credit Approved', copy=False)
    l3_in_credit_approved_id = fields.Many2one('res.users', string='Level 3 In Credit Approved', copy=False)

    credit_activity_one = fields.Boolean(default=False, copy=False)
    credit_activity_two = fields.Boolean(default=False, copy=False)
    credit_activity_three = fields.Boolean(default=False, copy=False)

    credit_is_level_one = fields.Boolean(default=False, copy=False)
    credit_is_level_two = fields.Boolean(default=False, copy=False)
    credit_is_level_three = fields.Boolean(default=False, copy=False)
    credit_show_first = fields.Boolean(compute='_compute_credit_show_buttons')
    credit_show_second = fields.Boolean(compute='_compute_credit_show_buttons')
    credit_show_third = fields.Boolean(compute='_compute_credit_show_buttons')

    @api.depends('invoice_line_ids', 'move_type')
    def _compute_in_credit_approval_id(self):
        for rec in self:
            if rec.move_type == 'out_refund':
                max_value_amount_base = rec.amount_total
                max_value_approval_amount_base = rec.env['credit.approvals'].search(
                    [('credit_minimum_amount', '<', max_value_amount_base)],
                    order='credit_minimum_amount desc, sequence desc',
                    limit=1
                )

                # Compare and select the approval record with the higher minimum value
                if max_value_approval_amount_base:
                    rec.in_credit_approval_id = max_value_approval_amount_base
                    rec.level_of_credit_approval_needed = len(rec.in_credit_approval_id.credit_approval_level_ids)
                else:
                    rec.in_credit_approval_id = False
                    rec.level_of_credit_approval_needed = 0
            else:
                rec.in_credit_approval_id = False
                rec.level_of_credit_approval_needed = 0


    @api.depends('credit_levels_approved', 'level_of_credit_approval_needed')
    def _compute_all_credit_level_approved(self):
        for rec in self:
            rec.credit_all_level_approved = rec.credit_levels_approved >= rec.level_of_credit_approval_needed

    @api.depends('in_credit_approval_id.credit_approval_level_ids', 'move_type')
    def _compute_credit_approver_ids(self):
        for record in self:
            if record.move_type == 'out_refund':
                record.l1_in_credit_approver_ids = False
                record.l2_in_credit_approver_ids = False
                record.l3_in_credit_approver_ids = False
                credit_is_level_one = False
                credit_is_level_two = False
                credit_is_level_three = False

                if record.in_credit_approval_id:
                    for level_id in record.in_credit_approval_id.credit_approval_level_ids.filtered(
                            lambda l: l.name in ['level1', 'level2', 'level3']):
                        if level_id.name == 'level1':
                            record.l1_in_credit_approver_ids = [(4, id) for id in level_id.credit_approver_ids.ids]
                            credit_is_level_one = True
                        elif level_id.name == 'level2':
                            record.l2_in_credit_approver_ids = [(4, id) for id in level_id.credit_approver_ids.ids]
                            credit_is_level_two = True
                        elif level_id.name == 'level3':
                            record.l3_in_credit_approver_ids = [(4, id) for id in level_id.credit_approver_ids.ids]
                            credit_is_level_three = True

                record.credit_is_level_one = credit_is_level_one
                record.credit_is_level_two = credit_is_level_two
                record.credit_is_level_three = credit_is_level_three
            else:
                record.l1_in_credit_approver_ids = False
                record.l2_in_credit_approver_ids = False
                record.l3_in_credit_approver_ids = False

    @api.depends('l1_in_credit_approver_ids', 'l2_in_credit_approver_ids', 'l3_in_credit_approver_ids', 'credit_levels_approved', 'level_of_credit_approval_needed')
    def _compute_credit_show_buttons(self):
        for rec in self:
            rec.credit_show_first = rec.credit_show_second = rec.credit_show_third = False
            if rec.move_type == 'out_refund' and rec.level_of_credit_approval_needed != rec.credit_levels_approved:
                if rec.l1_in_credit_approver_ids and not rec.l1_in_credit_approved_id and rec.env.user.id in rec.l1_in_credit_approver_ids.ids:
                    rec.credit_show_first = True
                if rec.l1_in_credit_approved_id and rec.l2_in_credit_approver_ids and not rec.l2_in_credit_approved_id and rec.env.user.id in rec.l2_in_credit_approver_ids.ids:
                    rec.credit_show_second = True
                if rec.l1_in_credit_approved_id and rec.l2_in_credit_approved_id and rec.l3_in_credit_approver_ids and not rec.l3_in_credit_approved_id and rec.env.user.id in rec.l3_in_credit_approver_ids.ids:
                    rec.credit_show_third = True

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type == 'out_refund' and self.level_of_credit_approval_needed != self.credit_levels_approved:
            raise ValidationError("Please complete the approvals before confirming the invoice!")
        return res

    # Additional methods for approval actions can be added here

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)

        # Check move_type and create Level 1 activity if not created before
        if res.move_type == 'out_refund' and not res.credit_activity_one:
            for user1 in res.l1_in_credit_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'note': 'Level 1 In Credit Approval!!'
                    })
                    res.credit_activity_one = True

        # Check move_type and create Level 2 activity if not created before
        if res.move_type == 'out_refund' and not res.credit_activity_two:
            for user2 in res.l2_in_credit_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'note': 'Level 2 In Credit Approval!!'
                    })
                    res.credit_activity_two = True

        # Check move_type and create Level 3 activity if not created before
        if res.move_type == 'out_refund' and not res.credit_activity_three:
            for user3 in res.l3_in_credit_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'note': 'Level 3 In Credit Approval!!'
                    })
                    res.credit_activity_three = True

        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)

        # Check and create Level 1 activity if not created before
        if not self.credit_activity_one:
            for user1 in self.l1_in_credit_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'note': 'Level 1 In Credit Approval!!'
                    })
                    self.credit_activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.credit_activity_two and 'l2_in_credit_approver_ids' in vals:
            for user2 in self.l2_in_credit_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'note': 'Level 2 In Credit Approval!!'
                    })
                    self.credit_activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.credit_activity_three and 'l3_in_credit_approver_ids' in vals:
            for user3 in self.l3_in_credit_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 In Credit Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'credit_approvels_dynamic.notification_discount_credit_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'note': 'Level 3 In Credit Approval!!'
                    })
                    self.credit_activity_three = True

        return res

    def _complete_activity(self, activity_note):
        activities_to_complete = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('note', '=', activity_note),
            ('state', '=', 'pending'),
        ])
        activities_to_complete.action_done()

    def credit_approve_first_discount(self):
        current_user_id = self.env.user
        self.l1_in_credit_approved_id = current_user_id.id
        self.credit_levels_approved = self.credit_levels_approved + 1
        self._complete_activity('Level 1 In Credit Approval!!')

    def credit_approve_second_discount(self):
        current_user_id = self.env.user
        self.l2_in_credit_approved_id = current_user_id.id
        self.credit_levels_approved = self.credit_levels_approved + 1
        self._complete_activity('Level 2 In Credit Approval!!')

    def credit_approve_third_discount(self):
        current_user_id = self.env.user
        self.l3_in_credit_approved_id = current_user_id.id
        self.credit_levels_approved = self.credit_levels_approved + 1
        self._complete_activity('Level 3 In Credit Approval!!')