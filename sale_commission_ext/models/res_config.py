from odoo import fields, models, api, _

class ConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    notice_period = fields.Integer(string='Notice Period ',
                                   config_parameter='sale_commission_ext.notice_period')