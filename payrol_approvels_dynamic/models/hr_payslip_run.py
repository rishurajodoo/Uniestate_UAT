
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_submit_approval(self):
        if self.slip_ids:
            for slip in self.slip_ids:
                slip.submit_for_approval()
        else:
            raise ValidationError(_('No payslip in the batch'))
