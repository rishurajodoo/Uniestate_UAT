from odoo import models, api
from datetime import datetime


class PaymentVoucherReport(models.AbstractModel):
    _name = 'report.property_custom_reports.sale_marquis'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        domain = []
        data_list = []  # Initialize an empty list to store data

        for doc in docs:
            rent_payment = self.env['rent.payment.plan.line'].search([('order_id', '=', doc.id)])

            for rec in rent_payment:
                order_liness = docs.order_line

                for record in order_liness:
                    data_dict = {}  # Initialize an empty dictionary to store data for each record
                    if record.product_id.is_unit and not record.is_debit:
                        if not rec.milestone_id.is_post_cheque and not rec.milestone_id.is_ejari and not rec.milestone_id.is_debit:
                            data_dict['tax'] = record.tax_id.name
                            data_dict['mode'] = rec.type.capitalize()

                            data_dict['date'] = rec.start_date
                            data_dict['amount'] = rec.amount
                            data_dict['tax_amount'] = rec.tax_amount
                            data_dict['milestone'] = rec.milestone_id.name
                            data_dict['total'] = rec.amount + rec.tax_amount
                            data_list.append(data_dict)
                            break  # Append the dictionary to the list
                    if record.product_id.is_unit and record.is_debit:
                        if rec.milestone_id.is_debit and not rec.milestone_id.is_post_cheque and not rec.milestone_id.is_ejari:
                            data_dict['tax'] = record.tax_id.name
                            data_dict['date'] = rec.start_date
                            data_dict['amount'] = rec.amount
                            data_dict['mode'] = rec.type.capitalize()

                            data_dict['tax_amount'] = rec.tax_amount
                            data_dict['milestone'] = rec.milestone_id.name
                            data_dict['total'] = rec.amount + rec.tax_amount

                            data_list.append(data_dict)
                            break  # Append the dictionary to the list
                    if record.product_id.is_sec:
                        if rec.milestone_id.is_post_cheque:
                            data_dict['tax'] = record.tax_id.name
                            data_dict['date'] = rec.start_date
                            data_dict['mode'] = rec.type.capitalize()

                            data_dict['amount'] = rec.amount
                            data_dict['tax_amount'] = rec.tax_amount
                            data_dict['milestone'] = rec.milestone_id.name
                            data_dict['total'] = rec.amount + rec.tax_amount

                            data_list.append(data_dict)
                            break  # Append the dictionary to the list
                    if record.product_id.is_ejari:
                        if rec.milestone_id.is_ejari:
                            data_dict['tax'] = record.tax_id.name
                            data_dict['date'] = rec.start_date
                            data_dict['mode'] = rec.type.capitalize()

                            data_dict['amount'] = rec.amount
                            data_dict['tax_amount'] = rec.tax_amount
                            data_dict['milestone'] = rec.milestone_id.name
                            data_dict['total'] = rec.amount + rec.tax_amount

                            data_list.append(data_dict)
                            break;  # Append the dictionary to the list

        print(f"what is in data list=------------------------{data_list}")
        # Now 'data_list' contains a list of dictionaries, where each dictionary represents the data for each iteration

        docides = docs
        for doc_id in docides:
            sale_order_line = self.env['sale.order.line'].search([("order_id", "=", doc_id.id)])
            rent_payment = self.env['rent.payment.plan.line'].search([("order_id", "=", doc_id.id)])
            print(
                f"what is in saleorderline-------------------------{sale_order_line} and what it is of rental------{rent_payment}")
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'data': data,
            'data_list': data_list
        }
