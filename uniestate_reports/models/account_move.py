from odoo import api, fields, models, _


class AccountMoveInherited(models.Model):
    _inherit = 'account.move'

    def get_amount_in_words(self, amount):
        text = self.currency_id.amount_to_text(amount)
        return text.title()
