# -*- coding: utf-8 -*-

from odoo import models, api
from datetime import datetime


class SaleHandingOverReport(models.AbstractModel):
    _name = 'report.sale_hand_over_report.sale_hand_over_report_form'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        spa_list = []
        unit_list = []
        commission_list = []
        spa_line_dict = {}
        unit_line_dict = {}
        commission_line_dict = {}

        for doc in docs:
            if doc.purchaser_ids:
                spa_line_dict['name'] = doc.purchaser_ids[0].purchase_individual.name or ""
                spa_line_dict['street'] = doc.purchaser_ids[0].purchase_individual.street or ""
                spa_line_dict['street2'] = doc.purchaser_ids[0].purchase_individual.street2 or ""
                spa_line_dict['city'] = doc.purchaser_ids[0].purchase_individual.city or ""
                spa_line_dict['state'] = doc.purchaser_ids[0].purchase_individual.state_id.name if doc.purchaser_ids[0].purchase_individual.state_id else ""
                spa_line_dict['zip'] = doc.purchaser_ids[0].purchase_individual.zip or ""
                spa_line_dict['country'] = doc.purchaser_ids[0].purchase_individual.country_id.name if doc.purchaser_ids[0].purchase_individual.country_id else ""
                spa_list.append(spa_line_dict)
            if doc.unit:
                unit_line_dict['unit_code'] = doc.unit[0].name or ""

            unit_line_dict['unit_code'] = doc.unit[0].name or ""
            unit_line_dict['building_no'] = doc.unit[0].building.name or ""
            unit_line_dict['apartment_no'] = doc.unit[0].building.plot_no or ""
            unit_line_dict['sub_unit'] = doc.unit[0].sub_unit_id.name or ""
            unit_line_dict['floor'] = doc.unit[0].floor_id.name.name or ""
            unit_line_dict['total_area'] = doc.unit[0].property_size or ""
            unit_line_dict['price'] = doc.unit[0].price_sqft or ""
            unit_line_dict['total_price_unit'] = doc.unit[0].rent_price or ""
            unit_line_dict['price_parking'] = doc.unit[0].parking_price or ""
            unit_line_dict['total_price'] = doc.unit[0].rent_price + doc.unit[0].parking_price
            unit_list.append(unit_line_dict)

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
            'unit': doc.unit[0].name,
            'unit_list': unit_list,
            'commission_list': commission_list,
            'partner': docs.partner_id,
        }
