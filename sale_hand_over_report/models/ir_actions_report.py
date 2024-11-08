# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_template(self, template, values=None):
        order = values.get('docs')
        if order:
            if values.get('doc_model') == 'sale.order':
                if str(template) == 'sale_hand_over_report.sale_hand_over_report_form' and order.for_rent:
                    raise ValidationError(_('Report print in only for sale.'))
        res = super()._render_template(template, values)
        return res
