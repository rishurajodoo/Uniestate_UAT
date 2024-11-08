# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime


class ResUsers(models.Model):
    _inherit = 'res.users'

    po_box = fields.Char(string="P.O Box")