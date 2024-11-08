# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_chiller_charges = fields.Boolean('Is Chiller Charge', config_parameter='marquespoint_overall.is_chiller_charges')
