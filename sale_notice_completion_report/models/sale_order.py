# -*- coding: utf-8 -*-

from odoo import models, api, _
from num2words import num2words


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def amount_to_text(self, amount):
        return num2words(amount)
