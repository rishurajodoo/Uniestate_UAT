from odoo import api, fields, models, _
import xlsxwriter
from odoo.exceptions import UserError
import base64
import io
import pandas as pd
from datetime import date


class PropertyCustomReportWizard(models.Model):
    _name = 'property.custom.report.wizard'

    building_ids = fields.Many2many(comodel_name='project.project', string="Building")
    for_rent = fields.Boolean(default=True)
    for_sale = fields.Boolean(default=False)
    state = fields.Selection(
        selection=[("all", "All"),
                   ("available", "Available"),
                   ("reserved", "Reserved"),
                   ("booked", "Booked"),
                   ("sold", "Sold"),
                   ("rented", "Rented")],
        string="State", default="all")
    generate_xls_file = fields.Binary(
        "Generated file",
        help="Technical field used to temporarily hold the generated XLS file before its downloaded.")

    @api.constrains('for_sale', 'for_rent')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.for_sale and rec.for_rent:
                raise UserError("You Can't be able to select both Sale and Rent on same time")

    def property_custom_report_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        format1 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True})
        header = workbook.add_format({'font_size': 16, 'bg_color': '#d9dadb', 'align': 'center', 'bold': True})
        format2 = workbook.add_format({'font_size': 14, 'align': 'center', 'bg_color': '#d9dadb', 'bold': True})
        format3 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True})

        # repoort header
        sheet = workbook.add_worksheet("Property Custom Report ")
        floating_point_bordered = workbook.add_format({'num_format': '#,##0.00', 'border': 1})

        building_ids = 'All' if not self.building_ids else ', '.join(self.building_ids.mapped('name'))

        type = 'Saleable' if self.for_sale else 'Rentable'

        sheet.write(2, 3, 'Buildings', format1)
        sheet.write(2, 4, building_ids)
        sheet.write(2, 5, 'State', format1)
        sheet.write(2, 6, self.state)
        sheet.write(2, 7, 'Type', format1)
        sheet.write(2, 8, type)
        sheet.set_column(6, 1, 20)
        sheet.set_column(6, 2, 20)
        sheet.set_column(6, 2, 20)
        sheet.set_column(6, 3, 20)
        sheet.set_column(6, 4, 30)
        sheet.set_column(6, 5, 30)
        sheet.set_column(6, 6, 40)
        sheet.set_column(6, 7, 25)
        sheet.set_column(6, 8, 30)
        sheet.set_column(6, 9, 30)
        sheet.set_column(6, 10, 30)
        sheet.set_column(6, 11, 30)
        sheet.set_column(6, 12, 30)
        sheet.set_column(6, 13, 30)
        sheet.set_column(6, 14, 30)
        sheet.set_column(6, 15, 30)

        sheet.write(6, 1, 'Project', format1)
        sheet.write(6, 2, 'Building', format1)
        sheet.write(6, 3, 'Floor', format1)
        sheet.write(6, 4, 'Unit Name', format1)
        sheet.write(6, 5, 'Unit Type', format1)
        sheet.write(6, 6, 'Sub Unit Type', format1)
        sheet.write(6, 7, 'Property Size SQFT', format1)
        sheet.write(6, 8, 'Price/SQFT', format1)
        sheet.write(6, 9, 'Reasonable Price', format1)
        if self.for_sale:
            sheet.write(6, 10, 'Sales Price', format1)
        else:
            sheet.write(6, 10, 'Rent Price', format1)
        sheet.write(6, 11, 'Actual Price/SQFT', format1)
        col = 11
        if self.for_rent:
            sheet.write(6, col + 1, 'Percentage Variance', format1)
            sheet.write(6, col + 2, 'Payment Plan', format1)
            sheet.write(6, col + 3, 'Days', format1)
            sheet.write(6, col + 4, 'Status', format1)
        else:
            sheet.write(6, col + 1, 'Status', format1)

        domain = []
        if self.for_sale:
            domain += [('for_sale', '=', True)]
        if self.for_rent:
            domain += [('for_rent', '=', True)]
        if self.building_ids:
            domain += [('project', 'in', self.building_ids.ids)]
        if self.state == 'all':
            domain += [('state', 'in', ['available', 'reserved', 'rented', 'booked', 'sold'])]
        else:
            domain += [('state', '=', self.state)]

        unit_ids = self.env['product.product'].search(domain)

        i = 7
        # reasonable_price_1 = 0
        sale_rent_price_1 = 0
        actual_price_sqft_1 = 0
        percentage_variance_1 = 0
        for unit_id in unit_ids:
            reasonable_price = unit_id.reasonable_price
            sale_rent_price = unit_id.rent_price if self.for_rent else unit_id.property_price
            if sale_rent_price > 0 and unit_id.property_price > 0:
                actual_price_sqft = sale_rent_price / unit_id.property_size
            else:
                actual_price_sqft = 0
            if reasonable_price > 0 and sale_rent_price > 0:
                percentage_variance = ((reasonable_price - sale_rent_price) / reasonable_price) * 100
            else:
                percentage_variance = 0.0

            # reasonable_price_1 += reasonable_price
            sale_rent_price_1 += sale_rent_price
            actual_price_sqft_1 += actual_price_sqft
            percentage_variance_1 += percentage_variance

            sheet.write(i, 1, unit_id.project.name)
            sheet.write(i, 2, unit_id.building.name)
            sheet.write(i, 3, unit_id.floor_id.name.name)
            sheet.write(i, 4, unit_id.name)
            sheet.write(i, 5, unit_id.unit_type_id.name)
            sheet.write(i, 6, unit_id.sub_unit_id.name)
            sheet.write(i, 7, unit_id.property_size)
            sheet.write(i, 8, unit_id.price_sqft)
            sheet.write(i, 9, reasonable_price)
            sheet.write(i, 10, sale_rent_price)
            sheet.write(i, 11, actual_price_sqft, floating_point_bordered)

            col = 11
            date_diff = unit_id.end_date - unit_id.start_date
            if date_diff != 0:
                payment_plan = date_diff / pd.Timedelta(365, 'd')
                payment_plan = round(payment_plan, 2)
                days = "Years"
            else:
                payment_plan = " "
                days = " "
            if unit_id.tenancy_state == 'closed':
                tenancy_date = date.today() - unit_id.end_date
            else:
                tenancy_date = " "
            if self.for_rent:
                sheet.write(i, col + 1, percentage_variance, floating_point_bordered)
                sheet.write(i, col + 2, str(payment_plan) + " " + days)
                sheet.write(i, col + 3, tenancy_date)
                sheet.write(i, col + 4, unit_id.state)
            else:
                sheet.write(i, col + 1, unit_id.state)
            i += 1

        i += 3
        sheet.write(i, 2, 'Grand Totals')
        sheet.write(i, 7, sum(unit_ids.mapped('property_size')))
        sheet.write(i, 8, sum(unit_ids.mapped('price_sqft')))
        sheet.write(i, 9, sum(unit_ids.mapped('reasonable_price')))
        sheet.write(i, 10, sale_rent_price_1)
        sheet.write(i, 11, actual_price_sqft_1, floating_point_bordered)
        if self.for_rent:
            sheet.write(i, 12, percentage_variance_1, floating_point_bordered)

        workbook.close()
        output.seek(0)
        self.generate_xls_file = base64.b64encode(output.read())
        file_name = "Property Report" + "-" + str(date.today())
        return {
            'type': 'ir.actions.act_url',
            'url': "/web/content?model=property.custom.report.wizard&download=true&field=generate_xls_file&filename={}.xlsx&id={}".format(
                file_name, self.id),
            'target': 'self',
        }
