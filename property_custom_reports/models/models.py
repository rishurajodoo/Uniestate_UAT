# # -*- coding: utf-8 -*-
#
from odoo import models, fields, api
from datetime import datetime


#
#
class PaymentMode(models.Model):
    _name = 'payment.mode'
    _description = 'for payment mode only created'
    name = fields.Char(string="Pament Mode")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def is_parking(self):
        is_parking = ""
        if self.product_id.is_parking == "no":
            is_parking = "Yes"
        elif self.product_id.is_parking == "yes":
            is_parking = "No"
        else:
            is_parking = ""
        return is_parking

    def is_furnished(self):
        is_furnished = ""
        if self.product_id.furnishing == "yes":
            is_furnished = "Yes"
        elif self.product_id.furnishing == "no":
            is_furnished = "No"
        else:
            is_furnished = ""
        return is_furnished

    def get_unit_name(self):
        for rec in self:
            if isinstance(rec.product_id.name, str):
                property_no = rec.product_id.name.split('-')
                return property_no[-1] if property_no else rec.product_id.name
            else:
                # Handle the case when self.unit.name is not a string (e.g., a boolean)
                return str(rec.product_id.name)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_mode_id = fields.Many2one(comodel_name='payment.mode', string='Mode of Payment')
    more_is_unit = fields.Char(compute='_get_more_is_unit')
    property_owner = fields.Many2one('res.partner', string="Property Owner")
    lessor = fields.Many2one('res.partner', string="Lessor")

    def _get_more_is_unit(self):
        more_is_unit = 0
        for rec in self.order_line:
            if rec.product_id.is_unit:
                more_is_unit = more_is_unit + 1
        if more_is_unit > 1:
            self.more_is_unit = "True"
        else:
            self.more_is_unit = "False"

    def get_amount_in_words(self, amount):
        text = self.currency_id.amount_to_text(amount)
        return text.title()

    def get_total_rent_percentage(self):
        for rec in self:
            if rec.rent_plan_ids:
                total_percentage = sum(plan.percentage for plan in rec.rent_plan_ids)
                return total_percentage
            else:
                return 0.0

    def get_cheque_deposit(self):
        milestone = self.env['payment.plan'].search([('is_post_cheque', '=', True)], limit=1)
        print(milestone)
        if milestone:
            security_cheque = self.env['rent.payment.plan.line'].search(
                [('milestone_id', '=', milestone.id), ('order_id', '=', self.id)])
            print(security_cheque)
            if security_cheque:
                return security_cheque.amount
            else:
                return 0
        else:
            return 0

    def get_cheque_deposit_mode(self):
        milestone = self.env['payment.plan'].search([('is_post_cheque', '=', True)], limit=1)
        print(milestone)
        payment_mode = ""
        if milestone:
            security_cheque = self.env['rent.payment.plan.line'].search(
                [('milestone_id', '=', milestone.id), ('order_id', '=', self.id)])
            print(security_cheque)
            if security_cheque:
                payment_mode = security_cheque.type
                payment_mode = payment_mode.capitalize()
        return payment_mode

    def get_property_names(self):
        property_names_list = []
        property_names_string = " "
        count = 0
        for rec in self.order_line:
            if rec.product_id.is_unit:
                count = count + 1
                print(rec.product_id)
        if count > 1:
            for order_line in self.order_line:
                if order_line.product_id.is_unit and order_line.is_ejari and not order_line.is_debit:
                    if isinstance(order_line.product_id.name, str):
                        property_no = order_line.product_id.name.split('-')
                        property_names_list.append(property_no[-1] if property_no else order_line.unit.name)
                    else:
                        # Handle the case when order_line.unit.name is not a string (e.g., a boolean)
                        property_names_list.append(str(order_line.product_id.name))
            property_names_string = "Property No:" + ", ".join(property_names_list)
        return property_names_string

    def get_is_unit_order_total_without_tax(self):
        amount_total_without_tax = 0.0
        if all(record.product_id.is_unit for record in self.order_line if not record.product_id.is_ejari):
            for rec in self.order_line:
                if not rec.is_debit and rec.is_ejari:
                    amount_total_without_tax += (rec.price_unit * rec.product_uom_qty)
        # Formatting the amount with commas for thousands separators and two decimal places
        formatted_amount = "{:,.2f}".format(amount_total_without_tax)
        return formatted_amount

    def get_is_unit_order_total_with_tax(self):
        amount_total_with_tax = 0.0
        if all(record.product_id.is_unit for record in self.order_line if not record.product_id.is_ejari):
            for rec in self.order_line:
                if not rec.is_debit and rec.is_ejari:
                    amount_total_with_tax = (
                                                    rec.price_unit * rec.product_uom_qty) + amount_total_with_tax + rec.price_tax
        return amount_total_with_tax

    def get_property_number(self):
        count = 0
        for rec in self.order_line:
            if rec.product_id.is_unit and not rec.is_debit and rec.is_ejari:
                count = count + 1
                print(rec.product_id)
                sub_unit = rec.product_id.unit_type_id.name
        if count > 0:
            if count == 1:
                if isinstance(self.unit.name, str):
                    property_no = self.unit.name.split('-')
                    return property_no[-1] if property_no else self.unit.name
                else:
                    # Handle the case when self.unit.name is not a string (e.g., a boolean)
                    return str(self.unit.name)
            else:
                return str(count) + "  " + str(sub_unit)
        # property_no = (self.unit.name).split('-')
        # return property_no[-1] if property_no else self.unit.name

    def get_plot_number(self):
        property_no = (self.unit.name).split('-')
        if property_no:
            return property_no[-2]
        else:
            return 0

    def get_rent_installments_available(self, milestone):
        return any(
            installment.milestone_id == milestone
            for installment in self.rent_installment_ids
        )

    def get_milestone_date(self, milestone_id):
        line = self.env['rent.installment.line'].search(
            [('milestone_id', '=', milestone_id.id), ('order_id', '=', self.id)])
        return line.pdc_payment_id.date_registered or False
        # for line in self.rent_installment_ids:
        #     if milestone_id == line.milestone_id:
        #         return line.pdc_payment_id.date_registered
        #     else:
        #         return False


class AccountMove(models.Model):
    _inherit = 'account.move'

    bank_info = fields.Many2one('account.journal', string='Bank/Cash', domain=[('type', '=', 'bank')])

    def get_vat_rate(self, line):
        if line.tax_ids:
            return line.tax_ids[0].amount
        else:
            return 0

    def get_vat_net(self, line):
        vat_rate = self.get_vat_rate(line)
        if vat_rate:
            return (self.get_vat_rate(line) / 100) * line.price_subtotal
        else:
            return 0

    def get_total_price(self, line):
        return line.price_subtotal + self.get_vat_net(line)

    def get_amount_in_words(self, amount):
        text = self.currency_id.amount_to_text(amount)
        return text.title()


class ResPartnerBankInherited(models.Model):
    _inherit = 'res.partner.bank'

    iban_number = fields.Char('IBAN Number')


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_studio_l_auth = fields.Char('l auth')


class ProductVariantsInherit(models.Model):
    _inherit = 'product.product'

    price_sqft = fields.Float('Price SQFT')
    reasonable_price = fields.Float(string='Reasonable Price', compute="calculate_reasonable_price", store=True)

    @api.depends("property_size", "price_sqft")
    def calculate_reasonable_price(self):
        for rec in self:
            rec.reasonable_price = rec.price_sqft * rec.property_size
