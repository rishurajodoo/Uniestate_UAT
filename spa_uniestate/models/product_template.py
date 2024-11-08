# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_owner_name = fields.Char(related='property_owner.name', string="Property Owner Name", store=True)
    property_owner_name_arabic = fields.Char(related='property_owner.name_arabic', string="Property Owner Name Arabic", store=True)