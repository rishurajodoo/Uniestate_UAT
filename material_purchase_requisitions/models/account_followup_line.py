# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountFollowupLine(models.Model):
    _inherit = 'account_followup.followup.line'

    is_pretty = fields.Boolean(default=False)
