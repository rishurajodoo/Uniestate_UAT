import ast
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

PURCHASE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('pending_approval', "Pending Approval"),
    ('approved', "Approved"),
    ('purchase', "Purchase Order"),
    ('done', "Locked"),
    ('cancel', "Cancelled"),
]

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(
        selection=PURCHASE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    purchase_approval_id = fields.Many2one('purchase.approvals', compute='_get_purchase_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_purchase_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_purchase_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_purchase_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_purchase_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_purchase_approved_id = fields.Many2one('res.users', string='Level 1 Purchase Approved', copy=False)
    l2_purchase_approved_id = fields.Many2one('res.users', string='Level 2 Purchase Approved', copy=False)
    l3_purchase_approved_id = fields.Many2one('res.users', string='Level 3 Purchase Approved', copy=False)

    # show_first = fields.Boolean(compute='_get_show_buttons', store=True)
    # show_second = fields.Boolean(compute='_get_show_buttons', store=True)
    # show_third = fields.Boolean(compute='_get_show_buttons', store=True)

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)
    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    @api.depends('level_of_approval_needed', 'levels_approved', 'l1_purchase_approver_ids', 'l1_purchase_approved_id',
                 'l2_purchase_approver_ids', 'l2_purchase_approved_id', 'l3_purchase_approver_ids',
                 'l3_purchase_approved_id')
    def _get_show_buttons(self):
        for order in self:
            order.show_first = False
            order.show_second = False
            order.show_third = False
            if order.level_of_approval_needed != order.levels_approved:
                if order.l1_purchase_approver_ids and not order.l1_purchase_approved_id and self.env.user.id in order.l1_purchase_approver_ids.ids:
                    order.show_first = True
                if order.l1_purchase_approved_id and order.l2_purchase_approver_ids and not order.l2_purchase_approved_id and self.env.user.id in order.l2_purchase_approver_ids.ids:
                    order.show_second = True
                if order.l1_purchase_approved_id and order.l2_purchase_approved_id and order.l3_purchase_approver_ids and not order.l3_purchase_approved_id and self.env.user.id in order.l3_purchase_approver_ids.ids:
                    order.show_third = True

    # @api.depends('amount_total', 'purchase_approval_id.discount_approval')
    # def _get_show_buttons(self):
    #     for order in self:
    #         order.show_first = False
    #         order.show_second = False
    #         order.show_third = False
    #
    #         if order.purchase_approval_id and order.purchase_approval_id.discount_approval == 'amount base':
    #             # Logic for 'amount base' approval
    #             if order.amount_total >= order.purchase_approval_id.minimum_amount:
    #                 order.show_first = True
    #
    #         elif order.purchase_approval_id and order.purchase_approval_id.discount_approval == '%Base':
    #             # Logic for '%Base' approval
    #             if order.amount_total >= order.purchase_approval_id.minimum_amount:
    #                 order.show_first = True
    #             elif order.amount_total >= order.purchase_approval_id.minimum_amount_second:
    #                 order.show_second = True

    # Remove or correct the @depends decorator
    @api.depends('order_line')
    def _get_purchase_approval_id(self):
        for rec in self:
            rec.purchase_approval_id = False
            if rec.state != 'draft':
                max_value_amount_base = rec.amount_total
                max_value_approval_amount_base = rec.env['purchase.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc',
                    limit=1
                )

                # Compare and select the approval record with the higher minimum value
                if max_value_approval_amount_base:
                    for purchase_approval in max_value_approval_amount_base:
                        if purchase_approval.purchase_domain:
                            purchase_domain = ast.literal_eval(purchase_approval.purchase_domain)
                            purchase_domain += [('id', '=', self.id)]
                            purchase_records = self.search(purchase_domain)
                            if purchase_records:
                                rec.purchase_approval_id = purchase_approval.id
                                break
                            else:
                                rec.purchase_approval_id = False
                        else:
                            rec.purchase_approval_id = purchase_approval.id
                            break
                rec.level_of_approval_needed = len(
                    rec.purchase_approval_id.approval_level_ids) if rec.purchase_approval_id else 0
            else:
                rec.level_of_approval_needed = 0
                rec.purchase_approval_id = False

    @api.depends('order_line')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_purchase_approver_ids = False
            record.l2_purchase_approver_ids = False
            record.l3_purchase_approver_ids = False
            for level_id in record.purchase_approval_id.approval_level_ids:
                if level_id.name == 'level1':
                    if level_id.approver_ids:
                        record.l1_purchase_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_one = True
                if level_id.name == 'level2':
                    if level_id.approver_ids:
                        record.l2_purchase_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_two = True
                if level_id.name == 'level3':
                    if level_id.approver_ids:
                        record.l3_purchase_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_three = True

    def _get_all_level_approved(self):
        for rec in self:
            if rec.state == 'pending_approval':
                if rec.level_of_approval_needed == rec.levels_approved:
                    rec.all_level_approved = True
                else:
                    rec.all_level_approved = False
            else:
                rec.all_level_approved = False

    def button_confirm_action(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'approved']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    # @api.model
    # def create(self, vals):
    #     res = super(PurchaseOrder, self).create(vals)
    #
    #     # Check and create Level 1 activity if not created before
    #     if not res.activity_one:
    #         for user1 in res.l1_purchase_approver_ids:
    #             existing_activity = res.env['mail.activity'].search([
    #                 ('res_id', '=', res.id),
    #                 ('user_id', '=', user1.id),
    #                 ('note', '=', 'Level 1 Approval!!'),
    #                 ('state', 'in', ['pending', 'done']),
    #             ], limit=1)
    #
    #             if not existing_activity:
    #                 activity = res.env['mail.activity'].create({
    #                     'activity_type_id': res.env.ref(
    #                         'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('purchase.order').id,
    #                     'user_id': user1.id,
    #                     'note': 'Level 1 Approval!!'
    #                 })
    #                 res.activity_one = True
    #
    #     # Check and create Level 2 activity if not created before
    #     if not res.activity_two:
    #         for user2 in res.l2_purchase_approver_ids:
    #             existing_activity = res.env['mail.activity'].search([
    #                 ('res_id', '=', res.id),
    #                 ('user_id', '=', user2.id),
    #                 ('note', '=', 'Level 2 Approval!!'),
    #                 ('state', 'in', ['pending', 'done']),
    #             ], limit=1)
    #
    #             if not existing_activity:
    #                 activity = res.env['mail.activity'].create({
    #                     'activity_type_id': res.env.ref(
    #                         'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('purchase.order').id,
    #                     'user_id': user2.id,
    #                     'note': 'Level 2 Approval!!'
    #                 })
    #                 res.activity_two = True
    #
    #     # Check and create Level 3 activity if not created before
    #     if not res.activity_three:
    #         for user3 in res.l3_purchase_approver_ids:
    #             existing_activity = res.env['mail.activity'].search([
    #                 ('res_id', '=', res.id),
    #                 ('user_id', '=', user3.id),
    #                 ('note', '=', 'Level 3 Approval!!'),
    #                 ('state', 'in', ['pending', 'done']),
    #             ], limit=1)
    #
    #             if not existing_activity:
    #                 activity = res.env['mail.activity'].create({
    #                     'activity_type_id': res.env.ref(
    #                         'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('purchase.order').id,
    #                     'user_id': user3.id,
    #                     'note': 'Level 3 Approval!!'
    #                 })
    #                 res.activity_three = True
    #
    #     return res

    def check_and_approve(self):
        """This method checks the conditions and updates the state to 'approved' if needed."""
        for rec in self:
            if rec.state == 'pending_approval' and  rec.levels_approved != 0:
                if len(rec.purchase_approval_id.approval_level_ids.ids) == rec.levels_approved:
                    rec.write({'state': 'approved'})


    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        # Check and create Level 1 activity if not created before
        self.check_and_approve()
        if not self.activity_one:
            for user1 in self.l1_purchase_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('purchase.order').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_purchase_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('purchase.order').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_purchase_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref(
                            'purchase_approvels_dynamic.notification_discount_purchase_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('purchase.order').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    self.activity_three = True

        return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
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
                    'default_summary': 'Purchase Approval',
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
                    'default_summary': 'Purchase Approval',
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
                    'default_summary': 'Purchase Approval',
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

    def submit_for_purchase_approval(self):
        if not self.activity_one:
            for user1 in self.l1_purchase_approver_ids:
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
                        'activity_type_id': self.env.ref('sales_approvels_dynamic.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user1.id,
                        'summary': 'Sales Approval',
                        'note': user_note
                    })
                    self.activity_one = True

            # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_purchase_approver_ids:
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
                        'activity_type_id': self.env.ref('sales_approvels_dynamic.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user2.id,
                        'summary': 'Sales Approval',
                        'note': user_note
                    })
                    self.activity_two = True

            # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_purchase_approver_ids:
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
                        'activity_type_id': self.env.ref('sales_approvels_dynamic.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user3.id,
                        'summary': 'Sales Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        self.state = 'pending_approval'

class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    button_number = fields.Integer(default=0)

    def action_done(self):
        purchase_order = self.env['purchase.order'].search([('id', '=', self.res_id)])
        if self.button_number == 1:
            purchase_order.l1_purchase_approved_id = self.env.user.id
            purchase_order.levels_approved = purchase_order.levels_approved + 1
        if self.button_number == 2:
            purchase_order.l2_purchase_approved_id = self.env.user.id
            purchase_order.levels_approved = purchase_order.levels_approved + 1
        if self.button_number == 3:
            purchase_order.l3_purchase_approved_id = self.env.user.id
            purchase_order.levels_approved = purchase_order.levels_approved + 1
        res = super(MailActivityInherit, self).action_done()
        return res