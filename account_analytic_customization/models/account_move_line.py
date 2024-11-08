# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.move.line'

    building = fields.Many2one('property.building', string='Building', compute='_compute_property_items', store=True)
    floor = fields.Many2one(comodel_name='property.floor', string='Floor', compute='_compute_property_items', store=True)
    unit = fields.Many2many(comodel_name='product.product', string='Unit', compute='_compute_property_items', store=True)

    @api.depends('move_id')
    def _compute_property_items(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.building:
                    rec.building = rec.move_id.building
                else:
                    rec.building = False
                if rec.move_id.floor:
                    rec.floor = rec.move_id.floor
                else:
                    rec.floor = False
                if rec.move_id.unit:
                    rec.unit = [(6, 0, rec.move_id.unit.ids)]
