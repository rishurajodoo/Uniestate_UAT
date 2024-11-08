from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast

# class SaleOrderApprovalList(models.Model):
#     _name = 'sale.order.approval.list'
#
#     sale_approver_ids = fields.Many2many(comodel_name='res.users', string="Approver Names")
#     approved_id = fields.Many2one('res.users', string="Approved Person")
#     status = fields.Selection(
#         [('pending', 'Pending'),
#          ('done', 'Done'),
#          ],
#         string='Approval Level',
#     )
#     order_id = fields.Many2one('sale.order', string="Sale Order")

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('pending_approval', "Pending Approval"),
    ('approved', "Approved"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    # state = fields.Selection(selection_add=[('pending_approval', "Pending Approval"), ('approved', "Approved")])

    sale_approval_id = fields.Many2one('sales.approvals', compute='_get_sale_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_sale_approval_id')
    levels_approved = fields.Integer(defaut=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    # approved_page_id = fields.One2many('sale.order.approval.list', 'order_id', string="Approver Status")

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
        # new_wizard = self.env['mail.activity'].create({})
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

    # def _get_approved_page_id(self):
    #     for rec in self:

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

    @api.depends('order_line')
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

    # @api.depends('order_line', 'sale_approval_id.discount_approval')
    # def _get_sale_approval_id(self):
    #     for rec in self:
    #         rec.sale_approval_id = False
    #         max_value_approval_amount_base = False
    #         max_value_approval_percent_base = False
    #
    #         if rec.order_line:
    #             # Calculate max value and corresponding approval record for 'amount base'
    #             max_value_amount_base = rec.amount_total
    #             max_value_approval_amount_base = rec.env['sales.approvals'].search(
    #                 [('minimum_amount', '<', max_value_amount_base)],
    #                 order='minimum_amount desc, sequence desc', limit=1)
    #
    #             # Calculate max value and corresponding approval record for '%Base'
    #             max_value_percent_base = max(rec.order_line.mapped('margin_percent'))  * 100
    #             max_value_approval_percent_base = rec.env['sales.approvals'].search(
    #                 [('minimum_percent', '>', max_value_percent_base)],
    #                 order='minimum_percent, sequence', limit=1)
    #
    #         # Compare and select the approval record with the higher minimum value
    #         if max_value_approval_amount_base and (not max_value_approval_percent_base or
    #                                                max_value_approval_amount_base.minimum_amount > max_value_approval_percent_base.minimum_percent):
    #             rec.sale_approval_id = max_value_approval_amount_base
    #         elif max_value_approval_percent_base:
    #             rec.sale_approval_id = max_value_approval_percent_base
    #
    #         rec.level_of_approval_needed = len(rec.sale_approval_id.sapproval_level_ids) if rec.sale_approval_id else 0

    def _get_sale_approval_id(self):
        for rec in self:
            max_discount = 0
            if rec.state not in ('draft','sent','booked','cancel','expired'):
                if rec.order_line and not rec.sale_approval_id:
                    max_discount_percent = rec.margin_percent * 100  # 80 %
                    max_discount_amount = rec.margin  # 1000 rupees
                    for line in rec.order_line:
                        max_discount = line.discount

                    a = rec.env['sales.approvals'].search([
                        ('minimum_percent', '>', max_discount_percent),
                        ('maximum_percent', '<', max_discount_percent),
                        ('minimum_percent', '!=', 0),
                        ('maximum_percent', '!=', 0)])

                    b = rec.env['sales.approvals'].search([
                        ('maximum_percent', '<', max_discount_percent),
                        ('minimum_percent', '=', 0),
                        ('maximum_percent', '!=', 0)
                    ])

                    c = rec.env['sales.approvals'].search([
                        ('minimum_percent', '>', max_discount_percent),
                        ('maximum_percent', '=', 0),
                        ('minimum_percent', '!=', 0)
                    ])

                    a_amt = rec.env['sales.approvals'].search([
                        ('minimum_amount', '>', max_discount_amount),
                        ('maximum_amount', '<', max_discount_amount),
                        ('minimum_amount', '!=', 0),
                        ('maximum_amount', '!=', 0)])

                    b_amt = rec.env['sales.approvals'].search([
                        ('maximum_amount', '<', max_discount_amount),
                        ('minimum_amount', '=', 0),
                        ('maximum_amount', '!=', 0)
                    ])

                    c_amt = rec.env['sales.approvals'].search([
                        ('minimum_amount', '>', max_discount_amount),
                        ('maximum_amount', '=', 0),
                        ('minimum_amount', '!=', 0)
                    ])

                    a_disc = rec.env['sales.approvals'].search([
                        ('minimum_discount', '>', max_discount),
                        ('maximum_discount', '<', max_discount),
                        ('minimum_discount', '!=', 0),
                        ('maximum_discount', '!=', 0)])

                    b_disc = rec.env['sales.approvals'].search([
                        ('maximum_discount', '<', max_discount),
                        ('minimum_discount', '=', 0),
                        ('maximum_discount', '!=', 0)
                    ])

                    c_disc = rec.env['sales.approvals'].search([
                        ('minimum_discount', '>', max_discount),
                        ('maximum_discount', '=', 0),
                        ('minimum_discount', '!=', 0)
                    ])

                    approvals = a | b | c | a_amt | b_amt | c_amt | a_disc | b_disc | c_disc

                    # approval = approvals and approvals[0] or False
                    approval = rec.env['sales.approvals'].search(
                        [('id', 'in', approvals.ids)],
                        order='sequence asc')


                    print("aproval", approval)
                    if approval:
                        for sale_approval in approval:
                            sale_domain = ast.literal_eval(sale_approval.sale_domain)
                            sale_domain += [('id', '=', self.id)]
                            sale_records = self.search(sale_domain)
                            if sale_records:
                                rec.sale_approval_id = sale_approval.id
                                break
                            else:
                                rec.sale_approval_id = False
                        print("rec.sale_approval_id", rec.sale_approval_id)
                        rec.level_of_approval_needed = len(rec.sale_approval_id.sapproval_level_ids)
                    else:
                        rec.sale_approval_id = False
                        rec.level_of_approval_needed = 0
                else:
                    rec.level_of_approval_needed = 0
                    rec.sale_approval_id = False
            else:
                rec.level_of_approval_needed = 0
                rec.sale_approval_id = False

    def _get_sale_approval_id11(self):
        for rec in self:
            rec.sale_approval_id = False
            rec.levels_approved = 0
            rec.level_of_approval_needed = 0
            if rec.order_line:
                max_discount = rec.margin_percent * 100
                if max_discount != 0:
                    if rec.env['sales.approvals'].search([('minimum_percent', '>', max_discount)]):
                        max_discount_amt_in_config = max(
                            rec.env['sales.approvals'].search([('minimum_percent', '>', max_discount)]).mapped(
                                'minimum_percent'))
                        rec.sale_approval_id = rec.env['sales.approvals'].search(
                            [('minimum_percent', '=', max_discount_amt_in_config)])
                        rec.level_of_approval_needed = len(self.sale_approval_id.sapproval_level_ids)
                    else:
                        rec.sale_approval_id = False
                        rec.levels_approved = 0
                        rec.level_of_approval_needed = 0
            else:
                rec.sale_approval_id = False
                rec.levels_approved = 0
                rec.level_of_approval_needed = 0

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

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.level_of_approval_needed != self.levels_approved:
            raise ValidationError("Please Complete the approvals !!!")
        elif self.for_rent and not self.rent_plan_ids:
            raise ValidationError("Before Approvals Or Confirmation To Add Tenancy Payment Plan")
        elif self.for_sale and not self.plan_ids:
            raise ValidationError("Before Approvals Or Confirmation To Add Payment Plan")
        return res

    # @api.model
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)

        # if self.level_of_approval_needed != self.levels_approved and self.level_of_approval_needed != 0:
        # if self.state == 'approved':
        #     raise ValidationError("Please Complete the approvals !!!")

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
                        'activity_type_id': self.env.ref('sales_approvels_dynamic.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user3.id,
                        'summary': 'Sales Approval',
                        'note': user_note
                    })
                    self.activity_three = True

        return res

    # def write(self, vals):
    #     res = super(SaleOrder, self).write(vals)
    #     if self.state == 'pending_approval':
    #         raise ValidationError("Please Complete the approvals !!!")
    #     return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        orders = self.filtered(lambda s: s.state in ['pending_approval', 'approved'])
        orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
            'levels_approved': 0,
            'is_level_one': False,
            'is_level_two': False,
            'is_level_three': False,
            'show_first': False,
            'show_second': False,
            'show_third': False,
            'all_level_approved': False,
            'activity_one': False,
            'activity_two': False,
            'activity_three': False,
        })
        self.sale_approval_id = False
        self.l1_sale_approved_id = False
        self.l2_sale_approved_id = False
        self.l3_sale_approved_id = False
        if self.activity_ids:
            self.activity_ids.unlink()

        return res

    def submit_for_approval(self):
        # Check and create Level 1 activity if not created before
        if self.for_rent and not self.rent_plan_ids:
            raise ValidationError("Before Approvals Or Confirmation To Add Tenancy Payment Plan")
        elif self.for_sale and not self.plan_ids:
            raise ValidationError("Before Approvals Or Confirmation To Add Payment Plan")
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
                        'activity_type_id': self.env.ref('sales_approvels_dynamic.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user3.id,
                        'summary': 'Sales Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        self.state = 'pending_approval'

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
                    'default_summary': 'Sales Approval',
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
                    'default_summary': 'Sales Approval',
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
                    'default_summary': 'Sales Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }


class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    button_number = fields.Integer(default=0)

    def action_done(self):
        sale_order = self.env['sale.order'].search([('id', '=', self.res_id)])
        if self.button_number == 1:
            sale_order.l1_sale_approved_id = self.env.user.id
            sale_order.levels_approved = sale_order.levels_approved + 1
        if self.button_number == 2:
            sale_order.l2_sale_approved_id = self.env.user.id
            sale_order.levels_approved = sale_order.levels_approved + 1
        if self.button_number == 3:
            sale_order.l3_sale_approved_id = self.env.user.id
            sale_order.levels_approved = sale_order.levels_approved + 1
        res = super(MailActivityInherit, self).action_done()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('discount')
    def _onchange_discount(self):
        sale_approver = self.env['sales.approvals'].search(
            [('minimum_discount', '>=', self.discount), ('maximum_discount', '<=', self.discount)],
            order='sequence asc', limit=1)
        # for approver in sale_approver:
        if self.discount:
            if sale_approver.discount_approval == 'discount':
                # print("sale_approver.minimum_discount", sale_approver.minimum_discount)
                # print("sale_approver.maximum_discount", sale_approver.maximum_discount)
                # if self.discount <= approver.minimum_discount and self.discount >= approver.maximum_discount:
                #     pass
                if not sale_approver:
                    raise ValidationError(
                        "Discount amount is mismatched based on approval configuration please check")
