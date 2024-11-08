from odoo import api, fields, models, _
import xlsxwriter

import base64
import io


class OnHandReport(models.Model):
    _name = 'pdc.onhand.wizard'

    partner_id = fields.Many2many('res.partner', string='Partner')
    generate_xls_file = fields.Binary(
        "Generated file",
        help="Technical field used to temporarily hold the generated XLS file before its downloaded."
    )
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')

    # state = fields.Selection([
    #                           ('all', 'All'),
    #                           ('draft', 'Draft'),
    #                           ('registered', 'Registered'),
    #                           ('bounced', 'Bounced'),
    #                           ('cleared', 'Cleared'),
    #                           ('cancel', 'Cancel'),
    #                           ], string='State', default='draft')

    def print_onhand_report(self):
        data = {
            'partner_id': self.partner_id.ids,
            # 'state': self.state,
            'pdc_type': 'received'
        }

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        format1 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bg_color': 'red', 'color': 'white', 'bold': True})
        header = workbook.add_format({'font_size': 16, 'align': 'center', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})
        format3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})

        # repoort header
        sheet = workbook.add_worksheet("On Hand Cheque ")
        sheet.write(1, 2, 'On Hand Cheque (CDC & PDC) REPORT')
        sheet.set_column(3, 0, 20)
        sheet.set_column(3, 1, 20)
        sheet.set_column(3, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(3, 4, 30)
        sheet.set_column(3, 5, 30)
        sheet.set_column(3, 6, 40)
        sheet.set_column(3, 7, 25)
        sheet.set_column(3, 8, 30)
        sheet.set_column(3, 9, 30)
        sheet.set_column(3, 10, 30)
        sheet.set_column(3, 11, 30)
        sheet.set_column(3, 12, 30)

        sheet.write(4, 0, 'Chq Date', format1)
        sheet.write(4, 1, 'Chq No', format1)
        sheet.write(4, 2, 'Partner Name', format1)
        sheet.write(4, 3, 'Name', format1)
        sheet.write(4, 4, 'Building', format1)
        sheet.write(4, 5, 'Unit', format1)
        sheet.write(4, 6, 'Amount', format1)
        sheet.write(4, 7, 'Totals', format1)
        sheet.write(4, 8, 'Contact Type', format1)
        sheet.write(4, 9, 'Tenant Bank', format1)
        sheet.write(4, 10, 'From Date', format1)
        sheet.write(4, 11, 'To Date', format1)
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
        if data['partner_id']:
            pdc = pdc.filtered(lambda self: self.partner_id.id in data['partner_id'])
        if data['pdc_type']:
            pdc = pdc.filtered(lambda self: self.pdc_type == data['pdc_type'])
        # if data['state']:
        #     if data['state'] == 'all':
        #         pdc = pdc.filtered(lambda self: self.state in ['draft','registered','bounced','cleared','cancel'])
        #     else:
        #         pdc = pdc.filtered(lambda self: self.state == data['state'])

        i = 5
        for line in pdc:
            # s_o_f = self.env['rent.installment.line'].search([('pdc_payment_id', '=', line.id)])
            # ten_con = self.env['tenancy.contract'].search([('order_id', '=', s_o_f.order_id.id)])
            # if len(ten_con.ids) > 0 and len(ten_con.ids) <= 1:
            sheet.write(i, 0, str(line.date_registered))
            sheet.write(i, 1, line.cheque_no)
            sheet.write(i, 2, str(line.partner_id.name))
            sheet.write(i, 3, str(line.name))
            sheet.write(i, 4, line.building_id.name)

            sheet.write(i, 5, ', '.join(line.unit_id.mapped('name')))

            # sheet.write(i, 5, line.unit_id.name)
            sheet.write(i, 6, line.payment_amount)
            sheet.write(i, 7, line.payment_amount)
            sheet.write(i, 9, line.commercial_bank_id.name)
            ten_con = line.order_id.tenancy
            if ten_con:
                if ten_con.state == 'open':
                    sheet.write(i, 8, 'IN PROGRESS')
                else:
                    sheet.write(i, 8, ten_con.state.upper())
                sheet.write(i, 10, str(ten_con.start_date))
                sheet.write(i, 11, str(ten_con.end_date))
            i += 1

        workbook.close()
        output.seek(0)
        self.generate_xls_file = base64.b64encode(output.read())
        return {
            'type': 'ir.actions.act_url',
            'url': "/web/content?model=pdc.onhand.wizard&download=true&field=generate_xls_file&filename=Form_2307.xlsx&id={}".format(
                self.id),
            'target': 'self',
        }
