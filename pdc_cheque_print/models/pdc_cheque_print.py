# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field

class PDCChequePrint(models.Model):
    _name = 'pdc.cheque.print'
    _description = 'PDC Check Print'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    cheque_height = fields.Float(string='Cheque Height')
    cheque_width = fields.Float(string='Cheque Width')
    maximum_char = fields.Integer(string='Maximum Characters')
    cheque_image = fields.Image(string='Cheque Image')
    pdc_cheque_line = fields.One2many('pdc.cheque.print.format.line','pdc_cheque')

    bank_name = fields.Char(string='Bank Name',
                            help='Enter the name of the bank.',
                            required=True)
    font_size = fields.Float(string='Font Size',
                             help='Total font size for the text.')
    cheque_width = fields.Float(string='Width', help='Width of the cheque.')
    cheque_height = fields.Float(string='Height', help='Height of the cheque.')
    print_cheque_number = fields.Boolean(string='Print Cheque Number',
                                         help='Enable to print the cheque '
                                              'sequence number. '
                                              'You can adjust this if the '
                                              'numbering is incorrect.')
    cheque_no_tm = fields.Float(string='Cheque No: Top Margin',
                                help="Top margin for the cheque number.")
    cheque_no_lm = fields.Float(string='Cheque No: Left Margin',
                                help="Left margin for the cheque number.")
    is_account_payee = fields.Boolean(string="Crossed Account Payee Cheque",
                                      help="Select to make the cheque a "
                                           "Crossed Account Payee cheque. "
                                           "Prints ‘A/C Payee Only’ between "
                                           "parallel crossing lines.")
    a_c_payee_top_margin = fields.Float(string='Payee Top Margin',
                                        help="Top margin for the 'A/C Payee' "
                                             "text.")
    a_c_payee_left_margin = fields.Float(string="Payee Left Margin",
                                         help="Left margin for the 'A/C Payee'"
                                              " text.")
    a_c_payee_width = fields.Float(string="Payee Width",
                                   help="Width of the 'A/C Payee' text.")
    a_c_payee_height = fields.Float(string="Payee Height",
                                    help="Height of the 'A/C Payee' text.")
    date_remove_slashes = fields.Boolean(string="Remove Slashes",
                                         help="Enable to remove slashes from"
                                              " the date.")
    date_top_margin = fields.Float(string="Date Top Margin",
                                   help="Top margin for the date.")
    date_left_margin = fields.Float(string="Date Left Margin",
                                    help="Left margin for the date.")
    date_letter_spacing = fields.Float(string="Date Letter Spacing",
                                       help="Spacing between date characters.")
    beneficiary_top_margin = fields.Float(string="Beneficiary Top Margin",
                                          help="Top margin for the beneficiary"
                                               " name.")
    beneficiary_left_margin = fields.Float(string="Beneficiary Left Margin",
                                           help="Left margin for the "
                                                "beneficiary name.")
    amount_word_tm = fields.Float(string="Amount in Words Top Margin",
                                  help="Top margin for the amount in words.")
    amount_word_lm = fields.Float(string="Amount in Words Left Margin",
                                  help="Left margin for the amount in words.")
    amount_word_ls = fields.Float(string="Amount in Words Letter Spacing",
                                  help="Spacing between characters in the "
                                       "amount in words.")
    print_currency = fields.Boolean(string="Print Currency Symbol",
                                    help="Enable to print the currency symbol."
                                         "")
    amount_digit_tm = fields.Float(string="Amount in Digits Top Margin",
                                   help="Top margin for the amount in digits."
                                        "")
    amount_digit_lm = fields.Float(string="Amount in Digits Left Margin",
                                   help="Left margin for the amount in digits."
                                        "")
    amount_digit_ls = fields.Float(string="Amount in Digits Letter Spacing",
                                   help="Spacing between characters in the "
                                        "amount in digits.")
    amount_digit_size = fields.Float(string="Amount in Digits Font Size",
                                     help="Font size for the amount in digits"
                                          ".")
    #
    # def action_config_attribute(self):
    #     pass

class PDCChequePrintFormatLine(models.Model):
    _name = 'pdc.cheque.print.format.line'
    _description = 'PDC Check Format Line'

    name = fields.Many2one( 'ir.model.fields',
       domain=[('model_id.model', '=', 'pdc.payment')], readonly=False, store=True,string='Name')
    font_size = fields.Integer(string='Font Size')
    letter_spacing = fields.Integer(string='Letter Spacing')
    top_displacement = fields.Integer(string='Top Displacement')
    left_displacement = fields.Integer(string='Left Displacement')
    height = fields.Integer(string='Height')
    width = fields.Integer(string='Width')
    pdc_cheque = fields.Many2one('pdc.cheque.print')