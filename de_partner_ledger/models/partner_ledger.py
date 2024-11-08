# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015 Dynexcel (<http://dynexcel.com/>).
#
##############################################################################

import time

from odoo import fields, api, models
from dateutil import parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class PartnerLedger(models.TransientModel):
    _name = 'partner.ledger'

    start_date = fields.Date(string='From Date', required=True, default=fields.Date.today().replace(day=1))
    end_date = fields.Date(string='To Date', required=True, default=fields.Date.today())
    partner_id = fields.Many2many('res.partner', string='Partner', required=True, help='Select Partner for movement')
    sale_order_ids = fields.One2many('sale.order', 'partner_id', 'Sales Order',related="partner_id.sale_order_ids")
    sale_order_id = fields.One2many('sale.order','partner_id', string="Sale Orders")

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        if self.sale_order_id:
            # Get all start and end dates from the selected sale orders
            sale_order_dates = self.sale_order_ids.mapped(lambda so: (so.start_date, so.end_date))
            if sale_order_dates:
                # Calculate the new start_date and end_date
                new_start_date = min(date[0] for date in sale_order_dates)
                new_end_date = max(date[1] for date in sale_order_dates)

                # Update the fields
                self.start_date = new_start_date
                self.end_date = new_end_date

    @api.onchange('partner_id', 'start_date', 'end_date')
    def onchange_partner_id(self):
        # res = self.env['ir.actions.act_window']._for_xml_id('de_partner_ledger.action_partner_ledger_wizard')
        # res['domain'] = {'sale_order_id': [('id', '=', self.partner_id.sale_order_ids.ids)], }
        return {'domain': {'sale_order_id': [('id', '=', self.partner_id.sale_order_ids.ids)]}}

    def print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_id.ids,
            'sale_order_id': self.sale_order_id.ids
        }
        return self.env.ref('de_partner_ledger.action_partner_ledger_pdf').report_action(self, data)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # def action_partner_ledger(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Partner Ledger',
    #         'view_id': self.env.ref('de_partner_ledger.partner_ledger_wizard_report', False).id,
    #         'target': 'new',
    #         'res_model': 'partner.ledger',
    #         'context': {'default_partner_id': self.id},
    #         'view_mode': 'form',
    #     }
    #
    def action_partner_ledger_wizard(self):
        selected_ids = self.env.context.get('active_ids', [])
        selected_records = self.env['res.partner'].browse(selected_ids)
        print(selected_records)
        partners = []
        for r in selected_records:
            partners.append(r.id)
        print(partners)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Partner Ledger',
            'view_id': self.env.ref('de_partner_ledger.partner_ledger_wizard_report', False).id,
            'target': 'new',
            'res_model': 'partner.ledger',
            'context': {'default_partner_id': partners},
            'view_mode': 'form',
        }


class AccountInherit(models.Model):
    _inherit = 'account.account'

    is_pdc = fields.Boolean(string="Is PDC")
