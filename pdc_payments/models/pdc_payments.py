# -*- coding: utf-8 -*-

import datetime
from email.policy import default

from lxml import etree
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import float_compare


class PDCBank(models.Model):
    _name = 'pdc.commercial.bank'

    name = fields.Char('Name')


class PDCPayment(models.Model):
    _name = 'pdc.payment'
    _description = 'PDC Payment'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    payment_amount = fields.Float(string='Payment Amount', tracking=True)
    # cheque_ref = fields.Many2one('pdc.commercial.bank', string='Commercial Bank Name', tracking=True)
    commercial_bank_id = fields.Many2one('pdc.commercial.bank', string='Commercial Bank Name', tracking=True)
    memo = fields.Char(string='Memo', tracking=True)
    destination_account_id = fields.Many2one('account.account', string='Bank', tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    pdc_type = fields.Selection([('sent', 'Sent'),
                                 ('received', 'Received'),
                                 ], string='PDC Type', tracking=True)

    date_payment = fields.Date(string='Cheque Date', tracking=True)
    date_registered = fields.Date(string='Collection/Issue date', tracking=True)
    date_cleared = fields.Date(string='Cleared Date', tracking=True)
    date_bounced = fields.Date(string='Bounced Date', tracking=True)

    bounce_clear_btn_hide = fields.Boolean(string="Hide Button Bounce and Clear if cheque date is >= today date")

    state = fields.Selection([('draft', 'Draft'),
                              ('registered', 'Registered'),
                              ('bounced', 'Bounced'),
                              ('cleared', 'Cleared'),
                              ('cancel', 'Cancel'),
                              ], string='State', default='draft', tracking=True, readonly=True, index=True, copy=False)

    registered_counter = fields.Integer('Registered', compute='get_registered_jv_count')
    bounce_counter = fields.Integer('Bounce', compute='get_bounce_jv_count')
    cleared_counter = fields.Integer('Cleared', compute='get_cleared_jv_count')

    move_id = fields.Many2one('account.move', string='Invoice/Bill Ref')
    move_ids = fields.Many2many('account.move', string='Invoices/Bills Ref')
    cheque_no = fields.Char()
    cheque_type_id = fields.Many2one('cheque.type', string='Cheque Type')
    application_no = fields.Char('Application No')
    unit_id = fields.Many2many('product.product', string='Unit')
    floor_id = fields.Many2one('property.floor', string='Floor')
    building_id = fields.Many2one('property.building', string='Building')
    project_id = fields.Many2one('project.project', string='Project')
    order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')
    total_invoice = fields.Integer('Invoice', compute='get_invoice_count')
    is_security = fields.Boolean(string="Is Security ?", related="cheque_type_id.is_security")
    is_bounce_clear = fields.Boolean(compute="_compute_is_bounce_clear", default=False)
    is_recall = fields.Boolean(compute="_compute_is_bounce_clear", default=False)


    @api.depends("date_payment")
    def _compute_is_bounce_clear(self):
        for rec in self:
            if rec.date_payment:
                if rec.date_payment >= datetime.now().date():
                    rec.is_bounce_clear = True
                    rec.is_recall = False
                else:
                    rec.is_recall = True
                    rec.is_bounce_clear = False
            else:
                rec.is_bounce_clear = False
                rec.is_recall = False

    @api.onchange('cheque_no', 'date_payment', 'order_id', 'cheque_type_id')
    def _get_memo(self):
        for rec in self:
            if not rec.memo:
                if rec.cheque_no and rec.order_id.unit and rec.cheque_type_id and rec.date_payment:
                    rec.memo = "Chq No " + str(rec.cheque_no) + " DT " + str(rec.date_payment) + " For " + str(
                        rec.order_id.unit.name) + " against " + str(rec.cheque_type_id.description)
                else:
                    rec.memo = rec.memo

    def check_balance(self):
        partner_ledger = self.env['account.move.line'].search(
            [('partner_id', '=', self.partner_id.id),
             ('move_id.state', '=', 'posted'), ('full_reconcile_id', '=', False), ('balance', '!=', 0),
             ('account_id.reconcile', '=', True), ('full_reconcile_id', '=', False), '|',
             ('account_id.account_type', '=', 'liability_payable'),
             ('account_id.account_type', '=', 'asset_receivable')])
        bal = 0
        for par_rec in partner_ledger:
            bal = bal + (par_rec.debit - par_rec.credit)

    @api.model
    def create(self, vals):
        sequence = self.env.ref('pdc_payments.pdc_payment_seq')
        vals['name'] = sequence.next_by_id()
        rec = super(PDCPayment, self).create(vals)
        rec.button_register()
        return rec

    def action_registered_jv(self):
        lines = []
        unit_lst = []
        if self.unit_id:
            for unit in self.unit_id:
                unit_lst.append((4, [unit.id]))
        for record in self:
            if record.pdc_type == 'received':
                analytic_distribution = {}
                for rec in record.unit_id:
                    analytic_distribution.update({rec.units_analytic_account.id: 100})
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': record.date_registered,
                    'state': 'draft',
                    'pdc_registered_id': self.id,
                    'application_no': self.application_no,
                    # 'unit': self.unit_id.id,
                    # 'unit': unit_lst,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'credit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'account_id': record.partner_id.property_account_receivable_id.id,
                    'cheque_no': self.cheque_no,
                    'analytic_distribution': analytic_distribution,
                })
                lines.append(debit_line)
                credit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'credit': 0.0,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_receivable')),
                    'cheque_no': self.cheque_no,
                    'analytic_distribution': analytic_distribution,
                })
                lines.append(credit_line)
                move_dict['line_ids'] = lines
                move = self.env['account.move'].create(move_dict)
                # move.write({'unit': unit_lst,})
                if self.unit_id:
                    for unit in self.unit_id:
                        # unit_lst.append((4, [unit.id]))
                        # move.write({'unit':(4, unit.id)})
                        move.write({'unit': unit})
                move.action_post()
            else:
                analytic_distribution = {}
                for rec in record.unit_id:
                    analytic_distribution.update({rec.units_analytic_account.id: 100})
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': record.date_registered,
                    'state': 'draft',
                    'pdc_registered_id': self.id,
                    'application_no': self.application_no,
                    # 'unit': self.unit_id.id,
                    'unit': unit_lst,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'credit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_bnk_vendor')),
                    'cheque_no': self.cheque_no,
                    'analytic_distribution': analytic_distribution,
                })
                lines.append(debit_line)
                credit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'credit': 0.0,
                    'account_id':record.partner_id.property_account_payable_id.id,
                    'cheque_no': self.cheque_no,
                    'analytic_distribution': analytic_distribution,
                })
                lines.append(credit_line)
                move_dict['line_ids'] = lines
                move = self.env['account.move'].create(move_dict)
                # move.write({'unit': unit_lst, })
                if self.unit_id:
                    for unit in self.unit_id:
                        # unit_lst.append((4, [unit.id]))
                        # move.write({'unit':(4, unit.id)})
                        move.write({'unit': unit.id})
        # self.date_registered = datetime.today().date()

    def action_bounce_jv(self):
        lines = []
        for record in self:
            if record.pdc_type == 'received':
                if not record.date_bounced:
                    record.date_bounced = datetime.today().date()
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': record.date_bounced,
                    'state': 'draft',
                    'pdc_bounce_id': self.id,
                    'application_no': self.application_no,
                    'unit': self.unit_id.ids,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'credit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_receivable')),
                    'cheque_no': self.cheque_no
                })
                lines.append(debit_line)
                credit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'credit': 0.0,
                    'account_id': record.partner_id.property_account_receivable_id.id,
                    'cheque_no': self.cheque_no
                })
            else:
                if not record.date_bounced:
                    record.date_bounced = datetime.today().date()
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': record.date_bounced,
                    'state': 'draft',
                    'pdc_bounce_id': self.id,
                    'application_no': self.application_no,
                    'unit': self.unit_id.id,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'credit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'account_id': record.partner_id.property_account_payable_id.id,
                    'cheque_no': self.cheque_no
                })
                lines.append(debit_line)
                credit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'credit': 0.0,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_bnk_vendor')),
                    'cheque_no': self.cheque_no
                })
            lines.append(credit_line)
            move_dict['line_ids'] = lines
            move = self.env['account.move'].create(move_dict)
            move.action_post()

    def action_cleared_jv(self):
        lines = []
        for record in self:
            if record.pdc_type == 'received':
                if not record.date_cleared:
                    date_cleared = datetime.today().date()
                else:
                    date_cleared = record.date_cleared
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': date_cleared,
                    'state': 'draft',
                    'pdc_cleared_id': self.id,
                    'application_no': self.application_no,
                    'unit': self.unit_id.ids,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                # debit_line = (0, 0, {
                #     'name': 'PDC Cleared',
                #     'debit': record.payment_amount,
                #     'credit': 0.0,
                #     'partner_id': record.partner_id.id,
                #     'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_bnk_customer')),
                # })
                # lines.append(debit_line)
                credit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'partner_id': record.partner_id.id,
                    'credit': record.payment_amount,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_receivable')),
                    'cheque_no': self.cheque_no,
                })
                lines.append(credit_line)
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'credit': 0.0,
                    'partner_id': record.partner_id.id,
                    'account_id': record.destination_account_id.id,
                    'cheque_no': self.cheque_no,
                })
                lines.append(debit_line)
                # credit_line = (0, 0, {
                #     'name': 'PDC Cleared',
                #     'debit': 0.0,
                #     'partner_id': record.partner_id.id,
                #     'credit': record.payment_amount,
                #     'account_id': record.partner_id.property_account_receivable_id.id,
                # })
                # lines.append(credit_line)
                move_dict['line_ids'] = lines
                move = self.env['account.move'].create(move_dict)
                move.action_post()
            else:
                if not record.date_cleared:
                    record.date_cleared = datetime.today().date()
                move_dict = {
                    'ref': record.name,
                    'move_type': 'entry',
                    'journal_id': record.journal_id.id,
                    # 'partner_id': record.partner_id.id,
                    'date': record.date_cleared,
                    'state': 'draft',
                    'pdc_cleared_id': self.id,
                    'application_no': self.application_no,
                    'unit': self.unit_id.ids,
                    'floor': self.floor_id.id,
                    'building': self.building_id.id,
                    'project': self.project_id.id,
                    'cheque_no': self.cheque_no
                }
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': record.payment_amount,
                    'credit': 0.0,
                    'partner_id': record.partner_id.id,
                    'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_bnk_vendor')),
                    'cheque_no': self.cheque_no,
                })
                lines.append(debit_line)
                # credit_line = (0, 0, {
                #     'name': 'PDC Cleared',
                #     'debit': 0.0,
                #     'partner_id': record.partner_id.id,
                #     'credit': record.payment_amount,
                #     'account_id': int(self.env['ir.config_parameter'].get_param('pdc_payments.pdc_payable')),
                # })
                # lines.append(credit_line)
                debit_line = (0, 0, {
                    'name': record.memo,
                    'debit': 0.0,
                    'credit': record.payment_amount,
                    'partner_id': record.partner_id.id,
                    'account_id': record.destination_account_id.id,
                    'cheque_no': self.cheque_no,
                })
                lines.append(debit_line)
                # credit_line = (0, 0, {
                #     'name': 'PDC Cleared',
                #     'debit': record.payment_amount,
                #     'partner_id': record.partner_id.id,
                #     'credit': 0.0,
                #     'account_id': record.partner_id.property_account_payable_id.id,
                # })
                # lines.append(credit_line)
                move_dict['line_ids'] = lines
                move = self.env['account.move'].create(move_dict)
                move.action_post()
        # self.date_cleared = datetime.today().date()
        # self.date_cleared = False

    def button_register(self):
        self.action_registered_jv()
        self.write({
            'state': 'registered'
        })

    def button_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def button_bounce(self):
        # self.action_bounce_jv()
        # self.write({
        #     'state': 'bounced'
        # })
        cheque_ids = self.search([('partner_id.id', '=', self.partner_id.id), ('state', '=', 'bounced')])
        id_lst = []
        if cheque_ids:
            for rec in cheque_ids:
                id_lst.append((4, [rec.id]))
        return {
            'name': _('PDC Bounce'),
            'view_type': 'form',
            'res_model': 'pdc.bounce.wizard',
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_pdc_cheque_id': self.id,
                        'default_previous_cheque_ids': id_lst,
                        # 'default_penalty_amount':0.00,
                        'default_cheque_no': self.cheque_no}
        }

    def button_cleared(self):
        self.action_cleared_jv()
        if not self.date_cleared:
            date_cleared = datetime.today()
        else:
            date_cleared = self.date_cleared
        self.write({
            'date_cleared': date_cleared,
            'state': 'cleared'
        })

    def action_get_registered_jv(self):
        return {
            'name': _('PDC Payment'),
            'domain': [('pdc_registered_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_registered_jv_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('pdc_registered_id', '=', rec.id)])
            rec.registered_counter = count

    def action_get_invoices(self):
        return {
            'name': _('Invoices'),
            'domain': [('id', 'in', self.move_ids.ids)],
            'view_type': 'tree',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_invoice_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('id', 'in', self.move_ids.ids)])
            rec.total_invoice = count

    def action_get_bounce_jv(self):
        return {
            'name': _('PDC Payment'),
            'domain': [('pdc_bounce_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_bounce_jv_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('pdc_bounce_id', '=', rec.id)])
            rec.bounce_counter = count

    def action_get_cleared_jv(self):
        return {
            'name': _('PDC Payment'),
            'domain': [('pdc_cleared_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_cleared_jv_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('pdc_cleared_id', '=', rec.id)])
            rec.cleared_counter = count

    @api.onchange('journal_id')
    def _onchange_state(self):
        for rec in self:
            if rec.journal_id:
                rec.destination_account_id = rec.journal_id.default_account_id.id

    purchaser_id = fields.Many2one(comodel_name='res.partner', string='Payee Purchaser')

    def button_recall(self):
        return {
            'name': _('PDC Recall'),
            'view_type': 'form',
            'res_model': 'pdc.recall.wizard',
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_penalty_amount': 0.00,
                        'default_cheque_date': self.date_registered,
                        'default_pdc_cheque_id': self.id,
                        }
        }

    def _cron_hide_button_based_on_cheque_date(self):
        pdc_payments = self.search([('date_payment', '>=', datetime.today())])
        for pdc_payment in pdc_payments:
            pdc_payment.bounce_clear_btn_hide = True


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    pdc_ref = fields.Char(string='PDC Reference', tracking=True)
    # available_partner_bank_ids = fields.Many2many('res.bank')


class AccountEdiDocument(models.Model):
    _inherit = 'account.edi.document'

    def action_export_xml(self):
        pass


class AccountMove(models.Model):
    _inherit = 'account.move'

    pdc_registered_id = fields.Many2one('pdc.payment')
    pdc_bounce_id = fields.Many2one('pdc.payment')
    pdc_cleared_id = fields.Many2one('pdc.payment')
    application_no = fields.Char('Application No')
    pdc_recall_id = fields.Many2one('pdc.payment')

    pdc_count = fields.Integer(string="PDC", compute='_compute_pdc_count')
    is_pdc_created = fields.Boolean()
    cheque_no = fields.Char(string="Cheque No")

    def action_pdc_payment_wizard(self, amount=False):
        pdc_invoice_lst = []
        unit_lst = []
        if self.pdc_recall_id:
            for rec in self.pdc_recall_id.move_ids:
                pdc_invoice_lst.append((4, [rec.id]))
        if self.unit:
            for unit_id in self.unit:
                unit_lst.append((4, [unit_id.id]))
        if not self.pdc_recall_id:
            pdc_invoice_lst = self.ids
        total_payment_amount = 0.00
        if self.pdc_recall_id and amount:
            total_payment_amount = self.pdc_recall_id.payment_amount + amount
        if self.pdc_recall_id and not amount:
            total_payment_amount = self.pdc_recall_id.payment_amount
        if not self.pdc_recall_id:
            total_payment_amount = self.amount_total
        if self.pdc_bounce_id and amount:
            total_payment_amount = self.pdc_bounce_id.payment_amount + amount
        if not self.pdc_bounce_id:
            total_payment_amount = self.amount_total
        if self.pdc_bounce_id:
            journal_id = self.pdc_bounce_id.journal_id.id
            order_id = self.pdc_bounce_id.order_id.id
            destination_account_id = self.pdc_bounce_id.destination_account_id.id
            commercial_bank_id = self.pdc_bounce_id.commercial_bank_id.id
        if self.pdc_recall_id:
            journal_id = self.pdc_recall_id.journal_id.id
            order_id = self.pdc_recall_id.order_id.id
            destination_account_id = self.pdc_recall_id.destination_account_id.id
            commercial_bank_id = self.pdc_recall_id.commercial_bank_id.id
        else:
            commercial_bank_id = False
            destination_account_id = False
            journal_id = False
            order_id = self.so_ids.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'PDC Wizard',
            'view_id': self.env.ref('pdc_payments.view_pdc_payment_wizard_form', False).id,
            'target': 'new',
            'context': {'default_partner_id': self.partner_id.id,
                        'default_payment_amount': total_payment_amount,
                        'default_date_payment': self.invoice_date,
                        'default_currency_id': self.currency_id.id,
                        'default_move_id': self.ids,
                        'default_order_id': order_id,
                        'default_journal_id': journal_id,
                        'default_destination_account_id': destination_account_id,
                        'default_commercial_bank_id': commercial_bank_id,
                        # 'default_move_ids': [self.id],
                        'default_move_ids': pdc_invoice_lst,
                        # 'default_memo': self.name,
                        # 'default_unit_id': self.unit.id,
                        'default_unit_id': unit_lst,
                        'default_floor_id': self.floor.id,
                        'default_building_id': self.building.id,
                        'default_project_id': self.project.id,
                        'default_pdc_payment_id': self.pdc_recall_id.id,
                        'default_pdc_type': 'received' if self.move_type == 'out_invoice' else 'sent',
                        },
            'res_model': 'pdc.payment.wizard',
            'view_mode': 'form',
        }

    def action_combine_pdc_payment_wizard(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['account.move'].browse(selected_ids)
        # print(selected_records)
        if any(res.state != 'posted' for res in selected_records) or len(
                selected_records.mapped('partner_id')) > 1 or len(selected_records.mapped('journal_id')) > 1:
            raise ValidationError('Invoices must be in Posted state And Journal must be same. ')
        for res in selected_records:
            if res.is_pdc_created:
                raise UserError(_('PDC of invoice %s is already created.') % res.name)
        # if any(res.is_pdc_created):
        #     raise ValidationError('PDC of ')
        return {
            'type': 'ir.actions.act_window',
            'name': 'PDC Wizard',
            'view_id': self.env.ref('pdc_payments.view_pdc_payment_wizard_form', False).id,
            'target': 'new',
            'context': {'default_partner_id': selected_records[0].partner_id.id,
                        'default_payment_amount': sum(selected_records.mapped('amount_residual')),
                        # 'default_date_payment': self.invoice_date_due,
                        'default_currency_id': selected_records[0].currency_id.id,
                        'default_move_ids': selected_records.ids,
                        'default_pdc_type': 'received' if selected_records[0].move_type == 'out_invoice' else 'sent',
                        },
            'res_model': 'pdc.payment.wizard',
            'view_mode': 'form',
        }

    def action_show_pdc(self):
        return {
            'name': _('PDC Payments'),
            'view_mode': 'tree,form',
            'res_model': 'pdc.payment',
            'domain': [('move_ids', 'in', [self.id])],
            'context': {'default_partner_id': self.partner_id.id,
                        'default_payment_amount': self.amount_residual,
                        'default_date_payment': self.invoice_date_due,
                        'default_currency_id': self.currency_id.id,
                        'default_move_id': self.id,
                        'default_move_ids': [self.id],
                        # 'default_memo': self.name,
                        'default_unit_id': [(6, 0, self.unit.ids)],
                        'default_pdc_type': 'received' if self.move_type == 'out_invoice' else 'sent',
                        'create': False,
                        },
            'type': 'ir.actions.act_window',
        }

    def _compute_pdc_count(self):
        records = self.env['pdc.payment'].search_count([('move_ids', 'in', [self.id])])
        self.pdc_count = records

    # @api.onchange('so_ids')
    # def compute_invoice_units(self):
    #     unit_lst = []
    #     for rec in self:
    #         if rec.so_ids:
    #             for unit_id in rec.so_ids.unit:
    #                 unit_lst.append((4,[unit_id.id]))
    #         rec.write({'unit':unit_lst})


class ChequeType(models.Model):
    _name = 'cheque.type'

    name = fields.Char('Name')
    description = fields.Char(string="Description")
    is_security = fields.Boolean(string="Is Security ?")


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cheque_no = fields.Char('Cheque No')
