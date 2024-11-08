# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime
from num2words import num2words


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contact_site = fields.Char(string="Contact at Site")

    def amount_to_text(self, amount):
        return num2words(amount)


