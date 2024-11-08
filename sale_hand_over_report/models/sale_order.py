# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

