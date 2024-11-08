# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime


class LocalPurchaseReport(models.AbstractModel):
    _name = 'report.local_purchase_order.report_local_po_temp_uni'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(docids)
        line_list = []
        line_dict = {}

        for doc in docs:
            for line in doc.order_line:
                line_dict['description'] = line.name or ""
                line_dict['uom'] = line.product_uom.name or ""
                line_dict['qty'] = line.product_qty or ""
                line_dict['unit'] = line.price_unit or ""
                line_dict['total'] = line.price_subtotal or ""
                line_list.append(line_dict)



        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs': docs,
            'data': data,
            'line_list':line_list,
        }
