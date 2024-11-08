# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
