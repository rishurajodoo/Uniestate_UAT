from num2words import num2words

from odoo import api, fields, models


class PDCReceipt(models.Model):
    _inherit = 'pdc.payment'

    def qty_to_text(self, total):
        qty_txt = num2words(total)
        return qty_txt

    def qty_to_text_i(self, totat_i):
        qty_txt_i = num2words(totat_i)
        return qty_txt_i


class ReceiptVoucher(models.Model):
    _name = 'report.alshafar_chequereceipt_voucher.receipt_temp_id'

    @api.model
    def _get_report_values(self, docids, data=None):
        pdc = self.env['pdc.payment'].browse(docids)
        total_amount = sum(pdc.mapped('payment_amount'))

        rec_list = []

        for line in pdc:
            rec_list.append({
                'type': 'pdc',
                'pay_mode': 'Cheque',
                'cheque_no': line.cheque_no,
                'cheque_date': line.date_payment,
                'bank_id': line.commercial_bank_id.name,
                'memo': line.memo,
                'amount': line.payment_amount,
                'rv_num': line.get_jv.name,
                'partner_id': line.partner_id.name,
            })
        unit_rec = []
        for line in pdc:
            for unit_details in line.order_id:
                unit_names = ", ".join(unit.name for unit in unit_details.unit)
                unit_rec.append({
                    'project': unit_details.project.name,
                    'building': unit_details.building.name,
                    'floor': unit_details.floor.name.name,
                    'unit': unit_names
                })

        partner_ids = pdc.mapped('partner_id').ids
        cash_payment = self.env['account.payment'].search(
            [('order_id', '=', pdc.order_id.id), ('state', 'in', ['draft', 'posted']),
             ('partner_id', 'in', partner_ids), ('id', 'in', pdc.move_id.so_ids.account_payment_ids.ids)
             ])
        # cash_payment = cash_payment.filtered(lambda self: self.journal_id.type == 'cash')
        print(f"what is im partner_idssssssssssssssssssss")
        cash_payment = cash_payment.filtered(lambda self: self.journal_id.type in ['cash', 'bank'])
        total_amount_inv = sum(cash_payment.mapped('amount'))
        total_total = total_amount_inv + total_amount

        total_total_words = pdc.currency_id.amount_to_text(total_total)
        amount_in_words = pdc.currency_id.amount_to_text(total_amount_inv)

        cash_list = []
        for rec in cash_payment:
            print(rec, '=========recccccccc')
            print(rec.journal_id, '=======journal id')
            print(rec.journal_id.type, '=======journal id type')
            cash_list.append({
                'type': 'cash',
                'pay_mode': rec.journal_id.type.upper(),
                'date': rec.date,
                'amount': rec.amount,
                'memo': rec.ref
            })
        return {
            'record': rec_list,
            'cash_list': cash_list,
            'total': total_amount,
            'total_amount_inv': total_amount_inv,
            'amount_in_words': amount_in_words,
            'total_total': total_total,
            'total_total_words': total_total_words,
            'pdc': pdc,
            'pdc_type' : pdc.pdc_type,
            'unit_details': unit_rec
        }


class ReceiptPaymentVoucher(models.Model):
    _name = 'report.alshafar_chequereceipt_voucher.receipt_payment_temp_id'

    @api.model
    def _get_report_values(self, docids, data=None):        
        payment = self.env['account.payment'].browse(docids)
        pdc = self.env['account.payment'].browse(docids).order_id.pdc_ids
        order = self.env['account.payment'].browse(docids).order_id
        total_pdc_amount = sum(pdc.mapped('payment_amount'))

        total_amount_words = payment.currency_id.amount_to_text(payment.amount)

        rec_list = []

        for line in pdc:
            rec_list.append({
                'type': 'pdc',
                'pay_mode': 'Cheque',
                'cheque_no': line.cheque_no,
                'cheque_date': line.date_payment,
                'bank_id': line.commercial_bank_id.name,
                'memo': line.memo,
                'amount': line.payment_amount,
                'rv_num': line.get_jv.name,
                'partner_id': line.partner_id.name,
            })

        cash_list = []
        currency_symbol = ""
        payment_type = ""
        journal_type = ""
        for rec in payment:
            cash_list.append({
                'type': 'Cash',
                # 'pay_mode': 'Cash',
                'pay_mode': rec.payment_method_line_id.name,
                'date': rec.date.strftime('%d/%m/%Y'),
                'amount': rec.amount,
                'memo': rec.ref,
            })
            currency_symbol += rec.currency_id.symbol
            payment_type += rec.payment_type
            journal_type += rec.journal_id.type

        unit_rec = []
        for line in order:
            unit_names = ", ".join(unit.name for unit in line.unit)
            unit_rec.append({
                'project': line.project.name,
                'building': line.building.name,
                'floor': line.floor.name.name,
                'unit': unit_names
            })

        print("unit_rec", unit_rec)

        report_data = {
            'record': rec_list,
            'cash_list': cash_list,
            'date': payment.date,
            'partner': payment.partner_id.name,
            'total_amount': payment.amount,
            'total_amount_words': total_amount_words,
            'total': total_pdc_amount,
            'pdc': pdc,
            'unit_details': unit_rec,
            'currency_symbol': currency_symbol,
            'payment_type': payment_type,
            'journal_type': journal_type,
            'user_name': self.env.user.name,
            'company_name': self.env.company.name,
            'company_address': (self.env.company.street or '') + " " +
                               (self.env.company.street2 or '') + " " +
                               (self.env.company.city or '') + " " +
                               (self.env.company.state_id.name or '') + " " +
                               (self.env.company.country_id.name or '')
        }
        if self.env.company.logo:
            report_data.update({'company_logo': self.env.company.logo})

        return report_data
