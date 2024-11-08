from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_approval_id = fields.Many2one('invoice.approvals', compute='_get_invoice_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_invoice_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_invoice_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_invoice_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_invoice_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_invoice_approved_id = fields.Many2one('res.users', string='Level 1 Invoice Approved', copy=False)
    l2_invoice_approved_id = fields.Many2one('res.users', string='Level 2 Invoice Approved', copy=False)
    l3_invoice_approved_id = fields.Many2one('res.users', string='Level 3 Invoice Approved', copy=False)

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)
    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    def _get_show_buttons(self):
        for move in self:
            move.show_first = False
            move.show_second = False
            move.show_third = False
            if move.move_type == 'out_invoice' and move.level_of_approval_needed != move.levels_approved:
                if move.l1_invoice_approver_ids and not move.l1_invoice_approved_id and self.env.user.id in move.l1_invoice_approver_ids.ids:
                    move.show_first = True
                if move.l1_invoice_approved_id and move.l2_invoice_approver_ids and not move.l2_invoice_approved_id and self.env.user.id in move.l2_invoice_approver_ids.ids:
                    move.show_second = True
                if move.l1_invoice_approved_id and move.l2_invoice_approved_id and move.l3_invoice_approver_ids and not move.l3_invoice_approved_id and self.env.user.id in move.l3_invoice_approver_ids.ids:
                    move.show_third = True

    @api.depends('invoice_line_ids', 'move_type')
    def _get_invoice_approval_id(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.invoice_approval_id = False
                max_value_amount_base = rec.amount_total
                max_value_approval_amount_base = rec.env['invoice.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc',
                    limit=1
                )

                # Compare and select the approval record with the higher minimum value
                if max_value_approval_amount_base:
                    rec.invoice_approval_id = max_value_approval_amount_base

                rec.level_of_approval_needed = len(
                    rec.invoice_approval_id.approval_level_ids) if rec.invoice_approval_id else 0
            else:
                rec.invoice_approval_id = False
                rec.level_of_approval_needed = 0

    @api.depends('invoice_approval_id.approval_level_ids', 'move_type')
    def _compute_approver_ids(self):
        for record in self:
            if record.move_type == 'out_invoice':
                record.l1_invoice_approver_ids = False
                record.l2_invoice_approver_ids = False
                record.l3_invoice_approver_ids = False

                if record.invoice_approval_id:
                    for level_id in record.invoice_approval_id.approval_level_ids.filtered(
                            lambda l: l.name in ['level1', 'level2', 'level3']):
                        if level_id.name == 'level1':
                            record.l1_invoice_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                            record.is_level_one = True
                        elif level_id.name == 'level2':
                            record.l2_invoice_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                            record.is_level_two = True
                        elif level_id.name == 'level3':
                            record.l3_invoice_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                            record.is_level_three = True
            else:
                record.l1_invoice_approver_ids = False
                record.l2_invoice_approver_ids = False
                record.l3_invoice_approver_ids = False

    def _get_all_level_approved(self):
        for rec in self:
            if rec.level_of_approval_needed == rec.levels_approved:
                rec.all_level_approved = True
            else:
                rec.all_level_approved = False

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type == 'out_invoice' and self.level_of_approval_needed != self.levels_approved:
            raise ValidationError("Please complete the approvals before confirming the invoice!")
        return res

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)

        # Check move_type and create Level 1 activity if not created before
        if res.move_type == 'out_invoice' and not res.activity_one:
            for user1 in res.l1_invoice_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    res.activity_one = True

        # Check move_type and create Level 2 activity if not created before
        if res.move_type == 'out_invoice' and not res.activity_two:
            for user2 in res.l2_invoice_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    res.activity_two = True

        # Check move_type and create Level 3 activity if not created before
        if res.move_type == 'out_invoice' and not res.activity_three:
            for user3 in res.l3_invoice_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    res.activity_three = True

        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)

        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_invoice_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two and 'l2_invoice_approver_ids' in vals:
            for user2 in self.l2_invoice_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three and 'l3_invoice_approver_ids' in vals:
            for user3 in self.l3_invoice_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'customer_approvels_dynamic.notification_discount_xyz_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('account.move').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    self.activity_three = True

        return res

    def approve_first_discount(self):
        current_user_id = self.env.user
        self.l1_invoice_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        self._complete_activity('Level 1 Approval done!!')


    def approve_second_discount(self):
        current_user_id = self.env.user
        self.l2_invoice_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        self._complete_activity('Level 2 Approval done!!')


    def approve_third_discount(self):
        current_user_id = self.env.user
        self.l3_invoice_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        self._complete_activity('Level 3 Approval done!!')






    def _complete_activity(self, activity_note):
        activities_to_complete = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('note', '=', activity_note),
            ('state', '=', 'pending'),
        ])
        activities_to_complete.action_done()