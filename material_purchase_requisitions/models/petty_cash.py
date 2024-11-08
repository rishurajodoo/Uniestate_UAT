# -*- coding: utf-8 -*-
import math

from odoo import models, fields, api, _
from datetime import datetime, date
# from odoo.exceptions import Warning, UserError
from lxml import etree
from odoo.tools.float_utils import float_compare

from odoo.exceptions import UserError
import json


# from doc._extensions.pyjsparser.parser import true

class PettyCashModel(models.Model):
    _name = 'petty.cash'
    _description = 'Petty Cash'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']  # odoo11
    _order = 'id desc'

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )

    petty_cash_owner_id = fields.Many2one(
        'res.users',
        string='Petty Cash Owner',
        copy=False,
    )
    limit_type = fields.Selection([
        ('0', 'Special Limit'),
        ('1', 'General Limit'),
    ], 'Limit Type', default='0')
    limit_number = fields.Integer(string="Limit")
    period_start_date = fields.Date(
        string='Period Start Date',
        copy=True,
    )
    period_end_date = fields.Date(
        string='Period End Date',
        copy=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('paid', 'Paid')],
        default='draft',
        track_visibility='onchange',
    )

    petty_cash_journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        copy=False,
    )
    request_amount = fields.Integer(string="Request Amount")
    date = fields.Date(
        string='Date',
        copy=True,
    )

    payment_count = fields.Integer(string="Payment")
    is_payment_generated = fields.Boolean(default=False, copy=False)
    payment_id = fields.Many2one(
        'account.payment',
        string='Journal',
        copy=False,
    )
    payment_paid = fields.Boolean(compute='_is_payment_paid', default=False, copy=False)

    balance_limit = fields.Float(string="Balance", default=0, compute="_compute_balance_calculate", store=True)

    petty_cash_destination_journal_id = fields.Many2one(
        'account.journal',
        string='Destination Journal',
        copy=False,
    )
    payment_type = fields.Selection([
        ('0', 'Cash/Bank'),
        ('1', 'Cheque Payment'),
    ], 'Payment Type', default='0')
    pdc_payment_id = fields.Many2one('pdc.payment', string='PDC Payment')



    def limit_submit(self):
        # approval_conf = self.env['sales.approvals'].search([('name', '=', 'Test Approval')])
        # users = []
        # if approval_conf:
        #     for levels in approval_conf.sapproval_level_ids:
        #         users.append({levels.name: levels.approver_ids})
        self.state = 'submitted'
        self.state = 'to_approve'
        pass

    def limit_generate_payment(self):
        payment_obj = self.env['account.payment']
        payment_vals = {
                'payment_type': 'outbound',
                'partner_id': self.petty_cash_owner_id.partner_id[0].id,
                'amount': self.request_amount,
                'date': self.date,
                'is_internal_transfer': True,
                'journal_id': self.petty_cash_journal_id.id,
                'destination_journal_id': self.petty_cash_destination_journal_id.id,
            }
        payment_id = payment_obj.sudo().create(payment_vals)
        if payment_id:
                self.payment_count += 1
                self.is_payment_generated = True
                self.payment_id = payment_id
        if self.payment_type == '1':
            return {
                'type': 'ir.actions.act_window',
                'name': 'PDC Wizard',
                'view_id': self.env.ref('sale_customization.view_pdc_sale_wizard_form', False).id,
                'target': 'new',
                'context': {'default_partner_id': self.petty_cash_owner_id.partner_id.id,
                            'default_payment_amount': self.balance_limit,
                            # 'default_date_payment': self.invoice_date_due,
                            'default_date_payment': self.date,
                            'default_date_registered': self.date,
                            'default_currency_id': self.env.user.company_id.currency_id.id,
                            'default_journal_id': self.petty_cash_journal_id.id,
                            'default_move_ids': [payment_id.move_id.id],
                            # 'default_memo': self.name,
                            'default_pdc_type': 'sent',
                            },
                'res_model': 'pdc.sale.wizard',
                'view_mode': 'form',
            }

    def action_get_vehicle_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('id', 'in', [self.payment_id.id])],
            'context': "{'create': False}"
        }
        pass

    @api.depends('payment_id.state')
    def _is_payment_paid(self):
        if self.payment_id:
            if self.payment_id.state == 'posted':
                self.state = 'paid'
                self.payment_paid = True
            else:
                self.payment_paid = False
        else:
            self.payment_paid = False

    @api.depends('limit_type')
    def _compute_balance_calculate(self):
        total_balances = self.env['petty.cash.balances'].search(
            [('owner_id', '=', self.petty_cash_owner_id.id),
             ('limit_type', '=', self.limit_type)], limit=1)
        if total_balances:
            total_balances_amount = total_balances.balance_amount
            self.balance_limit = total_balances_amount
        else:
            self.balance_limit = 0.0

    # @api.model
    # def create(self, vals):
    #     name = self.env['ir.sequence'].next_by_code('assign.limit.seq')
    #     vals.update({
    #         'name': name
    #     })
    #     res = super(PettyCashModel, self).create(vals)
    #     return res

    # sale_approval_id = fields.Many2one('sales.approvals', compute='_get_sale_approval_id')
    general_limit_approval_id = fields.Many2one('general.limit.approvals', compute='_get_sale_approval_id')
    special_limit_approval_id = fields.Many2one('special.limit.approvals', compute='_get_sale_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_sale_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_sale_approved_id = fields.Many2one('res.users', string='Level 1 Approved', copy=False)
    l2_sale_approved_id = fields.Many2one('res.users', string='Level 2 Approved', copy=False)
    l3_sale_approved_id = fields.Many2one('res.users', string='Level 3 Approved', copy=False)

    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)

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

    # @api.depends('order_line')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_sale_approver_ids = False
            record.l2_sale_approver_ids = False
            record.l3_sale_approver_ids = False
            if self.limit_type == '0':
                for level_id in record.special_limit_approval_id.sapproval_level_ids:  # Corrected field name
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
            if self.limit_type == '1':
                for level_id in record.general_limit_approval_id.sapproval_level_ids:  # Corrected field name
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

    @api.depends('general_limit_approval_id.discount_approval', 'special_limit_approval_id.discount_approval')
    def _get_sale_approval_id(self):
        for rec in self:
            # rec.sale_approval_id = False
            rec.general_limit_approval_id = False
            rec.special_limit_approval_id = False
            max_value_approval_amount_base = False
            max_value_approval_percent_base = False

            # if rec.order_line:
            # Calculate max value and corresponding approval record for 'amount base'
            max_value_amount_base = rec.request_amount
            if self.limit_type == '1':
                max_value_approval_amount_base = rec.env['general.limit.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc', limit=1)
            if self.limit_type == '0':
                max_value_approval_amount_base = rec.env['special.limit.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc', limit=1)
            #
            #     # Calculate max value and corresponding approval record for '%Base'
            #     max_value_percent_base = max(rec.order_line.mapped('margin'))
            #     max_value_approval_percent_base = rec.env['sales.approvals'].search(
            #         [('minimum_percent', '>', max_value_percent_base)],
            #         order='minimum_percent, sequence', limit=1)
            #
            # # Compare and select the approval record with the higher minimum value
            if max_value_approval_amount_base:
                if self.limit_type == '1':
                    rec.general_limit_approval_id = max_value_approval_amount_base
                if self.limit_type == '0':
                    rec.special_limit_approval_id = max_value_approval_amount_base
            # if max_value_approval_percent_base:
            #     rec.sale_approval_id = max_value_approval_percent_base
            #
            # rec.level_of_approval_needed = len(rec.sale_approval_id.sapproval_level_ids) if rec.sale_approval_id else 0
            if self.limit_type == '1':
                rec.level_of_approval_needed = len(
                    rec.general_limit_approval_id.sapproval_level_ids) if rec.general_limit_approval_id else 0
            if self.limit_type == '0':
                rec.level_of_approval_needed = len(
                    rec.special_limit_approval_id.sapproval_level_ids) if rec.special_limit_approval_id else 0

    def _get_all_level_approved(self):
        for rec in self:
            if rec.level_of_approval_needed == rec.levels_approved:
                rec.all_level_approved = True
                self.state = 'approved'
            else:
                rec.all_level_approved = False

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('assign.limit.seq')
        vals.update({
            'name': name,
            'balance_limit': self.balance_limit
        })
        res = super(PettyCashModel, self).create(vals)

        current_user_balance = self.env['petty.cash.balances'].search([('owner_id', '=', res.petty_cash_owner_id.id),
                                                                               ('limit_type', '=', res.limit_type)])
        if not current_user_balance:
            balance_obj = self.env['petty.cash.balances']
            balance_vals = {
                'owner_id': res.petty_cash_owner_id.id,
                'limit_type': res.limit_type,
                'balance_amount': res.request_amount,
            }
            payment_id = balance_obj.sudo().create(balance_vals)
            # if payment_id:
            #     self.payment_count += 1
            #     self.is_payment_generated = True
            #     self.payment_id = payment_id
            # pass

        # Check and create Level 1 activity if not created before
        if not res.activity_one:
            for user1 in res.l1_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    res.activity_one = True

        # Check and create Level 2 activity if not created before
        if not res.activity_two:
            for user2 in res.l2_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    res.activity_two = True

        # Check and create Level 3 activity if not created before
        if not res.activity_three:
            for user3 in res.l3_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    res.activity_three = True

        return res

    def write(self, vals):
        vals.update({
            'balance_limit': self.balance_limit
        })
        res = super(PettyCashModel, self).write(vals)

        current_user_balance = self.env['petty.cash.balances'].search(
            [('owner_id', '=', self.petty_cash_owner_id.id),
             ('limit_type', '=', self.limit_type)], limit=1)
        total_limit_records = self.env['petty.cash'].search(
            [('petty_cash_owner_id', '=', self.petty_cash_owner_id.id), ('limit_type', '=', self.limit_type), ('state', '=', 'paid')])
        total_request_amount = 0.0
        for rec in total_limit_records:
            total_request_amount += rec.request_amount
        if current_user_balance:
            if self.state == 'paid' and total_request_amount > current_user_balance.balance_amount:
                current_user_balance.balance_amount += self.request_amount

        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    self.activity_three = True

        return res

    def approve_first_discount(self):
        current_user_id = self.env.user
        self.l1_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

    def approve_second_discount(self):
        current_user_id = self.env.user
        self.l2_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

    def approve_third_discount(self):
        current_user_id = self.env.user
        self.l3_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

class PettyCashExpenseModel(models.Model):
    _name = 'petty.cash.expense'
    _description = 'Petty Cash Expense'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']  # odoo11
    _order = 'id desc'

    request_owner_id = fields.Many2one(
        'res.users',
        string='Request Owner',
        copy=False,
    )

    account_id = fields.Many2one(
        comodel_name='account.account',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Account'
    )

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Journal',
        domain="[('type', 'in', ['cash', 'bank'])]",
    )

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )

    limit_type = fields.Selection([
        ('0', 'Special Limit'),
        ('1', 'General Limit'),
    ], 'Limit Type', default='0')

    date = fields.Date(
        string='Date',
        copy=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('paid', 'Paid')],
        default='draft',
        track_visibility='onchange',
    )
    balance_amount = fields.Float(string="Balance", compute='_compute_balance_calculate', default=0.0, store=True)
    expense_amount = fields.Float(string="Expense Amount", compute='_get_total_expense_amount', default=0.0, store=True)
    remaining_amount = fields.Float(string="Remaining Amount", compute='_get_remaining_amount', default=0.0, store=True)

    petty_cash_expense_ids = fields.One2many(comodel_name='petty.expense.lines', inverse_name='petty_cash_expense_id',
                                             string='Petty cash Expense Lines')

    move_count = fields.Integer(string="Move Count", default=0, compute='_get_bill_count')
    is_move_generated = fields.Boolean(string="is move generated", default=False)
    payment_count = fields.Integer(string="Payment Count", default=0, compute='_get_payment_count')
    move_id = fields.Many2one(
        comodel_name='account.move',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Move ID'
    )

    payment_id = fields.Many2one(
        comodel_name='account.payment',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Payment ID'
    )
    payment_type = fields.Selection([
        ('0', 'Cash/Bank'),
        ('1', 'Cheque Payment'),
    ], 'Payment Type', default='0')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, store=True)
    pdc_payment_id = fields.Many2one('pdc.payment', string='PDC Payment')



    def _get_bill_count(self):
        if self.move_id:
            self.move_count = len(self.move_id.ids)
        else:
            self.move_count = 0

    def _get_payment_count(self):
        if self.payment_id:
            self.payment_count = len(self.payment_id.ids)
        else:
            self.payment_count = 0

    # @api.model
    # def create(self, vals):
    #     name = self.env['ir.sequence'].next_by_code('petty.expense.seq')
    #     vals.update({
    #         'name': name
    #     })
    #     res = super(PettyCashExpenseModel, self).create(vals)
    #     return res

    # def _get_journal_id(self):
    #     if self.request_owner_id.user_journal_id:
    #         self.journal_id = self.request_owner_id.user_journal_id
    #     else:
    #         self.journal_id = False

    def limit_submit(self):
        self.state = 'submitted'
        self.state = 'to_approve'
        pass

    def action_get_bill_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', [self.move_id.id])],
            'context': "{'create': False}"
        }

    def action_get_payment_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('id', 'in', [self.payment_id.id])],
            'context': "{'create': False}"
        }

    # def expense_generate_journal(self):
    #     print(self)
    #     # entry_obj = self.env['account.move']
    #     entry_vals = {
    #         'move_type': 'entry',
    #         'partner_id': self.request_owner_id.partner_id[0].id,
    #         'journal_id': self.journal_id.id,
    #         # 'amount': self.request_amount,
    #         'invoice_date': self.date}
    #     line_ids = []
    #     for line in self.petty_cash_expense_ids:
    #         debit = line.amount
    #         credit = self.expense_amount
    #         line_ids += [(0, 0, {
    #             'name': line.product.name or '/',
    #             'debit': debit,
    #             'account_id': line.account.id,
    #             'partner_id': self.request_owner_id.partner_id[0].id
    #         }), (0, 0, {
    #             'name': '/',
    #             'credit': credit,
    #             'account_id': line.account.id,
    #             'partner_id': self.request_owner_id.partner_id[0].id
    #         })]
    #     if line_ids:
    #         entry_vals.update({'line_ids': line_ids})
    #     move_id = self.env['account.move'].create(entry_vals)
    #     if move_id:
    #         self.move_count += 1
    #         self.is_move_generated = True
    #         self.move_id = move_id

    def expense_generate_bill(self):
        for rec in self:
            rec.state = 'paid'
            bill = {
                # 'petty_cash_id': rec.id,
                # 'ref': rec.ref,
                'partner_id': rec.request_owner_id.partner_id[0].id,
                'invoice_date': rec.date,
                'date': rec.date,
                'state': 'draft',
                'move_type': 'in_invoice',
                'petty_cash_expense_id': rec.id}
            invoice_line_ids = []
            for line in rec.petty_cash_expense_ids:
                invoice_line_ids += [(0, 0, {
                    'product_id': line.product.product_variant_id.id,
                    'name': line.name,
                    'price_unit': line.amount,
                    'quantity': 1.0,
                    'tax_ids': line.taxes.ids,
                    'account_id': line.account.id,
                    'analytic_distribution': line.analytic_distribution,
                })]
            if invoice_line_ids:
                bill.update({'invoice_line_ids': invoice_line_ids})
            record = self.env['account.move'].create(bill)
            rec.move_id = record.id
            record.action_post()
            if rec.move_id:
                rec.is_move_generated = True
                payment = {
                    'date': rec.date,
                    'amount': rec.move_id.amount_residual,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'ref': rec.move_id.name,
                    'journal_id': rec.journal_id.id,
                    # 'currency_id': 148,
                    'partner_id': rec.move_id.partner_id.id,
                    'partner_bank_id': False,
                    # 'destination_account_id': rec.account_id.id,
                    'state': 'draft',
                    # 'petty_cash_id': rec.id,
                }
                record = self.env['account.payment'].create(payment)
                if rec.payment_type == '0':
                    if record:
                        rec.payment_id = record.id
                        record.action_post()
                        rec.move_id.payment_id = record.id
                        rec.move_id.payment_state = 'in_payment'
                    if rec.payment_type == '1':
                        return {
                            'type': 'ir.actions.act_window',
                            'name': 'PDC Wizard',
                            'view_id': self.env.ref('sale_customization.view_pdc_sale_wizard_form', False).id,
                            'target': 'new',
                            'context': {'default_partner_id': self.request_owner_id.partner_id.id,
                                        'default_payment_amount': self.expense_amount,
                                        # 'default_date_payment': self.invoice_date_due,
                                        'default_date_payment': self.date,
                                        'default_date_registered': self.date,
                                        'default_currency_id': self.currency_id.id,
                                        'default_move_id': rec.move_id.id,
                                        # 'default_move_ids': [self.id],
                                        # 'default_memo': self.name,
                                        'default_pdc_type': 'sent',
                                        # 'default_unit_id': self.order_id.unit.id,
                                        # 'default_floor_id': self.order_id.floor.id,
                                        # 'default_building_id': self.order_id.building.id,
                                        # 'default_project_id': self.order_id.project.id,
                                        },
                            'res_model': 'pdc.sale.wizard',
                            'view_mode': 'form',
                        }

    @api.depends('petty_cash_expense_ids.amount')
    def _get_total_expense_amount(self):
        if self.petty_cash_expense_ids:
            total_amount = 0.0
            for rec in self.petty_cash_expense_ids:
                if rec.taxes:
                    tax = rec.amount * (rec.taxes.amount / 100)
                    total_amount += rec.amount + tax
                else:
                    total_amount += rec.amount
            if total_amount == 0.0 or total_amount >= self.expense_amount:
                self.expense_amount = total_amount
        else:
            self.expense_amount = 0.0
        pass

    @api.depends('petty_cash_expense_ids.amount', 'limit_type')
    def _compute_balance_calculate(self):
        total_balances = self.env['petty.cash.balances'].search(
            [('owner_id', '=', self.request_owner_id.id),
             ('limit_type', '=', self.limit_type)], limit=1)
        print("total_balances", total_balances)
        if total_balances:
            total_balances_amount = total_balances.balance_amount
            self.balance_amount = total_balances_amount
        else:
            self.balance_amount = 0.0

    @api.depends('expense_amount', 'state')
    def _get_remaining_amount(self):
        if self.balance_amount and self.expense_amount:
            self.remaining_amount = self.balance_amount - self.expense_amount
            if self.remaining_amount:
                total_balances = self.env['petty.cash.balances'].search(
                    [('owner_id', '=', self.request_owner_id.id),
                     ('limit_type', '=', self.limit_type)], limit=1)
                if total_balances:
                    if self.state == 'approved':
                        if self.payment_type == '0':
                            if self.move_id.payment_state == 'paid':
                                total_balances.balance_amount += self.move_id.amount_total_signed
                        elif self.payment_type == '1':
                            if self.pdc_payment_id.state == 'registered':
                                total_balances.balance_amount += self.move_id.amount_total_signed
                            # total_amount = sum(self.filtered(lambda
                            #                                      x: x.request_owner_id == total_balances.owner_id.id and x.limit_type == self.limit_type).mapped(
                            #     'remaining_amount'))
                            # total_balances.balance_amount = total_amount
        else:
            self.remaining_amount = 0.0

    general_expense_approval_id = fields.Many2one('general.expense.approvals', compute='_get_sale_approval_id')
    special_expense_approval_id = fields.Many2one('special.expense.approvals', compute='_get_sale_approval_id')
    level_of_approval_needed = fields.Integer(compute='_get_sale_approval_id')
    levels_approved = fields.Integer(default=0, copy=False)
    all_level_approved = fields.Boolean(compute='_get_all_level_approved')

    l1_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l2_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')
    l3_sale_approver_ids = fields.Many2many(comodel_name='res.users', compute='_compute_approver_ids')

    l1_sale_approved_id = fields.Many2one('res.users', string='Level 1 Approved', copy=False)
    l2_sale_approved_id = fields.Many2one('res.users', string='Level 2 Approved', copy=False)
    l3_sale_approved_id = fields.Many2one('res.users', string='Level 3 Approved', copy=False)

    show_first = fields.Boolean(compute='_get_show_buttons')
    show_second = fields.Boolean(compute='_get_show_buttons')
    show_third = fields.Boolean(compute='_get_show_buttons')

    activity_one = fields.Boolean(default=False, copy=False)
    activity_two = fields.Boolean(default=False, copy=False)
    activity_three = fields.Boolean(default=False, copy=False)

    is_level_one = fields.Boolean(default=False, copy=False)
    is_level_two = fields.Boolean(default=False, copy=False)
    is_level_three = fields.Boolean(default=False, copy=False)

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

    # @api.depends('order_line')
    def _compute_approver_ids(self):
        for record in self:
            record.l1_sale_approver_ids = False
            record.l2_sale_approver_ids = False
            record.l3_sale_approver_ids = False
            if self.limit_type == '0':
                for level_id in record.special_expense_approval_id.sapproval_level_ids:  # Corrected field name
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
            if self.limit_type == '1':
                for level_id in record.general_expense_approval_id.sapproval_level_ids:  # Corrected field name
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

    @api.depends('general_expense_approval_id.discount_approval', 'special_expense_approval_id.discount_approval')
    def _get_sale_approval_id(self):
        for rec in self:
            # rec.sale_approval_id = False
            rec.general_expense_approval_id = False
            rec.special_expense_approval_id = False
            max_value_approval_amount_base = False
            max_value_approval_percent_base = False

            # if rec.order_line:
            # Calculate max value and corresponding approval record for 'amount base'
            max_value_amount_base = rec.expense_amount
            if self.limit_type == '1':
                max_value_approval_amount_base = rec.env['general.expense.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc', limit=1)
            if self.limit_type == '0':
                max_value_approval_amount_base = rec.env['special.expense.approvals'].search(
                    [('minimum_amount', '<', max_value_amount_base)],
                    order='minimum_amount desc, sequence desc', limit=1)
            #
            #     # Calculate max value and corresponding approval record for '%Base'
            #     max_value_percent_base = max(rec.order_line.mapped('margin'))
            #     max_value_approval_percent_base = rec.env['sales.approvals'].search(
            #         [('minimum_percent', '>', max_value_percent_base)],
            #         order='minimum_percent, sequence', limit=1)
            #
            # # Compare and select the approval record with the higher minimum value
            if max_value_approval_amount_base:
                if self.limit_type == '1':
                    rec.general_expense_approval_id = max_value_approval_amount_base
                if self.limit_type == '0':
                    rec.special_expense_approval_id = max_value_approval_amount_base
            # if max_value_approval_percent_base:
            #     rec.sale_approval_id = max_value_approval_percent_base
            #
            # rec.level_of_approval_needed = len(rec.sale_approval_id.sapproval_level_ids) if rec.sale_approval_id else 0
            if self.limit_type == '1':
                rec.level_of_approval_needed = len(
                    rec.general_expense_approval_id.sapproval_level_ids) if rec.general_expense_approval_id else 0
            if self.limit_type == '0':
                rec.level_of_approval_needed = len(
                    rec.special_expense_approval_id.sapproval_level_ids) if rec.special_expense_approval_id else 0

    def _get_all_level_approved(self):
        for rec in self:
            if rec.level_of_approval_needed == rec.levels_approved:
                rec.all_level_approved = True
                self.state = 'approved'
            else:
                rec.all_level_approved = False

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('petty.expense.seq')
        vals.update({
            'name': name
        })
        res = super(PettyCashExpenseModel, self).create(vals)

        # Check and create Level 1 activity if not created before
        if not res.activity_one:
            for user1 in res.l1_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    res.activity_one = True

        # Check and create Level 2 activity if not created before
        if not res.activity_two:
            for user2 in res.l2_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    res.activity_two = True

        # Check and create Level 3 activity if not created before
        if not res.activity_three:
            for user3 in res.l3_sale_approver_ids:
                existing_activity = res.env['mail.activity'].search([
                    ('res_id', '=', res.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = res.env['mail.activity'].create({
                        'activity_type_id': res.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': res.id,
                        'res_model_id': res.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    res.activity_three = True

        return res

    def write(self, vals):
        res = super(PettyCashExpenseModel, self).write(vals)

        # Check and create Level 1 activity if not created before
        if not self.activity_one:
            for user1 in self.l1_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user1.id),
                    ('note', '=', 'Level 1 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 1 activity for user:", user1.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user1.id,
                        'note': 'Level 1 Approval!!'
                    })
                    self.activity_one = True

        # Check and create Level 2 activity if not created before
        if not self.activity_two:
            for user2 in self.l2_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user2.id),
                    ('note', '=', 'Level 2 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 2 activity for user:", user2.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user2.id,
                        'note': 'Level 2 Approval!!'
                    })
                    self.activity_two = True

        # Check and create Level 3 activity if not created before
        if not self.activity_three:
            for user3 in self.l3_sale_approver_ids:
                existing_activity = self.env['mail.activity'].search([
                    ('res_id', '=', self.id),
                    ('user_id', '=', user3.id),
                    ('note', '=', 'Level 3 Approval!!'),
                    ('state', 'in', ['pending', 'done']),
                ], limit=1)

                if not existing_activity:
                    print("Creating Level 3 activity for user:", user3.id)
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('material_purchase_requisitions.notification_discount_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model']._get('petty.cash.expense').id,
                        'user_id': user3.id,
                        'note': 'Level 3 Approval!!'
                    })
                    self.activity_three = True

        return res

    def approve_first_discount(self):
        current_user_id = self.env.user
        self.l1_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

    def approve_second_discount(self):
        current_user_id = self.env.user
        self.l2_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

    def approve_third_discount(self):
        current_user_id = self.env.user
        self.l3_sale_approved_id = current_user_id.id
        self.levels_approved = self.levels_approved + 1
        activity_id = False
        for rec in self.activity_ids:
            if rec.user_id == current_user_id:
                activity_id = rec.id
        return {'name': _("Schedule Activity"),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.activity',
                'view_id': self.env.ref('mail.mail_activity_view_form_popup').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': activity_id,
                }

class PettyCashExpenseLines(models.Model):
    _name = 'petty.expense.lines'
    _description = 'Petty Cash Expense Lines'
    _inherit = ['analytic.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char(string="Description")
    product = fields.Many2one(
        'product.template',
        string='Product',
        copy=False,
    )

    petty_cash_expense_id = fields.Many2one(
        comodel_name='petty.cash.expense',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Expense Lines'
    )
    account = fields.Many2one(
        comodel_name='account.account',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Account'
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.move.line',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Analytic Account'
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Company ID'
    )

    # analytic_account_json_id = fields.Char(string='Analytic Account')
    # analytic_account_ids = fields.Json(string='Analytic Account', related='analytic_account_id.analytic_distribution')

    ##################
    analytic_distribution_text = fields.Text(company_dependent=True)
    analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution", store=False, precompute=False)
    analytic_account_ids = fields.Many2many('account.analytic.account', compute="_compute_analytic_account_ids",
                                            copy=True)

    @api.depends_context('company')
    @api.depends('analytic_distribution_text')
    def _compute_analytic_distribution(self):
        for record in self:
            record.analytic_distribution = json.loads(record.analytic_distribution_text or '{}')

    def _inverse_analytic_distribution(self):
        for record in self:
            record.analytic_distribution_text = json.dumps(record.analytic_distribution)

    @api.depends('analytic_distribution')
    def _compute_analytic_account_ids(self):
        for record in self:
            record.analytic_account_ids = bool(record.analytic_distribution) and self.env[
                'account.analytic.account'].browse(
                list({int(account_id) for ids in record.analytic_distribution for account_id in ids.split(",")})
            ).exists()

    @api.onchange('product')
    def _onchange_analytic_distribution(self):
        for record in self:
            if record.product:
                record.analytic_distribution = record.env['account.analytic.distribution.model']._get_distribution({
                    "product_id": record.product.id,
                    "product_categ_id": record.product.categ_id.id,
                    "company_id": record.company_id.id,
                })

    @api.constrains('analytic_distribution')
    def _check_analytic(self):
        for record in self:
            record.with_context({'validate_analytic': True})._validate_distribution(**{
                'product': record.product.id,
                'company_id': record.company_id.id,
            })
    ##################

    taxes = fields.Many2one(
        comodel_name='account.tax',
        ondelete='cascade',  # Set ondelete to 'cascade' for automatic deletion of related records
        string='Taxes'
    )
    qty = fields.Integer(string="Qty")
    amount = fields.Float(string="Amount")

    @api.onchange('product')
    def _onchange_product(self):
        if self.product:
            self.name = self.product.name
            self.taxes = self.product.taxes_id.id
            self.amount = self.product.list_price
            print(self)

#############################################################

class PettyCashBalancesModel(models.Model):
    _name = 'petty.cash.balances'
    _description = 'Petty Cash Balances'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']  # odoo11
    _order = 'id desc'

    owner_id = fields.Many2one(
        'res.users',
        string='Petty Cash Owner',
        copy=False,
    )

    balance_amount = fields.Float(string='Balance',  store=True)

    limit_type = fields.Selection([
        ('0', 'Special Limit'),
        ('1', 'General Limit'),
    ], 'Limit Type', default='0')

    followup_line_ids = fields.One2many('account_followup.followup.line','petty_cash_balance_id',
        string="Follow-up Level", domain=[('is_pretty', '=', True)]
    )
    due_date = fields.Date(string='Due Date',compute='_compute_due_date')

    @api.depends('limit_type', 'owner_id')
    def _compute_due_date(self):
        today = datetime.today()
        for rec in self:
            petty_balance = self.env['petty.cash'].search(
                [('petty_cash_owner_id', '=', rec.owner_id.id),
                 ('limit_type', '=', rec.limit_type)], limit=1, order='id desc')
            rec.due_date = petty_balance.period_end_date
            if rec.due_date:
                today = fields.Date.today()
                # Both `due_date` and `today` are date objects, so subtraction works correctly
                days_left = (rec.due_date - today).days
                followup_level = self.env['account_followup.followup.line'].search([('delay', '<=', days_left)], limit=1)
                if followup_level:
                    rec.followup_line_ids = [(6,0,followup_level.ids)]


    def expense(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Petty Cash Expense',
            'view_mode': 'form',
            'res_model': 'petty.cash.expense',
            'context': "{'create': True}"
        }

    def limit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Petty Cash Limit',
            'view_mode': 'form',
            'res_model': 'petty.cash',
            'context': "{'create': True}"
        }

class UsersInherit(models.Model):
    _inherit = 'res.users'

    user_journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        copy=False,
        domain="[('type', 'in', ['cash', 'bank'])]"
    )

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    petty_cash_expense_id = fields.Many2one(
        'petty.cash.expense',
        string='Petty Cash Expense',
        copy=False
    )

class FollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    petty_cash_balance_id = fields.Many2one('petty.cash.balances', string='Petty Cash Balance')