# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'



class PaymentPlanLines(models.Model):

    _inherit = 'payment.plan.line'

    sequence_number = fields.Integer(string='Sequence Number', compute='_compute_sequence_number', store=True,readonly=True)

    @api.depends('order_id.plan_ids')
    def _compute_sequence_number(self):
        for index, line in enumerate(sorted(self._origin.order_id.plan_ids, key=lambda x: x.create_date)):
            line.sequence_number = index + 1

