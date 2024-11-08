from odoo import models, api

class PaymentVoucherReport(models.AbstractModel):
    _name = 'report.alshafar_payment_voucher.journal_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        domain = []
        
        # name = docs.name
        # driver = self.driver_id
        # state = self.state
        
        # if name:
        #     domain +=[('move_id.name','=',name)]
        # pdc = self.env['pdc.payment'].search_read(domain)
        # print(f"in journal reports pdc objects----------------{pdc}")
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'data': data,
        }