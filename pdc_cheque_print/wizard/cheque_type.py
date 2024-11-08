import pdb
from odoo import fields, models, _
from odoo.exceptions import ValidationError

from num2words import num2words

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_registered = fields.Boolean()

class ChequeTypes(models.TransientModel):
    _name = "cheque.types"
    _description = "Cheque Types"

    cheque_format_id = fields.Many2one('pdc.cheque.print', string='Cheque Format',
                                       help='Cheque Print Formats')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='Payee Name')
    cheque_amount_in_words = fields.Text(string='Amount in words',
                                         help='Cheque Amount in Words')
    cheque_date = fields.Date(string='Date', help='Cheque Date')
    company_id = fields.Many2one('res.company', string="company",
                                 default=lambda self: self.env.company,
                                 help='Company Name')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id',
                                  help='Currency')
    cheque_amount = fields.Monetary(currency_field='currency_id',
                                    string='Amount', help='Amount to be paid')
    check_number = fields.Char(string='Check Number', help='Check sequence '
                                                           'Number')

    pdc_cheque_id = fields.Many2one('pdc.payment', string="PDC Cheque")

    def action_print_selected_cheque(self):
        """
        Print selected cheque format by calling template.
        """
        amount_in_words = ''
        cheque_image_str = self.cheque_format_id.cheque_image.decode('utf-8')
        amount = self.pdc_cheque_id.payment_amount
        integer_part = int(amount)
        fractional_part = int(round((amount - integer_part),2)*100)
        if integer_part and fractional_part:
            # Convert integer part to words and title case, then replace " And " with " and "
            number_in_words = num2words(integer_part).title()
            formatted_number_in_words = number_in_words.replace(" And ", " and ")
            
            # Convert fractional part to words and title case, ensuring " And " is lowercase in both parts
            fractional_in_words = num2words(fractional_part).title().replace(" And ", " and ")
            
            # Construct the amount in words with currency labels
            amount_in_words = (formatted_number_in_words + " " +
                            "," + fractional_in_words + " " +
                            self.env.company.currency_id.currency_subunit_label)
        else:
            # Handle integer part only, ensuring " And " is lowercase
            number_in_words = num2words(integer_part).title()
            formatted_number_in_words = number_in_words.replace(" And ", " and ")
            
            # Construct the amount in words with currency unit label
            amount_in_words = (formatted_number_in_words + " " +
                            self.env.company.currency_id.currency_unit_label)

        # amount_in_words now contains the formatted string with "and" in lowercase

        
        data = {
            'cheque_width': self.cheque_format_id.cheque_width,
            'cheque_height': self.cheque_format_id.cheque_height,
            'font_size': self.cheque_format_id.font_size,
            'is_account_payee': self.cheque_format_id.is_account_payee,
            'a_c_payee_top_margin': self.cheque_format_id.a_c_payee_top_margin,
            'a_c_payee_left_margin': self.cheque_format_id.a_c_payee_left_margin,
            'a_c_payee_width': self.cheque_format_id.a_c_payee_width,
            'a_c_payee_height': self.cheque_format_id.a_c_payee_height,
            'date_top_margin': self.cheque_format_id.date_top_margin,
            'date_left_margin': self.cheque_format_id.date_left_margin,
            'date_letter_spacing': self.cheque_format_id.date_letter_spacing,
            'beneficiary_top_margin': self.cheque_format_id.beneficiary_top_margin,
            'beneficiary_left_margin': self.cheque_format_id.beneficiary_left_margin,
            'amount_word_tm': self.cheque_format_id.amount_word_tm,
            'amount_word_lm': self.cheque_format_id.amount_word_lm,
            'amount_word_ls': self.cheque_format_id.amount_word_ls,
            'amount_digit_tm': self.cheque_format_id.amount_digit_tm,
            'amount_digit_lm': self.cheque_format_id.amount_digit_lm,
            'amount_digit_ls': self.cheque_format_id.amount_digit_ls,
            'partner': self.pdc_cheque_id.partner_id.name.replace("\n", ""),
            'amount_in_words': self.cheque_amount_in_words,
            'amount_in_digit': self.cheque_amount,
            'cheque_date': False,
            'print_currency': self.cheque_format_id.print_currency,
            'currency_symbol': self.env.company.currency_id.symbol,
            'amount_digit_size': self.cheque_format_id.amount_digit_size,
            'print_cheque_number': self.cheque_format_id.print_cheque_number,
            'check_number': self.check_number,
            'cheque_no_tm': self.cheque_format_id.cheque_no_tm,
            'cheque_no_lm': self.cheque_format_id.cheque_no_lm,
            'check_image': cheque_image_str if cheque_image_str else '',
            'cheque_no': self.pdc_cheque_id.cheque_no,
            'purchaser': self.pdc_cheque_id.partner_id.name.replace("\n", ""),
            'date': self.pdc_cheque_id.date_payment,
            'amount': self.pdc_cheque_id.payment_amount,
            'amount_in_wordss': amount_in_words
        }                
        return self.env.ref(
            'pdc_cheque_print.print_cheque_action').report_action(self,
                                                                  data=data)
