# -*- coding: utf-8 -*-

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class TenancyContract(models.Model):
    _inherit = "tenancy.contract"

    amount_per_month = fields.Float(string='Amount Per Month', compute='_compute_amount_per_month')

    def _compute_amount_per_month(self):
        for contract in self:
            if contract.start_date and contract.end_date:
                date_diff = relativedelta(contract.end_date, contract.start_date)
                months = date_diff.years * 12 + date_diff.months + (
                    1 if date_diff.days > 0 else 0)

                if months > 0:
                    contract.amount_per_month = contract.amount / months
                else:
                    contract.amount_per_month = 0
            else:
                contract.amount_per_month = 0
