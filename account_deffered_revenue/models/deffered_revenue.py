# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import _, api, exceptions, fields, models
from dateutil.relativedelta import relativedelta
# from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare
from odoo.exceptions import UserError, ValidationError
import json


class DefferedRevenue(models.Model):
    _name = "deffered.revenue"
    _description = "DefferedRevenue"

    name = fields.Char(string='Deferred Revenue name', store=True, required=True)
    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building')
    floor_id = fields.Many2one('property.floor', string='Floor')
    unit_id = fields.Many2many('product.product', string='Unit')
    order_id = fields.Many2one('sale.order', string='Order')
    original_value = fields.Monetary(string='Original Value')
    acquisition_date = fields.Date(string='Acquisition Date')
    value_residual = fields.Monetary(string='Residual Amount to Recognize', compute='_compute_value_residual')
    book_value = fields.Monetary(string='Deferred Revenue Amount', compute='_compute_book_value')
    method_number = fields.Integer(string='Number of Recognitions')
    currency_id = fields.Many2one('res.currency', string='Account Currency')
    method_period = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period',
                                     default='1')
    is_closed = fields.Boolean(string='Is Closed', default=False, compute='_check_is_closed')
    prorata = fields.Boolean(
        string='Prorata Temporis',
        readonly=True,
        states={'draft': [('readonly', False)], 'model': [('readonly', False)]},
    )
    first_depreciation_date = fields.Date(
        string='First Defer Date',
        store=True, readonly=False,
    )
    account_depreciation_id = fields.Many2one('account.account', string='Revenue Account', required=True)
    account_depreciation_expense_id = fields.Many2one(
        comodel_name='account.account', string='Deferred Revenue Account', required=True
    )
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    # account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True)
    already_depreciated_amount_import = fields.Monetary(string='Depreciated Amount', default=0.0)
    depreciation_number_import = fields.Integer(string='Existing Depreciations', default=0)
    first_depreciation_date_import = fields.Date(string='First Depreciation Date')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Running'), ('close', 'Closed')], 'Status', copy=False,
                             default='draft')
    depreciation_move_ids = fields.One2many('account.move', 'revenue_id', string='Depreciation Lines', readonly=True)
    is_differed = fields.Boolean(default=False)
    depreciation_entries_count = fields.Integer(compute='_compute_counts', string='# Posted Depreciation Entries')

    #############
    analytic_distribution_text = fields.Text(company_dependent=True)
    analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution", store=False, precompute=False,
                                        string='Analytic Distribution')
    analytic_account_ids = fields.Many2many('account.analytic.account', compute="_compute_analytic_account_ids",
                                            copy=True)
    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get("Percentage Analytic"),
    )
    invoice_ids = fields.Many2many('account.move', string="Invoices", compute='compute_invoices')

    @api.depends('order_id')
    def compute_invoices(self):
        for rec in self:
            invoice_ids = self.env['account.move'].search(
                [('so_ids', '=', rec.order_id.id), ('reference.is_invoice', '=', True)])
            rec.invoice_ids = invoice_ids.ids

    @api.depends(
        'original_value', 'already_depreciated_amount_import',
        'depreciation_move_ids.state',
        'depreciation_move_ids.differed_depreciation_value',
        'depreciation_move_ids.reversal_move_id'
    )
    def _compute_value_residual(self):
        for record in self:
            posted_depreciation_moves = record.depreciation_move_ids.filtered(lambda mv: mv.state == 'posted')
            last_posted_depreciation_move = posted_depreciation_moves[0] if posted_depreciation_moves else None
            if last_posted_depreciation_move:
                record.value_residual = last_posted_depreciation_move.differed_depreciated_value
            else:
                record.value_residual = 0.0

    @api.depends(
        'original_value', 'already_depreciated_amount_import',
        'depreciation_move_ids.state',
        'depreciation_move_ids.differed_remaining_value',
        'depreciation_move_ids.reversal_move_id'
    )
    def _compute_book_value(self):
        for record in self:
            posted_depreciation_moves = record.depreciation_move_ids.filtered(lambda mv: mv.state == 'posted')
            last_posted_depreciation_move = posted_depreciation_moves[0] if posted_depreciation_moves else None
            if last_posted_depreciation_move:
                record.book_value = last_posted_depreciation_move.differed_remaining_value
            else:
                record.book_value = 0.0

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

    # @api.constrains('analytic_distribution')
    # def _check_analytic(self):
    #     for record in self:
    #         record.with_context({'validate_analytic': True})._validate_distribution(**{
    #             'product': record.product.id,
    #             'company_id': record.company_id.id,
    #         })
    #
    # def _validate_distribution(self, **kwargs):
    #     if self.env.context.get('validate_analytic', False):
    #         mandatory_plans_ids = [plan['id'] for plan in self.env['account.analytic.plan'].sudo().with_company(self.company_id).get_relevant_plans(**kwargs) if plan['applicability'] == 'mandatory']
    #         if not mandatory_plans_ids:
    #             return
    #         decimal_precision = self.env['decimal.precision'].precision_get('Percentage Analytic')
    #         distribution_by_root_plan = {}
    #         for analytic_account_ids, percentage in (self.analytic_distribution or {}).items():
    #             for analytic_account in self.env['account.analytic.account'].browse(map(int, analytic_account_ids.split(","))).exists():
    #                 root_plan = analytic_account.root_plan_id
    #                 distribution_by_root_plan[root_plan.id] = distribution_by_root_plan.get(root_plan.id, 0) + percentage
    #
    #         for plan_id in mandatory_plans_ids:
    #             if float_compare(distribution_by_root_plan.get(plan_id, 0), 100, precision_digits=decimal_precision) != 0:
    #                 raise ValidationError(_("One or more lines require a 100% analytic distribution."))
    ###############

    @api.depends('state')
    def _check_is_closed(self):
        tenancy = self.env['tenancy.contract'].search([('order_id', '=', self.order_id.id)], limit=1)
        if tenancy.show_refund_close_tab:
            self.is_closed = True
        else:
            self.is_closed = False

    def close_and_credit_note(self):
        # tenancy_id = self.env['tenancy.contract'].search([('order_id', '=', self.order_id.id)], limit=1)
        pdc_id = self.env['pdc.payment'].search([('order_id', '=', self.order_id.id)])
        registered_pdc = []
        for pdc in pdc_id:
            if pdc.state == 'registered':
                registered_pdc.append(pdc)
        # period = 0.00
        # penalty = 0.00
        # ref_amount = 0.00
        if registered_pdc:
            raise ValidationError(_('There are PDC payments on registered'))
        move_ids = self.depreciation_move_ids.filtered(lambda l: l.state == 'draft')
        for move_id in move_ids:
            move_id.state = 'cancel'

        # if tenancy_id:
        #     period = tenancy_id.early_termination_period
        #     penalty = tenancy_id.early_termination_penalty_amount
        #     ref_amount = tenancy_id.refundable_amount
        # return {
        #     'name': _("Close and Credit Note"),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'deffered.revenue.credit.wizard',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {'default_sale_order_id': self.order_id.id,
        #                 'default_deffered_revenue_id': self.id,
        #                 'default_early_termination_period': period,
        #                 'default_early_termination_penalty_amount': penalty,
        #                 'default_refundable_amount': ref_amount}
        # }

    def compute_depreciation_board(self):
        depreciation_moves = []
        if not self.is_differed:
            for rec in self:
                if rec.method_number:
                    depreciation_interval = rec.original_value / rec.method_number
                    remaining_value = rec.original_value
                    recognition_date = rec.first_depreciation_date
                    for i in range(rec.method_number):
                        depreciation_value = min(remaining_value, depreciation_interval)
                        remaining_value -= depreciation_value
                        next_month_date = recognition_date + relativedelta(months=1)
                        next_recognition_date = next_month_date.replace(day=1) - timedelta(days=1)
                        if i == 0:
                            recognition_date = next_recognition_date = rec.first_depreciation_date
                        move_data = {
                            'ref': f"Test ({i + 1}/{rec.method_number})",
                            'name': '/',
                            'date': next_recognition_date,
                            'partner_id': rec.order_id.partner_id.id,
                            'differed_depreciation_value': depreciation_value,
                            'differed_depreciated_value': rec.original_value - remaining_value,
                            'differed_remaining_value': remaining_value,
                            'revenue_id': rec.id,
                            'journal_id': rec.journal_id.id,
                            'auto_post': 'at_date',
                            'project': rec.project_id.id,
                            'building': rec.building_id.id,
                            'unit': rec.unit_id.ids,
                            'floor': rec.floor_id.id
                        }
                        depreciation_moves.append((0, 0, move_data))
                        recognition_date = next_month_date
                        rec.is_differed = True
                else:
                    raise UserError(_("Number of Recognitions not zero"))
            # Create the depreciation moves
            self.depreciation_move_ids = depreciation_moves
            for move in self.depreciation_move_ids:
                move.write({
                    'line_ids': [(0, 0, {
                        'name': 'Test(Copy)',
                        'account_id': rec.account_depreciation_expense_id.id,
                        'debit': move.differed_depreciation_value,
                        'partner_id': move.partner_id.id,
                        'credit': 0.0,
                        # 'analytic_distribution': {rec.account_analytic_id.id: 100}
                        'analytic_distribution': rec.analytic_distribution
                    }), (0, 0, {
                        'name': 'Test(Copy)',
                        'account_id': rec.account_depreciation_id.id,
                        'credit': move.differed_depreciation_value,
                        'partner_id':  move.partner_id.id,
                        'debit': 0.0,
                        # 'analytic_distribution': {rec.account_analytic_id.id: 100}
                        'analytic_distribution': rec.analytic_distribution
                    })]
                })

    def open_entries(self):
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
            'views': [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.depreciation_move_ids.ids)],
            'context': dict(self._context, create=False),
        }

    @api.depends('depreciation_move_ids.state')
    def _compute_counts(self):
        depreciation_per_asset = {
            group.id: count
            for group, count in self.env['account.move']._read_group(
                domain=[
                    ('revenue_id', 'in', self.ids),
                    ('state', '=', 'posted'),
                ],
                groupby=['revenue_id'],
                aggregates=['__count'],
            )
        }
        for revenue in self:
            revenue.depreciation_entries_count = depreciation_per_asset.get(revenue.id, 0)

    def action_validate(self):
        if self.is_differed:
            for revenue in self:
                if sum(self.invoice_ids.mapped('amount_total_signed')) >= revenue.original_value:
                    # if revenue.order_id.invoice_status != 'invoiced':
                    #     raise UserError("Deferred Revenue is not confirm before Sales Order is invoiced")
                    revenue.depreciation_move_ids.filtered(lambda move: move.state != 'posted')._post()

                    revenue.state = 'open'
                    # revenue.depreciation_move_ids.filtered(lambda move: move.state == 'draft')
                    # revenue.state = 'close'
                else:
                    raise ValidationError(
                        "You are not able to confirm the revenue due to original amount is less then invoice total amount")

    def action_close(self):
        for move in self.depreciation_move_ids:
            if move.state == 'draft':
                move.state = 'cancel'
        if self.order_id:
            if self.order_id.tenancy:
                self.order_id.tenancy.approve_stage = 'approved'
                self.order_id.tenancy.approve_by = self.env.user.id
                self.order_id.tenancy.approve_date = fields.Date.today()

class AccountMove(models.Model):
    _inherit = 'account.move'

    revenue_id = fields.Many2one('deffered.revenue')
    differed_remaining_value = fields.Monetary(string='Depreciable Value')
    differed_depreciated_value = fields.Monetary(string='Cumulative Depreciation')
    differed_depreciation_value = fields.Monetary(
        string="Depreciation", store=True)
