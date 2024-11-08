from num2words import num2words
from odoo import api, fields, models


class PDCCheques(models.Model):
    _inherit = 'pdc.payment'

    get_jv = fields.Many2one(string='Registered', comodel_name='account.move', compute="_compute_get_jv")

    def _compute_get_jv(self):
        for rec in self:
            check_jv = self.env['account.move'].search([('pdc_registered_id', '=', rec.id)])
            rec.get_jv = check_jv

    def qty_to_text(self, total):
        qty_txt = num2words(total)
        return qty_txt


class AccountMove(models.Model):
    _inherit = 'account.move'

    def amt_total_text(self, total):
        qty_txt1 = num2words(total)
        qty_txt = "Dirham" + " " + qty_txt1.title() + " " + "Only"
        return qty_txt
