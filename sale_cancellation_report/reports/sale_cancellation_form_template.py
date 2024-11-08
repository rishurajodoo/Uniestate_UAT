# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime


class SaleCancellationReport(models.AbstractModel):
    _name = 'report.sale_cancellation_report.sale_cancellation_form'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        spa_list = []
        commission_list = []
        spa_line_dict = {}
        commission_line_dict = {}

        for doc in docs:
            if doc.purchaser_ids:
                spa_line_dict['name'] = doc.purchaser_ids[0].purchase_individual.name or ""
                spa_line_dict['nationality'] = doc.purchaser_ids[0].purchase_individual.country_arabic.name or ""
                spa_line_dict['id'] = doc.purchaser_ids[0].purchase_individual.passport_eng or ""
                spa_line_dict['date_of_issue'] = doc.purchaser_ids[0].purchase_individual.date_of_issue or ""
                spa_line_dict['place_of_issue'] = doc.purchaser_ids[0].purchase_individual.place_of_issue or ""
                spa_line_dict['phone'] = doc.purchaser_ids[0].purchase_individual.phone or ""
                spa_line_dict['fax'] = doc.purchaser_ids[0].purchase_individual.fax_eng or ""
                spa_line_dict['mobile'] = doc.purchaser_ids[0].purchase_individual.mobile or ""
                spa_line_dict['email'] = doc.purchaser_ids[0].purchase_individual.email or ""
                spa_line_dict['address'] = self.get_full_address(doc.purchaser_ids[0].purchase_individual) or ""
                spa_line_dict['permanent_address'] = self.get_full_address(doc.purchaser_ids[0].purchase_individual) or ""
                spa_line_dict['unit_code'] = doc.unit[0].name or ""
                spa_line_dict['building_no'] = doc.unit[0].building.name or ""
                spa_line_dict['apartment_no'] = doc.unit[0].building.plot_no or ""
                spa_line_dict['sub_unit'] = doc.unit[0].sub_unit_id.name or ""
                spa_line_dict['floor'] = doc.unit[0].floor_id.name.name or ""
                spa_line_dict['total_area'] = doc.unit[0].property_size or ""
                spa_line_dict['price'] = doc.unit[0].price_sqft or ""
                spa_line_dict['total_price_unit'] = doc.unit[0].property_price or ""
                spa_line_dict['price_parking'] = doc.unit[0].parking_price or ""
                spa_line_dict['total_price'] = doc.unit[0].property_price + doc.unit[0].parking_price
                spa_list.append(spa_line_dict)

            if doc.partner_agent_ids:
                for agent in doc.partner_agent_ids:
                    commission_line_dict['title'] = agent.name or ""
                    commission_line_dict['name'] = agent.name or ""
                    commission_line_dict['percentage'] = agent.commission_id.name or ""
                    commission_line_dict['amount'] = doc.commission_total
                    commission_list.append(commission_line_dict)



        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'data': data,
            'spa_list': spa_list,
            'commission_list': commission_list,
            'partner': docs.partner_id,
        }

    def get_full_address(self, partner):
        address_parts = [
            partner.street or '',
            partner.street2 or '',
            partner.city or '',
            (partner.state_id and partner.state_id.name) or '',
            partner.zip or '',
            (partner.country_id and partner.country_id.name) or ''
        ]
        # Join non-empty parts with a comma and space
        full_address = ', '.join(part.strip() for part in address_parts if part.strip())
        return full_address
