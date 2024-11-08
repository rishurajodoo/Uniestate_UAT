from odoo import models, fields, api, _


class PdcPayment(models.Model):
    _inherit = 'pdc.payment'

    def print_check(self):
        print("hello")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Formats',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'cheque.types',
            'target': 'new',
            'context': {'default_pdc_cheque_id': self.id},
        }
        # return {
        #     'name': "Cheque Format",
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'cheque.types',
        #     'target': 'new',
        #
        # }
