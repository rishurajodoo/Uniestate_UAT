
import ast
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payslip_approval_id = fields.Many2one('hr.payslip.approvals', compute='_get_payslip_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_payslip_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_payslip_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_payslip_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_payslip_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_payslip_approved_id = fields.Many2one('res.users', string='Level 1 Payslip Approved', copy=False)
    l2_payslip_approved_id = fields.Many2one('res.users', string='Level 2 Payslip Approved', copy=False)
    l3_payslip_approved_id = fields.Many2one('res.users', string='Level 3 Payslip Approved', copy=False)

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)
    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', "Pending Approval"),
        ('approved', "Approved"),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancel', 'Rejected')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed then status is set to \'Done\'.
                    \n* When user cancel payslip the status is \'Rejected\'.""")
    sum_no_of_days = fields.Float(string='Attendance', compute='_compute_number_of_days')
    sum_no_of_hours = fields.Float(string='Overtime Hours', compute='_compute_number_of_hours')
    absent_day = fields.Float(string='Absent Day')
    basic_salary = fields.Float(string='Basic', compute='_compute_salary_rules')
    house_rent_allowance_salary = fields.Float(string='House Rent Allowance', compute='_compute_salary_rules')
    gross_payslip = fields.Float(string='Gross', compute='_compute_salary_rules')
    net_salary = fields.Float(string='Net Salary', compute='_compute_salary_rules')
    other_allowance = fields.Float(string='Other Allowance', compute='_compute_salary_rules')

    def _get_payslip_approval_id(self):
        for rec in self:
            rec.payslip_approval_id = False
            payslip_records = False
            if rec.state not in ('draft','verify','done','paid','cancel'):
                payslip_approval = rec.env['hr.payslip.approvals'].search([])
                print("payslip_approval",payslip_approval)
                # Compare and select the approval record with the higher minimum value
                if payslip_approval:
                    for line in payslip_approval:
                        if line.payroll_domain:
                            payslip_domain = ast.literal_eval(line.payroll_domain)
                            payslip_domain += [('id', '=', self.id)]
                            payslip_records = self.search(payslip_domain)
                        else:
                            payslip_records = line
                        if payslip_records:
                            rec.payslip_approval_id = line.id
                            break
                        else:
                            rec.payslip_approval_id = False
                rec.level_of_approval_needed = len(
                    rec.payslip_approval_id.approval_level_ids) if rec.payslip_approval_id else 0
            else:
                rec.level_of_approval_needed = 0
                rec.payslip_approval_id = False

    @api.depends('worked_days_line_ids')
    def _compute_number_of_days(self):
        for rec in self:
            if rec.worked_days_line_ids:
                rec.sum_no_of_days = sum(rec.worked_days_line_ids.mapped('number_of_days'))
            else:
                rec.sum_no_of_days = 0.0

    @api.depends('worked_days_line_ids')
    def _compute_number_of_hours(self):
        for rec in self:
            if rec.worked_days_line_ids:
                rec.sum_no_of_hours = sum(rec.worked_days_line_ids.mapped('number_of_hours'))
            else:
                rec.sum_no_of_hours = 0.0

    @api.depends('line_ids')
    def _compute_salary_rules(self):
        self.basic_salary = 0.0
        self.house_rent_allowance_salary = 0.0
        self.gross_payslip = 0.0
        self.net_salary = 0.0
        self.other_allowance = 0.0
        for rec in self:
            if rec.line_ids:
                rec.basic_salary = sum(rec.line_ids.filtered(lambda x: x.salary_rule_id.code == 'BASIC').mapped('amount'))
                rec.house_rent_allowance_salary = sum(rec.line_ids.filtered(lambda x: x.salary_rule_id.code == 'HRA').mapped('amount'))
                rec.gross_payslip = sum(rec.line_ids.filtered(lambda x: x.salary_rule_id.code == 'GROSS').mapped('amount'))
                rec.net_salary = sum(rec.line_ids.filtered(lambda x: x.salary_rule_id.code == 'NET').mapped('amount'))
                rec.other_allowance = sum(rec.line_ids.filtered(lambda x: x.salary_rule_id.code != 'HRA' and x.category_id.code == 'ALW').mapped('amount'))



    @api.depends('level_of_approval_needed', 'levels_approved', 'l1_payslip_approver_ids', 'l1_payslip_approved_id',
                 'l2_payslip_approver_ids', 'l2_payslip_approved_id', 'l3_payslip_approver_ids',
                 'l3_payslip_approved_id')
    def _get_show_buttons(self):
        for order in self:
            order.show_first = False
            order.show_second = False
            order.show_third = False
            if order.level_of_approval_needed != order.levels_approved:
                if order.l1_payslip_approver_ids and not order.l1_payslip_approved_id and self.env.user.id in order.l1_payslip_approver_ids.ids:
                    order.show_first = True
                if order.l1_payslip_approved_id and order.l2_payslip_approver_ids and not order.l2_payslip_approved_id and self.env.user.id in order.l2_payslip_approver_ids.ids:
                    order.show_second = True
                if order.l1_payslip_approved_id and order.l2_payslip_approved_id and order.l3_payslip_approver_ids and not order.l3_payslip_approved_id and self.env.user.id in order.l3_payslip_approver_ids.ids:
                    order.show_third = True

    def submit_for_approval(self):
        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_payslip_approver_ids:
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
                        'activity_type_id': self.env.ref('payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user1.id,
                        'summary': 'Payslip Approval',
                        'note': user_note
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_payslip_approver_ids:
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
                        'activity_type_id': self.env.ref('payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user2.id,
                        'summary': 'Payslip Approval',
                        'note': user_note
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_payslip_approver_ids:
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
                        'activity_type_id': self.env.ref('payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('sale.order').id,
                        'user_id': user3.id,
                        'summary': 'Payslip Approval',
                        'note': user_note
                    })
                    self.activity_three = True
        self.state = 'pending_approval'

    @api.model
    def _get_default_approval_id(self):
        approval = self.env['hr.payslip.approvals'].search([], limit=1)
        return approval.id if approval else False

    @api.model
    def _get_default_level_of_approval(self):
        approval = self.env['hr.payslip.approvals'].search([], limit=1)
        return len(approval.approval_level_ids) if approval else 0

    @api.depends('line_ids')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_payslip_approver_ids = False
            record.l2_payslip_approver_ids = False
            record.l3_payslip_approver_ids = False
            for level_id in record.payslip_approval_id.approval_level_ids:
                if level_id.name == 'level1':
                    if level_id.approver_ids:
                        record.l1_payslip_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_one = True
                if level_id.name == 'level2':
                    if level_id.approver_ids:
                        record.l2_payslip_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_two = True
                if level_id.name == 'level3':
                    if level_id.approver_ids:
                        record.l3_payslip_approver_ids = [(4, id) for id in level_id.approver_ids.ids]
                        record.is_level_three = True

    # @api.depends('line_ids')
    # def _compute_approver_ids(self):
    #     for record in self:
    #         record.l1_payslip_approver_ids = [(6, 0, record.payslip_approval_id.approval_level_ids.filtered(lambda level: level.name == 'level1').approver_ids.ids)]
    #         record.l2_payslip_approver_ids = [(6, 0, record.payslip_approval_id.approval_level_ids.filtered(lambda level: level.name == 'level2').approver_ids.ids)]
    #         record.l3_payslip_approver_ids = [(6, 0, record.payslip_approval_id.approval_level_ids.filtered(lambda level: level.name == 'level3').approver_ids.ids)]
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

    # def action_payslip_done(self):
    #     res = super(HrPayslip, self).action_payslip_done()
    #     if self.level_of_approval_needed != self.levels_approved:
    #         raise ValidationError("Please complete the approvals before confirming the payslip!")
    #     return res

    # @api.model
    # def create(self, vals):
    #     res = super(HrPayslip, self).create(vals)
    #
    #     # Check and create Level 1 activity if not created before
    #     if not res.activity_one:
    #         for user1 in res.l1_payslip_approver_ids:
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
    #                         'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('hr.payslip').id,
    #                     'user_id': user1.id,
    #                     'note': 'Level 1 Approval!!'
    #                 })
    #                 res.activity_one = True
    #
    #     # Check and create Level 2 activity if not created before
    #     if not res.activity_two:
    #         for user2 in res.l2_payslip_approver_ids:
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
    #                         'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('hr.payslip').id,
    #                     'user_id': user2.id,
    #                     'note': 'Level 2 Approval!!'
    #                 })
    #                 res.activity_two = True
    #
    #     # Check and create Level 3 activity if not created before
    #     if not res.activity_three:
    #         for user3 in res.l3_payslip_approver_ids:
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
    #                         'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
    #                     'res_id': res.id,
    #                     'res_model_id': res.env['ir.model']._get('hr.payslip').id,
    #                     'user_id': user3.id,
    #                     'note': 'Level 3 Approval!!'
    #                 })
    #                 res.activity_three = True
    #
    #     return res

    def write(self, vals):
        res = super(HrPayslip, self).write(vals)

        # Check and create Level 1 activity if not created before
        for rec in self:
            print("helloooo")
            print(rec.activity_one, rec.activity_two, rec.activity_three)
            if not rec.activity_one:
                for user1 in rec.l1_payslip_approver_ids:
                    existing_activity = self.env['mail.activity'].search([
                        ('res_id', '=', rec.id),
                        ('user_id', '=', user1.id),
                        ('note', '=', 'Level 1 Approval!!'),
                        ('state', 'in', ['pending', 'done']),
                    ], limit=1)

                    if not existing_activity:
                        activity = self.env['mail.activity'].create({
                            'activity_type_id': self.env.ref(
                                'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                            'res_id': rec.id,
                            'res_model_id': self.env['ir.model']._get('hr.payslip').id,
                            'user_id': user1.id,
                            'note': 'Level 1 Approval!!'
                        })
                        rec.activity_one = True

            # Check and create Level 2 activity if not created before
            if not rec.activity_two:
                for user2 in rec.l2_payslip_approver_ids:
                    existing_activity = self.env['mail.activity'].search([
                        ('res_id', '=', rec.id),
                        ('user_id', '=', user2.id),
                        ('note', '=', 'Level 2 Approval!!'),
                        ('state', 'in', ['pending', 'done']),
                    ], limit=1)

                    if not existing_activity:
                        activity = self.env['mail.activity'].create({
                            'activity_type_id': rec.env.ref(
                                'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                            'res_id': self.id,
                            'res_model_id': self.env['ir.model']._get('hr.payslip').id,
                            'user_id': user2.id,
                            'note': 'Level 2 Approval!!'
                        })
                        rec.activity_two = True

            # Check and create Level 3 activity if not created before
            if not rec.activity_three:
                for user3 in rec.l3_payslip_approver_ids:
                    existing_activity = self.env['mail.activity'].search([
                        ('res_id', '=', rec.id),
                        ('user_id', '=', user3.id),
                        ('note', '=', 'Level 3 Approval!!'),
                        ('state', 'in', ['pending', 'done']),
                    ], limit=1)

                    if not existing_activity:
                        activity = self.env['mail.activity'].create({
                            'activity_type_id': self.env.ref(
                                'payrol_approvels_dynamic.notification_discount_payslip_approval').id,
                            'res_id': rec.id,
                            'res_model_id': self.env['ir.model']._get('hr.payslip').id,
                            'user_id': user3.id,
                            'note': 'Level 3 Approval!!'
                        })
                        rec.activity_three = True

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
                    'default_summary': 'Payslip Approval',
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
                    'default_summary': 'Payslip Approval',
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
                    'default_summary': 'Payslip Approval',
                    'default_note': 'This activity assigned to User: Admin, please press "Mark AS DONE" to approve.',
                },
                }

    def _complete_activity(self, activity_note):
        activities_to_complete = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('note', '=', activity_note),
            ('state', '=', 'pending'),
        ])
        for activity in activities_to_complete:
            activity.action_done()

    def action_approve(self):
        current_user_id = self.env.user
        if self.show_first == True:
            self.l1_payslip_approved_id = current_user_id.id
            self.levels_approved = self.levels_approved + 1
            self._complete_activity('Level 1 Approval!!')
        elif self.show_second == True:
            self.l2_payslip_approved_id = current_user_id.id
            self.levels_approved = self.levels_approved + 1
            self._complete_activity('Level 2 Approval!!')
        elif self.show_third == True:
            self.l3_payslip_approved_id = current_user_id.id
            self.levels_approved = self.levels_approved + 1
            self._complete_activity('Level 3 Approval!!')

    def action_hr_payroll_approve(self):
        current_user_id = self.env.user
        for rec in self:
            if rec.show_first == True:
                rec.l1_payslip_approved_id = current_user_id.id
                rec.levels_approved = rec.levels_approved + 1
                rec._complete_activity('Level 1 Approval!!')
            elif rec.show_second == True:
                rec.l2_payslip_approved_id = current_user_id.id
                rec.levels_approved = rec.levels_approved + 1
                rec._complete_activity('Level 2 Approval!!')
            elif rec.show_third == True:
                rec.l3_payslip_approved_id = current_user_id.id
                rec.levels_approved = rec.levels_approved + 1
                rec._complete_activity('Level 3 Approval!!')

    def action_refuse(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def _complete_activity(self, activity_note):
        activities_to_complete = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('note', '=', activity_note),
            ('state', '=', 'pending'),
        ])
        activities_to_complete.action_done()


class MailActivityInherit(models.Model):
    _inherit = 'mail.activity'

    button_number = fields.Integer(default=0)

    def action_done(self):
        payslip_order = self.env['hr.payslip'].search([('id', '=', self.res_id)])
        if self.button_number == 1:
            payslip_order.l1_payslip_approved_id = self.env.user.id
            payslip_order.levels_approved = payslip_order.levels_approved + 1
        if self.button_number == 2:
            payslip_order.l2_payslip_approved_id = self.env.user.id
            payslip_order.levels_approved = payslip_order.levels_approved + 1
        if self.button_number == 3:
            payslip_order.l3_payslip_approved_id = self.env.user.id
            payslip_order.levels_approved = payslip_order.levels_approved + 1
        res = super(MailActivityInherit, self).action_done()
        return res
