# -*- coding: utf-8 -*-


from odoo import models
from datetime import datetime
from pytz import timezone


class CustomReport(models.AbstractModel):
    _name = "report.de_partner_ledger.de_partner_ledger_pdf_report"

    def get_partner_bal(self, data):
        lst = []
        for p in data['partner_id']:
            partner_ledger = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '>=', data['start_date']), ('date', '<=', data['end_date']),
                 ('balance', '!=', 0), '|',
                 ('account_id.account_type', '=', 'liability_payable'), ('account_id.account_type', '=', 'asset_receivable')
                    , ('account_id.is_pdc', '=', False)]).sorted(key=lambda r: r.date)
            for r in partner_ledger:
                # if r.move_id.name == 'CBD22/2024/06/0003':
                #     print("jnh")
                lst.append(r)
        # print(lst)
        return lst

    def get_opening_bal(self, data):
        lst = []
        for p in data['partner_id']:
            open_bal = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '<', data['start_date']),
                 ('move_id.state', '=', 'posted'), ('full_reconcile_id', '=', False), ('balance', '!=', 0),
                 ('account_id.reconcile', '=', True), ('full_reconcile_id', '=', False), '|',
                 ('account_id.account_type', '=', 'liability_payable'), ('account_id.account_type', '=', 'asset_receivable')])
            bal = 0
            for rec in open_bal:
                bal = bal + rec.balance
            record = self.env['res.partner'].search([('id', '=', p)])
            vals = {
                'partner': record,
                'bal': bal,
            }
            lst.append(vals)
        return lst

    def get_foreign_opening_bal(self, data):
        lst = []
        for p in data['partner_id']:
            open_bal = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '<', data['start_date']),
                 ('move_id.state', '=', 'posted'), ('full_reconcile_id', '=', False), ('balance', '!=', 0),
                 ('account_id.reconcile', '=', True), ('full_reconcile_id', '=', False), '|',
                 ('account_id.account_type', '=', 'liability_payable'), ('account_id.account_type', '=', 'asset_receivable')])
            bal = 0
            for rec in open_bal:
                bal = bal + rec.amount_currency
            record = self.env['res.partner'].search([('id', '=', p)])
            vals = {
                'partner': record,
                'bal': bal,
            }
            lst.append(vals)
        # print("foreign opening",lst)
        return lst

    def get_closing_bal(self, data):
        lst = []
        for p in data['partner_id']:
            open_bal = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '>=', data['start_date']), ('date', '<=', data['end_date']),
                 ('move_id.state', '=', 'posted'), ('full_reconcile_id', '=', False), ('balance', '!=', 0),
                 ('account_id.reconcile', '=', True), ('full_reconcile_id', '=', False), '|',
                 ('account_id.account_type', '=', 'liability_payable'), ('account_id.account_type', '=', 'asset_receivable'),
                 ('account_id.is_pdc', '=', False)])
            bal = 0
            for rec in open_bal:
                bal = bal + rec.balance
            record = self.env['res.partner'].search([('id', '=', p)])
            vals = {
                'partner': record,
                'bal': bal,
            }
            lst.append(vals)
        return lst

    def get_print_date(self):
        now_utc_date = datetime.now()
        now_dubai = now_utc_date.astimezone(timezone('Asia/Karachi'))
        return now_dubai.strftime('%d/%m/%Y %H:%M:%S')

    def _get_report_values(self, docids, data=None):

        dat = self.get_partner_bal(data)
        lst = []
        sale_order = self.env['sale.order'].search([('id', 'in', data['sale_order_id'])])
        for r in sale_order:
            lst.append(r)
        sale = lst
        openbal = self.get_opening_bal(data)
        closingbal = self.get_closing_bal(data)

        account_pdc_recieve_id = self.env['ir.config_parameter'].get_param('pdc_payments.pdc_receivable')
        account_recieve_id = self.env['account.account'].search([('id', '=', account_pdc_recieve_id)])

        account_pdc_payable_id = self.env['ir.config_parameter'].get_param('pdc_payments.pdc_payable')
        account_payable_id = self.env['account.account'].search([('id', '=', account_pdc_payable_id)])

        # pdc_partner_ledger = self.env['account.move.line'].search(
        #     [('partner_id', '=', result.partner_id.id),('account_id', '=', account_recieve_id.id),('account_id', '=',account_payable_id.id)])

        partners = []
        for p in data['partner_id']:
            record = self.env['res.partner'].search([('id', '=', p)])
            partners.append(record)
        pdc_ledger = []
        pdc_opening = []
        pdc_closing = []
        for p in data['partner_id']:
            open_bal = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '<', data['start_date']),
                 ('move_id.state', '=', 'posted'), ('balance', '!=', 0), '|',
                 ('account_id', '=', account_recieve_id.id), ('account_id', '=', account_payable_id.id)
                 ])
            bal = 0
            for rec in open_bal:
                print(rec.date)
                bal = bal + rec.balance
            record = self.env['res.partner'].search([('id', '=', p)])
            vals = {
                'partner': record,
                'bal': -1 * bal,
            }
            pdc_opening.append(vals)
            closing_bal = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '>=', data['start_date']), ('date', '<=', data['end_date']),
                 ('move_id.state', '=', 'posted'), ('balance', '!=', 0), '|',
                 ('account_id', '=', account_recieve_id.id), ('account_id', '=', account_payable_id.id), ])
            b = 0
            for cl in closing_bal:
                b = b + cl.balance
            record = self.env['res.partner'].search([('id', '=', p)])
            vals = {
                'partner': record,
                'bal': -1 * b,
            }
            pdc_closing.append(vals)
            pdc_partner_ledger = self.env['account.move.line'].search(
                [('partner_id', '=', p), ('date', '>=', data['start_date']),
                 ('date', '<=', data['end_date']),
                 ('move_id.state', '=', 'posted'), '|',
                 ('account_id', '=', account_recieve_id.id), ('account_id', '=', account_payable_id.id)],
                order="date asc")
            for pdc in pdc_partner_ledger:
                print(pdc.move_id.pdc_cleared_id.state)
                print(pdc.move_id.pdc_registered_id.state)
                print(pdc.move_id.pdc_bounce_id.state)
                pdc_ledger.append(pdc)

        active = self.env['partner.ledger'].browse(self.env.context.get('active_ids'))
        # print(active)
        print("pdc opening", pdc_opening)
        print("pdc Closing", pdc_closing)
        print({
            'doc_ids': self.ids,
            'doc_model': 'partner.ledger',
            'openbal': openbal,
            'print_date': self.get_print_date(),
            'login_user': self.env.user.name,
            'foreign_openbal': self.get_foreign_opening_bal(data),
            # 'closingbal': closingbal + openbal,
            'closingbal': closingbal,
            'pdc_opening': pdc_opening,
            'pdc_closing': pdc_closing,
            'dat': dat,
            'pdc_partner': pdc_ledger,
            'data': data,
            'partners': partners,
            'result': active,
            'sale': sale
        })
        return {
            'doc_ids': self.ids,
            'doc_model': 'partner.ledger',
            'openbal': openbal,
            'print_date': self.get_print_date(),
            'login_user': self.env.user.name,
            'foreign_openbal': self.get_foreign_opening_bal(data),
            # 'closingbal': closingbal + openbal,
            'closingbal': closingbal,
            'pdc_opening': pdc_opening,
            'pdc_closing': pdc_closing,
            'dat': dat,
            'pdc_partner': pdc_ledger,
            'data': data,
            'partners': partners,
            'result': active,
            'sale': sale

        }
