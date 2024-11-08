from odoo import fields, models, api


class PaymentPlan(models.Model):
    _name = 'payment.plan'
    _rec_name = 'name'

    name = fields.Char('Name')
    name_arabic = fields.Char('Arabic Name')
    code = fields.Char('Code')
    percentage = fields.Float('Percentage')
    amount = fields.Float('Amount')
    is_booked = fields.Boolean('Is Booked')
    is_admin_fee = fields.Boolean('DLD+Admin Fee')
    is_post_cheque = fields.Boolean('Security Cheque', default=False)
    is_ejari = fields.Boolean('Ejari', default=False)
    is_dld = fields.Boolean('DLD', default=False)
    is_service_charges = fields.Boolean('Service Charges', default=False)
    is_oqood = fields.Boolean('OQOOD', default=False)
    is_debit = fields.Boolean('Debit Note', default=False)
    is_renewal = fields.Boolean('Is renewal', default=False)
    is_utility_charge = fields.Boolean('Is Utility Charge', default=False)
    sequence = fields.Integer("Sequence", default=1)
    is_invoice = fields.Boolean("Is Invoice", default=False)
    is_chiller_charges = fields.Boolean('Is Chiller Charge', default=False)
    is_completion = fields.Boolean('Is Completion', default=False)
    chiller_charge_config = fields.Boolean('Chiller Charge Config', compute='_compute_chiller_charge')



    # is_invoice = fields.Boolean('Invoice', default=False)

    def _compute_chiller_charge(self):
        for rec in self:
            chiller_charge = self.env["ir.config_parameter"].sudo().get_param('marquespoint_overall.is_chiller_charges')
            rec.chiller_charge_config = chiller_charge
