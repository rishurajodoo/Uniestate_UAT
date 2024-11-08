import datetime
from email.policy import default
from pyexpat import model
from re import U
from tokenize import String

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import base64
import requests
import datetime
from datetime import timedelta


class PurchaserCompany(models.Model):
    _name = 'purchaser.company'

    # purchase_individual = fields.Many2one(comodel_name='res.partner', string='Individual',
    #                                       domain='[("is_unit", "=", False)]')
    purchase_individual = fields.Many2one(comodel_name='res.partner', string='Individual')
    purchase_company = fields.Many2one(comodel_name='res.company', string='Company')
    purchaser_id = fields.Many2one(comodel_name='sale.order')


class AccountPayment(models.Model):
    _inherit = 'account.move'

    so_ids = fields.Many2one(comodel_name='sale.order')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_tag_ids = fields.Many2many('account.analytic.plan', string="Analytic Tag")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_tag_ids = fields.Many2many('account.analytic.plan', 'sale_order_line_analytic_rel', 'order_line_id',
                                        'line_id', string="Analytic Tag")


class OLStartDate(models.Model):
    _inherit = 'sale.order'

    purchaser_ids = fields.One2many('purchaser.company', 'purchaser_id')
    location = fields.Char(string='Location')
    for_rent = fields.Boolean(default=False)
    location_arabic = fields.Char(string='Location Arabic')
    relevent_unit_no = fields.Many2one(comodel_name='product.product', string='Relevent Unit No')
    relevent_unit_area = fields.Char(string='Relevent Unit Area')
    relevent_bays_no = fields.Char(string='Relevent Bays No')

    bank_details = fields.Many2one(comodel_name='res.bank', string='Bank Details')
    anticipated_completion_date = fields.Char(string='Anticipated Completion Date')
    permitted_use = fields.Char(string='Permitted Use')
    permitted_use_arabic = fields.Char(string='Permitted Use(Arabic)')
    late_payment_fee = fields.Char(string='Late Payment Fee')
    late_payment_arabic = fields.Char(string='Late Payment Fee(Arabic)')
    down_payment = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')],
                                    string='Down Payment',
                                    default='amount')
    down_payment_amount = fields.Integer(String="Down Payment Amount", compute='downpaymentamount')
    amount = fields.Char(String='Amount')
    payment = fields.Selection(
        [('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('byannual', 'By Annual'), ('annual', 'Annual')],
        default='monthly')
    start_date = fields.Date(String='Starting Date')
    end_date = fields.Date(String='Ending Date')
    percentage = fields.Float(String='Percentage')
    payment_duration = fields.Integer(String='Duration', default=1)
    installment_amount = fields.Integer(String='Duration', compute='installmentamount')
    installment_payable_amount = fields.Float(String='Installment Payable Amount', compute='subtractioninamount')
    project = fields.Many2one('project.project', string='Project')
    commission_id = fields.Many2one('commission', string='Commission')

    def action_confirm(self):
        res = super(OLStartDate, self).action_confirm()
        if self.for_sale and self.purchaser_ids:
            for purchaser in self.purchaser_ids:
                self.partner_id.category_id.create(
                    {'partner_ids': [self.partner_id.id], 'name': purchaser.purchase_individual.name})
        return res

    # @api.depends('amount','amount_total')
    def subtractioninamount(self):
        if self.down_payment == "amount":
            self.installment_payable_amount = self.amount_total - float(self.amount)

        else:
            var = (self.percentage * self.amount_total)
            self.installment_payable_amount = self.amount_total - var
            # print(self.installment_payable_amount)

    def installmentamount(self):
        self.installment_amount = self.installment_payable_amount / float(self.payment_duration)

    def downpaymentamount(self):
        self.down_payment_amount = self.amount_total - self.installment_payable_amount

    def create_invoice_installment(self):
        invoice_lines = []
        order = self
        so_line = self.order_line[0] if self.order_line else False
        if so_line:
            invoice_vals = {
                'ref': order.client_order_ref,
                'move_type': 'out_invoice',
                'invoice_origin': order.name,
                'invoice_user_id': order.user_id.id,
                'narration': order.note,
                'partner_id': order.partner_invoice_id.id,
                'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id._get_fiscal_position(
                    order.partner_id)).id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'currency_id': order.currency_id.id,
                'payment_reference': order.reference,
                'invoice_payment_term_id': order.payment_term_id.id,
                'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
                'team_id': order.team_id.id,
                'campaign_id': order.campaign_id.id,
                'medium_id': order.medium_id.id,
                'source_id': order.source_id.id,
                'so_ids': order.id,
                'invoice_line_ids': [(0, 0, {
                    'name': so_line.name,
                    'price_unit': order.down_payment_amount,
                    'quantity': 1.0,
                    'commission_status': so_line.commission_status,
                    'product_id': so_line.product_id.id,
                    'product_uom_id': so_line.product_uom.id,
                    'tax_ids': [(6, 0, so_line.tax_id.ids)],
                    'sale_line_ids': [(6, 0, [so_line.id])],
                    'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                    'analytic_distribution': {order.analytic_account_id.id: 100}
                    # 'analytic_account_id': order.analytic_account_id.id or False,
                    # 'subtotal_so': so_line.price_subtotal,
                })],
            }
            invoice = self.env['account.move'].with_company(order.company_id) \
                .sudo().create(invoice_vals).with_user(self.env.uid)

    @api.model
    def create(self, vals):
        res = super(OLStartDate, self).create(vals)
        if res.opportunity_id.unit_id == res.unit:
            print("res.opportunity_id.broker_id Created", res.opportunity_id.broker_id)
            # broker_id = [
            # (0, 0, {'agent_id': res.opportunity_id.broker_id.id, "commission_id": res.opportunity_id.broker_id.commission_id.id, 'object_id': res.order_line[0].id})]
            try:
                broker_id = []

                for x in res.opportunity_id.broker_id:
                    commission = None
                    if x.agent_type == 'agent':
                        if res.for_sale:
                            commission = res.project.sale_external_agent_commission
                        elif res.for_rent:
                            commission = res.project.rent_external_agent_commission
                    elif x.agent_type == 'agent1':
                        if res.for_sale:
                            commission = res.project.sale_internal_agent_commission
                        elif res.for_rent:
                            commission = res.project.rent_internal_agent_commission
                    if commission:
                        res.commission_id = commission.id
                        broker_id.append((0, 0, {
                            'agent_id': x.id,
                            'commission_id': commission.id,
                            'object_id': res.order_line[0].id
                        }))

                res.order_line[0].agent_ids = broker_id
            except Exception:
                print("Error Line not found")
        return res


class ContactInherit(models.Model):
    _inherit = 'res.partner'

    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    passport_eng = fields.Char(string='Passport (English)')
    passport_arabic = fields.Char(string='Passport (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic = fields.Char(String="Street (Arabic)")
    street2_arabic = fields.Char(String="street2 (Arabic)")
    zip_arabic = fields.Char(String="Zip(Arabic)")
    city_arabic = fields.Char(String="City (Arabic)")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')
    emirates_id = fields.Char('Emirates ID')
    trade_licence_no = fields.Char('Trade License No.')
    mol_id = fields.Char('MOL ID')

    # licensing_aut = fields.Char(string='Licensing Authority')

    @api.constrains('passport_eng')
    def _check_unique_passport_eng(self):
        for record in self:
            if record.passport_eng:
                existing = self.search([('passport_eng', '=', record.passport_eng), ('id', '!=', record.id)])
                if existing:
                    raise ValidationError("Passport Number already exists!")

    @api.constrains('emirates_id')
    def _check_unique_emirates_id(self):
        for record in self:
            if record.emirates_id:
                existing = self.search([('emirates_id', '=', record.emirates_id), ('id', '!=', record.id)])
                if existing:
                    raise ValidationError("Emirates ID already exists!")

    @api.constrains('vat')
    def _check_unique_vat(self):
        for record in self:
            if record.vat:
                existing = self.search([('vat', '=', record.vat), ('id', '!=', record.id)])
                if existing:
                    raise ValidationError("VAT number already exists!")

    @api.constrains('name')
    def create_tags_based_on_name(self):
        for rec in self:
            rec.category_id.create({'partner_ids': [rec.id], 'name': rec.name})


class ContactInheritInCompany(models.Model):
    _inherit = 'res.company'

    name_arabic = fields.Char('Arabic Name')
    country_arabic = fields.Many2one(comodel_name='res.country', string='Nationality (Arabic)')
    fax_eng = fields.Char(string='Fax No (English)')
    fax_arabic = fields.Char(string='Fax No (Arabic)')
    street_arabic = fields.Char(String="Street (Arabic)")
    street2_arabic = fields.Char(String="street2 (Arabic)")
    zip_arabic = fields.Char(String="Zip(Arabic)")
    city_arabic = fields.Char(String="City (Arabic)")
    state_id_arabic = fields.Many2one(comodel_name='res.country.state', string='State')
    emirates_id = fields.Char('Emirates ID')
    mol_id = fields.Char('MOL ID')


class inheritanceinbank(models.Model):
    _inherit = 'res.bank'

    account_no = fields.Char(String='Account Number')
    account_name = fields.Char(String='Account Name')
    IBAN = fields.Char(String='IBAN')
    swift = fields.Char(String='SWIFT')
