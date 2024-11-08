# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_template(self, template, values=None):
        order = values.get('docs')
        if order:
            if values.get('doc_model') == 'sale.order':
                if str(template) == 'spa_uniestate.report_spa_uniestate' and order.for_rent:
                    raise ValidationError(_('Report print in only for sale.'))
                if (str(template) == 'tenancy_contract_report.tenancy_contract_template' or str(
                        template) == 'property_custom_reports.debit_note_id_print') and order.for_sale:
                    raise ValidationError(_('Report print in only for rent.'))
        res = super()._render_template(template, values)
        return res
