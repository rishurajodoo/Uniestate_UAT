from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _default_notice_period(self):
        # Fetch the notice period value from ir.config_parameter
        notice_period = self.env['ir.config_parameter'].sudo().get_param('sale_commission_ext.notice_period', default=0)
        return int(notice_period)

    notice_period = fields.Integer(string="Notice Period", default=lambda self: self._default_notice_period(), )
    is_np_editable = fields.Boolean(string="Is Notice Period Editable ?")
    notice_period_bool = fields.Boolean(compute='_get_notice_period_bool',string="Notice Period Bool")

    def _get_notice_period_bool(self):
        for rec in self:
            rec.notice_period_bool = False
            if rec.notice_period >=0:
                notice_period = self.env['ir.config_parameter'].sudo().get_param('sale_commission_ext.notice_period',
                                                                                 default=0)
                self.notice_period =  int(notice_period)




