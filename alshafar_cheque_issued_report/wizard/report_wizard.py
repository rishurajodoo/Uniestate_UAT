from odoo import api, fields, models
import io
import base64
import json
import xlsxwriter
from odoo.tools import date_utils


class ChequeIssuedReport(models.Model):
    _name = 'pdc.cheque.report.wizard'

    partner_id = fields.Many2many('res.partner', string='Partner')
    state = fields.Selection([
        ('all', 'All'),
        ('draft', 'Draft'),
        ('registered', 'Registered'),
        ('bounced', 'Bounced'),
        ('cleared', 'Cleared'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft')
    generate_xls_file = fields.Binary(
        "Generated file",
        help="Technical field used to temporarily hold the generated XLS file before its downloaded."
    )
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')

    def print_cheque_issued_report(self):
        data = {
            'partner_id': self.partner_id.ids,
            'state': self.state,
            'pdc_type': 'sent'
        }

        return self.env.ref('alshafar_cheque_issued_report.pdc_cheque_issue_report_action').report_action(self,
                                                                                                          config=False,
                                                                                                          data=data)

    def pdc_cheque_report_excel(self):
        data = {
            'partner_id': self.partner_id.ids,
            'state': self.state,
            'pdc_type': 'sent'
        }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        format1 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bg_color': 'green', 'color': 'white', 'bold': True})
        header = workbook.add_format({'font_size': 16, 'align': 'center', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})
        format3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})

        # repoort header
        sheet = workbook.add_worksheet("Cheque Issued ")
        sheet.write(1, 2, 'CHEQUES ISSUED (CDC & PDC) REPORT')
        sheet.set_column(3, 0, 20)
        sheet.set_column(3, 1, 20)
        sheet.set_column(3, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(3, 4, 30)
        sheet.set_column(3, 5, 30)
        sheet.set_column(3, 6, 40)
        sheet.set_column(3, 7, 25)
        sheet.set_column(3, 8, 25)

        sheet.write(4, 0, 'PV No.', format1)
        sheet.write(4, 1, 'PV Date.', format1)
        sheet.write(4, 2, 'Cheque Date', format1)
        sheet.write(4, 3, 'Cheque No.', format1)
        sheet.write(4, 4, 'Division', format1)
        sheet.write(4, 5, 'Name', format1)
        sheet.write(4, 6, 'Memo', format1)
        sheet.write(4, 7, 'Amount', format1)
        sheet.write(4, 8, 'State', format1)

        domain = []

        if self.partner_id:
            domain += [('partner_id', 'in', self.partner_id.ids)]
        if self.date_from and self.date_to:
            domain += [('date_registered', '>=', self.date_from), ('date_registered', '<=', self.date_to)]
        if self.date_from and not self.date_to:
            domain += [('date_registered', '>=', self.date_from)]
        if self.date_to:
            domain += [('date_registered', '<=', self.date_to)]

        pdc = self.env['pdc.payment'].search(domain)

        if self.partner_id:
            pdc = pdc.filtered(lambda self: self.partner_id.id in self.partner_id.ids)
        if data['pdc_type'] == 'sent':
            pdc = pdc.filtered(lambda self: self.pdc_type == data['pdc_type'])
        if data['state']:
            if data['state'] == 'all':
                pdc = pdc.filtered(lambda self: self.state in ['draft', 'registered', 'bounced', 'cleared', 'cancel'])
            else:
                pdc = pdc.filtered(lambda self: self.state == data['state'])

        i = 5
        for line in pdc:
            sheet.write(i, 0, line.name)
            sheet.write(i, 1, str(line.date_registered))
            sheet.write(i, 2, str(line.date_payment))
            sheet.write(i, 3, line.cheque_no)
            sheet.write(i, 4, 'Division')
            sheet.write(i, 5, line.partner_id.name)
            sheet.write(i, 6, line.memo)
            sheet.write(i, 7, line.payment_amount)
            sheet.write(i, 8, line.state.upper())
            i += 1
        # sheet.write(4, 1, 'Ticket No#', format1)
        # sheet.write(4, 2, 'Lead Name', format1)
        # sheet.write(4, 3, 'Team', format1)
        # sheet.write(4, 4, 'Ticket Type', format1)
        # sheet.write(4, 5, 'Ticket Type', format1)
        # j = 5
        # if lst:
        #     for rec in lst:
        #         sheet.write(j, 1, rec.get('name'))
        #         sheet.write(j, 2, rec.get('lead'))
        #         sheet.write(j, 3, rec.get('team_id'))
        #         sheet.write(j, 4, rec.get('ticket_type_id'))
        #         sheet.write(j, 5, rec.get('time'))
        #         j += 1
        # else:
        #     sheet.write(7, 2, 'No record found !')

        workbook.close()
        output.seek(0)

        self.generate_xls_file = base64.b64encode(output.read())
        return {
            'type': 'ir.actions.act_url',
            'url': "/web/content?model=pdc.cheque.report.wizard&download=true&field=generate_xls_file&filename=Form_2307.xlsx&id={}".format(
                self.id),
            'target': 'self',
        }
