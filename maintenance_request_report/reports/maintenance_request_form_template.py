# -*- coding: utf-8 -*-

from odoo import models, api, fields
from datetime import datetime


class MaintenanceRequestReport(models.AbstractModel):
    _name = 'report.maintenance_request_report.maintenance_request_form'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['maintenance.request'].browse(docids)
        check_list_doc = []
        schedule_list_dict = {}
        spare_list = []
        amount_total_dict = {}

        for doc in docs:
            if doc.checklist_ids:
                for check_list in doc.checklist_ids:
                    check_list_line_dict = {}
                    check_list_line_dict['description'] = check_list.description or ""
                    check_list_line_dict['remarks'] = check_list.remarks or ""
                    check_list_line_dict['ohter_infor'] = check_list.ohter_infor or ""
                    check_list_line_dict['state'] = check_list.state or ""
                    check_list_doc.append(check_list_line_dict)

            if doc.schedule_date:
                datetime_obj = fields.Datetime.from_string(doc.schedule_date)
                schedule_list_dict['date_str'] = datetime_obj.strftime("%d/%b/%Y")
                schedule_list_dict['time_str'] = datetime_obj.strftime("%H:%M:%S")

            if doc.sparepart_ids:
                for spare in doc.sparepart_ids:
                    spare_line_dict = {}
                    spare_line_dict['product'] = spare.product_id.name or ""
                    spare_line_dict['qty'] = spare.Qty or ""
                    spare_line_dict['cost'] = spare.cost or ""
                    spare_line_dict['total_cost'] = spare.total_cost or ""
                    spare_list.append(spare_line_dict)
                amount_total_dict['total_amount'] = sum(spare.total_cost for spare in doc.sparepart_ids) or ""
        return {
            'doc_ids': docids,
            'doc_model': 'maintenance.request',
            'docs': docs,
            'data': data,
            'check_list': check_list_doc,
            'spare_list': spare_list,
            'date_str': schedule_list_dict['date_str'] if "date_str" in schedule_list_dict else "",
            'time_str': schedule_list_dict['time_str'] if "time_str" in schedule_list_dict else "",
            'total_amount': amount_total_dict['total_amount'] if "total_amount" in amount_total_dict else ""
        }
