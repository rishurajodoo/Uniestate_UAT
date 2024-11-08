from datetime import datetime

import pytz

from odoo import api, fields, models, api, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    agreement_date = fields.Date(string="Agreement Date")

    def get_current_timezone_time(self):
        timezone = pytz.timezone(self.env.user.tz)
        return datetime.now(timezone).time().strftime('%H:%M:%S')
