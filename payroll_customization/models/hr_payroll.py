# -*- coding: utf-8 -*-

from odoo import models

class HRPayslip(models.Model):
    """Class To inherit the HR Payslip"""
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        """Method to set the analytic account and partner"""
        res = super(HRPayslip, self).action_payslip_done()
        if self.move_id:
            for line in self.move_id.line_ids:
                line.partner_id = self.employee_id.user_partner_id.id