# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    building = fields.Many2one('property.building', string='Building', compute='_compute_property_items', store=True)
    floor = fields.Many2one(comodel_name='property.floor', string='Floor', compute='_compute_property_items', store=True)
    unit = fields.Many2many(comodel_name='product.product', string='Unit', compute='_compute_property_items', store=True)
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account',  compute='_compute_analytic_account', store=True)
    analytic_plan_account_id = fields.Many2one(comodel_name='account.analytic.plan', string='Analytic Account',  compute='_compute_analytic_account', store=True)

    @api.depends('account_id')
    def _compute_analytic_account(self):
        for rec in self:
            if rec.account_id:
                rec.analytic_account_id = rec.account_id
            else:
                rec.analytic_account_id = False
            if rec.account_id.plan_id:
                rec.analytic_plan_account_id = rec.account_id.plan_id
            else:
                rec.analytic_plan_account_id = False

    @api.depends('move_line_id')
    def _compute_property_items(self):
        for rec in self:
            if rec.move_line_id:
                if rec.move_line_id.move_id.building:
                    rec.building = rec.move_line_id.move_id.building
                else:
                    rec.building = False
                if rec.move_line_id.move_id.floor:
                    rec.floor = rec.move_line_id.move_id.floor
                else:
                    rec.floor = False
                if rec.move_line_id.move_id.unit:
                    rec.unit = [(6, 0, rec.move_line_id.move_id.unit.ids)]
