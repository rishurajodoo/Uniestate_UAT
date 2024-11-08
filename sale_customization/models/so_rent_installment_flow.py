from email.policy import default

from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import UserError


class SalrOrderForRent(models.Model):
    _inherit = 'sale.order'

    rent_plan_ids = fields.One2many('rent.payment.plan.line', 'order_id', readonly=False)
    rent_plan_invoice_ids = fields.Many2many('payment.plan', string="Payment Rrnt", compute="compute_all_payment_rent")
    rent_payment_plan_id = fields.One2many('rent.payment.plan.line', 'order_id')
    rent_installment_ids = fields.One2many('rent.installment.line', 'order_id')
    is_deferred = fields.Boolean(compute='_is_deferred_true')
    pdc_ids = fields.One2many(comodel_name='pdc.payment', inverse_name='order_id', string='PDCs',
                              compute='_compute_pdc_ids')

    @api.constrains('order_line')
    def create_payment_plan_line(self):
        for rec in self._origin:
            ejari_amount = 0.0
            utility_amount = 0.0
            security_amount = 0.0
            renewal_amount = 0.0
            for line in rec.order_line:
                if line.price_subtotal <= 0.0:
                    raise UserError("Please set the price before the save records!")
                if line.product_id.is_ejari:
                    payment_plan_id = self.env['payment.plan'].search([('is_ejari', '=', True)])
                    rent_payment_plan_id = self.env['rent.payment.plan.line'].search(
                        [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                    if rent_payment_plan_id:
                        rent_payment_plan_id.unlink()
                    ejari_amount += line.price_subtotal
                    tax_amount = ejari_amount * line.tax_id.amount / 100
                    if payment_plan_id:
                       plan_line =  self.env['rent.payment.plan.line'].create({
                            'milestone_id': payment_plan_id.id,
                            'amount': ejari_amount,
                            'order_id': rec.id,
                            'tax_amount' : tax_amount
                        })
                       plan_line.write({
                           'percentage': (plan_line.amount / ejari_amount) * 100
                       })
                elif line.product_id.is_utility_charge:
                    payment_plan_id = self.env['payment.plan'].search([('is_utility_charge', '=', True)])
                    rent_payment_plan_id = self.env['rent.payment.plan.line'].search(
                        [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                    if rent_payment_plan_id:
                        rent_payment_plan_id.unlink()
                    utility_amount += line.price_subtotal
                    tax_amount = utility_amount * line.tax_id.amount / 100
                    if payment_plan_id:
                        plan_line = self.env['rent.payment.plan.line'].create({
                            'milestone_id': payment_plan_id.id,
                            'amount': utility_amount,
                            'order_id': rec.id,
                            'tax_amount' : tax_amount
                        })
                        plan_line.write({
                            'percentage': (plan_line.amount /utility_amount)* 100
                        })
                elif line.product_id.is_sec:
                    payment_plan_id = self.env['payment.plan'].search([('is_post_cheque', '=', True)])
                    rent_payment_plan_id = self.env['rent.payment.plan.line'].search(
                        [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                    if rent_payment_plan_id:
                        rent_payment_plan_id.unlink()
                    security_amount += line.price_subtotal
                    tax_amount = security_amount * line.tax_id.amount / 100
                    if payment_plan_id:
                        plan_line = self.env['rent.payment.plan.line'].create({
                            'milestone_id': payment_plan_id.id,
                            'amount': security_amount,
                            'order_id': rec.id,
                            'tax_amount' : tax_amount
                        })
                        plan_line.write({
                            'percentage': (plan_line.amount / security_amount) * 100
                        })
                elif line.product_id.is_renewal:
                    payment_plan_id = self.env['payment.plan'].search([('is_renewal', '=', True)])
                    rent_payment_plan_id = self.env['rent.payment.plan.line'].search(
                        [('order_id', '=', rec.id), ('milestone_id', '=', payment_plan_id.id)])
                    if rent_payment_plan_id:
                        rent_payment_plan_id.unlink()
                    renewal_amount += line.price_subtotal
                    tax_amount = renewal_amount * line.tax_id.amount / 100
                    if payment_plan_id:
                        plan_line = self.env['rent.payment.plan.line'].create({
                            'milestone_id': payment_plan_id.id,
                            'amount': renewal_amount,
                            'order_id': rec.id,
                            'tax_amount' : tax_amount
                        })
                        plan_line.write({
                            'percentage': (plan_line.amount / renewal_amount) * 100
                        })

    @api.depends('rent_plan_ids')
    def compute_all_payment_rent(self):
        for obj in self:
            all_payment_rent_ids = []
            rent_plan_ids = obj.rent_plan_ids.filtered(lambda l: l.milestone_id.is_invoice == True)
            if rent_plan_ids:
                all_payment_rent_ids = rent_plan_ids.mapped('milestone_id').ids
            obj.rent_plan_invoice_ids = [(6, 0, all_payment_rent_ids)]

    def _is_deferred_true(self):
        for rec in self:
            rec.is_deferred = bool(rec.state == 'sale' and rec.for_rent)

    def create_deferred(self):
        if self.env['account.asset'].search([('order_id', '=', self.id)]):
            return {
                'name': _('Deferred Revenues'),
                'view_mode': 'tree,form',
                'res_model': 'account.asset',
                'domain': [('order_id', '=', self.id)],
                'context': {
                    'default_name': self.unit.name,
                    'default_unit_id': [(6, 0, self.unit.ids)],
                    'default_floor_id': self.unit.floor_id.id,
                    'default_building_id': self.unit.building.id,
                    'default_project_id': self.unit.project.id,
                    'default_account_analytic_id': self.unit.units_analytic_account.id,
                    'default_order_id': self.id,
                    'default_original_value': self.amount_untaxed,
                    'default_acquisition_date': self.date_order.date(),
                    'default_method_number': 12,
                    'create': False,
                    'default_asset_type': 'sale',
                },
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref("account_deffered_revenue.view_account_deffered_revenue_tree").id, 'tree'),
                          (self.env.ref("account_deffered_revenue.view_account_deffered_revenue_form").id, 'form'), ]
            }
        else:
            return {
                'name': 'Deferred Revenues',
                'type': 'ir.actions.act_window',
                'res_model': 'account.asset',
                'view_mode': 'form',
                'view_type': 'form',
                'domain': [('asset_type', '=', 'sale')],
                'context': {
                    'default_name': self.unit.name,
                    'default_unit_id': self.unit.id,
                    'default_floor_id': self.unit.floor_id.id,
                    'default_building_id': self.unit.building.id,
                    'default_project_id': self.unit.project.id,
                    'default_account_analytic_id': self.unit.units_analytic_account.id,
                    'default_order_id': self.id,
                    'default_original_value': self.amount_untaxed,
                    'default_acquisition_date': self.date_order.date(),
                    'default_method_number': 12,
                    'asset_type': 'sale',
                    'default_asset_type': 'sale',
                    # 'create': False
                },
                'view_id': self.env.ref("account_deffered_revenue.view_account_deffered_revenue_form").id,
            }

    def create_tenancy_contract(self):
        if self.env['tenancy.contract'].search([('order_id', '=', self.id)]):
            return {
                'name': _('Tenancy Contract'),
                'view_mode': 'tree,form',
                'res_model': 'tenancy.contract',
                'domain': [('order_id', '=', self.id)],
                'context': {
                    'default_unit_id': self.unit.ids,
                    'default_floor_id': self.unit.floor_id.id,
                    'default_building_id': self.unit.building.id,
                    'default_project_id': self.unit.project.id,
                    'default_order_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'default_amount': self.amount_untaxed,
                    'create': False
                },
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'name': _('Tenancy Contract'),
                'res_model': 'tenancy.contract',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_unit_id': self.unit.ids,
                    'default_floor_id': self.unit.floor_id.id,
                    'default_building_id': self.unit.building.id,
                    'default_project_id': self.unit.project.id,
                    'default_order_id': self.id,
                    'default_start_date': self.start_date,
                    'default_end_date': self.end_date,
                    'default_partner_id': self.partner_id.id,
                    'default_amount': self.amount_untaxed,
                },
                'view_id': self.env.ref("marquespoint_overall.view_tenancy_contract_form").id,
            }

    def action_cancel(self):
        res = super(SalrOrderForRent, self).action_cancel()
        if self.for_rent and self.unit:
            self.unit.state = 'available'
            self.unit.sale_order = False
            self.unit.so_amount = 0
        return res

    def action_confirm(self):
        res = super(SalrOrderForRent, self).action_confirm()
        if self.for_rent and self.unit:
            self.unit.state = 'rented'
            self.unit.sale_order = self.id
            self.unit.so_amount = self.amount_untaxed
        if self.for_rent:
            for i in self.order_line:
                print(f"print before the changing the state of sale to confirmed=========-----------------{self.state}")
                print(f"print before the changing the state to rented=========-----------------{i.product_id.state}")
                i.product_id.state = 'rented'
                print(f"print after the changing the state to rented=========-----------------{i.product_id.state}")
                print(f"print after the changing the state of sale to confirmed=========-----------------{self.state}")
            # self.unit.state = 'rented'
            # self.unit.sale_order = self.id
            # self.unit.so_amount = self.amount_untaxed
        return res

    def show_pdcs(self):
        return {
            'name': _('PDC'),
            'res_model': 'pdc.payment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            # 'view_type': 'form',
            'domain': [('order_id', 'in', self.ids)],
            # ('move_ids', 'in', self.invoice_ids)
            'context': {}
        }

    def action_pdc_payment(self):
        selected_rent_plans = self.mapped('rent_plan_ids').filtered(lambda r: r.is_selected and r.move_id)
        total_amount = sum(selected_rent_plans.mapped('amount'))
        for rent_plan in selected_rent_plans:
            return {
                'type': 'ir.actions.act_window',
                'name': 'PDC Wizard',
                'view_id': self.env.ref('pdc_payments.view_pdc_payment_wizard_form', False).id,
                'target': 'new',
                'context': {'default_partner_id': self.partner_id.id,
                            'default_payment_amount': total_amount,
                            # 'default_date_payment': self.invoice_date_due,
                            # 'default_currency_id': self.currency_id.id,
                            # 'default_move_id': self.id,
                            'default_move_ids': [(6, 0, selected_rent_plans.move_id.ids)],
                            # 'default_memo': self.name,
                            'default_unit_id': [(6, 0, self.unit.ids)],
                            'default_floor_id': self.floor.id,
                            'default_building_id': self.building.id,
                            'default_project_id': self.project.id,
                            # 'default_pdc_type': 'received' if self.move_type == 'out_invoice' else 'sent',
                            },
                'res_model': 'pdc.payment.wizard',
                'view_mode': 'form',
            }

    def action_create_payment_plan(self):
        chiller_charge = self.env["ir.config_parameter"].sudo().get_param('marquespoint_overall.is_chiller_charges')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Plan',
            'view_id': self.env.ref('sale_customization.view_payment_plan_wizard_form', False).id,
            'target': 'new',
            'res_model': 'payment.plan.wizard',
            'view_mode': 'form',
            'context': {
                'default_chiller_charge_config': chiller_charge,
            }
        }

    @api.depends('invoice_ids')
    def _compute_pdc_ids(self):
        for rec in self:
            if rec.invoice_ids:
                pp = self.env['pdc.payment'].search([('order_id', 'in', rec.ids)])
                rec.pdc_ids = pp
            else:
                rec.pdc_ids = None

    # @api.depends('rent_plan_ids')
    # def _order_line_edit(self):
    #     for rec in self:
    #         rent_pln_id = rec.rent_plan_ids
    #         if rent_pln_id:
    #             raise ValueError("You Need to Delete Tenancy Payment Plan Records first")


# Installment Plans For Rent Applications
class RentPaymentPlanLines(models.Model):
    _name = 'rent.payment.plan.line'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    order_id = fields.Many2one('sale.order')
    milestone_ids = fields.Many2many(related="order_id.rent_plan_invoice_ids")
    percentage = fields.Float('Percentage')
    percentage_check = fields.Float('Percentage Check', compute="_compute_percentage")
    amount = fields.Float('Amount')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    pdc_payment_id = fields.Many2one('pdc.payment', string='PDC')
    tax_amount = fields.Float(string="Tax Amount")
    type = fields.Selection([
        ('cheque', 'Cheque'),
        ('cash_bank', 'Cash/Bank'),
    ], string='Payment Mode', default='cheque')
    move_id = fields.Many2one('account.move', string='Invoice')
    is_chiller_charges = fields.Boolean('Is Chiller Charge', default=False)
    chiller_charge_config = fields.Boolean('Chiller Charge Config', compute='_compute_chiller_charge')
    is_tax_include = fields.Boolean('Tax included', default=False, help='Tax will calculate only if this is checked')
    is_selected = fields.Boolean()
    is_token_money = fields.Boolean(string="Token Money")
    token_amount = fields.Float(string="Token Amount")
    is_token_created = fields.Boolean(string="Is Token Created", default=False)
    state = fields.Selection(related="order_id.state")

    @api.depends('amount')
    def _compute_percentage(self):
        ejari_amount = 0.0
        utility_charge_amount = 0.0
        renewal_charge_amount = 0.0
        for rec in self:
            for order in rec.order_id:
                for line in order.order_line:
                    if line.product_id.is_ejari and rec.milestone_id.is_ejari:
                        ejari_amount += line.price_subtotal
                        rec.percentage = (rec.amount / ejari_amount) * 100
                    elif line.product_id.is_utility_charge and rec.milestone_id.is_utility_charge:
                        utility_charge_amount += line.price_subtotal
                        rec.percentage = (rec.amount / utility_charge_amount) * 100
                    elif line.product_id.is_renewal and rec.milestone_id.is_renewal:
                        renewal_charge_amount += line.price_subtotal
                        rec.percentage = (rec.amount / renewal_charge_amount) * 100
            rec.percentage_check = 0.0

    def _compute_chiller_charge(self):
        for rec in self:
            chiller_charge = self.env["ir.config_parameter"].sudo().get_param('marquespoint_overall.is_chiller_charges')
            rec.chiller_charge_config = chiller_charge

    @api.constrains('is_token_money')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.is_token_money:
                if self.search(
                        [('id', '!=', rec.id), ('order_id', '=', rec.order_id.id), ('is_token_money', '=', True)]):
                    raise UserError("You Can't be able to select token money from the same order")

    # no_of_cheques = fields.Integer('Total Cheques')

    def open_rent_payment_plan_wizard(self):
        order_line = self.order_id.order_line
        price_unit = 0.0
        for line in order_line:
            if self.milestone_id.is_renewal and line.product_id.is_renewal:
                price_unit += line.price_subtotal
            elif self.milestone_id.is_post_cheque and line.product_id.is_sec:
                price_unit += line.price_subtotal
            elif self.milestone_id.is_ejari and line.product_id.is_ejari:
                price_unit += line.price_subtotal
            elif self.milestone_id.is_utility_charge and line.product_id.is_utility_charge:
                price_unit += line.price_subtotal
        chiller_charge = self.env["ir.config_parameter"].sudo().get_param('marquespoint_overall.is_chiller_charges')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Rent Installment Lines',
            'view_id': self.env.ref('sale_customization.view_rent_installment_wizard_form', False).id,

            'context': {
                'default_milestone_id': self.milestone_id.id,
                'default_order_id': self.order_id.id,
                'default_percentage': self.milestone_id.percentage,
                'default_is_post_cheque': self.milestone_id.is_post_cheque,
                'default_is_booked': self.milestone_id.is_booked,
                'default_chiller_charge_config': chiller_charge,
                'default_amount': price_unit
            },
            'target': 'new',
            'res_model': 'rent.installment.wizard',
            'view_mode': 'form',
        }

        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Create Rent Installment Lines',
        #     'view_id': self.env.ref('sale_customization.view_rent_installment_wizard_form', False).id,
        #     'context': {
        #         'default_milestone_id': self.milestone_id.id,
        #         'default_order_id': self.order_id.id,
        #         'default_percentage': self.milestone_id.percentage,
        #         'default_is_post_cheque': self.milestone_id.is_post_cheque,
        #         'default_is_booked': self.milestone_id.is_booked,
        #         'default_chiller_charge_config': chiller_charge,
        #     },
        #     'target': 'new',
        #     'res_model': 'rent.installment.wizard',
        #     'view_mode': 'form',
        # }

    def action_pdc_payment_wizard(self, vals=False):
        return {
            'type': 'ir.actions.act_window',
            'name': 'PDC Wizard',
            'view_id': self.env.ref('sale_customization.view_pdc_sale_wizard_form', False).id,
            'target': 'new',
            'context': {'default_partner_id': self.order_id.partner_id.id,
                        'default_payment_amount': self.amount + self.tax_amount,
                        # 'default_date_payment': self.invoice_date_due,
                        'default_date_payment': self.start_date,
                        'default_date_registered': self.start_date,
                        'default_currency_id': self.order_id.currency_id.id,
                        # 'default_move_id': self.id,
                        # 'default_move_ids': [self.id],
                        # 'default_memo': self.name,
                        'default_pdc_type': 'received',
                        'default_unit_id': self.order_id.unit.id,
                        'default_floor_id': self.order_id.floor.id,
                        'default_building_id': self.order_id.building.id,
                        'default_project_id': self.order_id.project.id,
                        },
            'res_model': 'pdc.sale.wizard',
            'view_mode': 'form',
        }

    # def make_line(self):
    #     return
    # def make_line(self):
    #     vals = {
    #         'milestone_id': self.milestone_id.id,
    #         # 'amount': self.amount / self.no_of_cheques,
    #         'order_id': self.order_id.id,
    #         # 'date': inv_date
    #     }
    #     self.env['rent.installment.line'].create(vals)

    def unlink(self):
        for rec in self:
            self.env['rent.installment.line'].search(
                [('milestone_id', '=', rec.milestone_id.id), ('order_id', '=', rec.order_id.id)]).unlink()
        return super(RentPaymentPlanLines, self).unlink()

    def create_inv(self):
        for installment in self:
            if installment.move_id:
                raise UserError('Invoice Already Attached')
            # if installment.milestone_id.is_post_cheque:
            #     raise UserError('Unable to create Invoice for "Security Cheque"')
            if installment.order_id.order_line:
                inv_lines = []

                product_list_for_count = []
                product_list = []
                inv_lines = []
                length_of_unique_product_names = set()
                price_unitvar = 0.0
                # price_unitvar=0
                print(
                    f"value in order line lenght---------------before loop----------------------------------------------{length_of_unique_product_names}")
                for line in installment.order_id.order_line:
                    if line.product_id.is_unit:
                        print(
                            f"value in order line lenght---------------in else ---------------------------------------------------------------{length_of_unique_product_names}")
                        # order_line_length = order_line_length+1
                        length_of_unique_product_names.add(line.product_id.id)
                order_line_length = len(length_of_unique_product_names)
                print(
                    f"value in order line lenght---------------Last ---------------------------------------------------------------{order_line_length}")
                price_unitvar = float(installment.amount / order_line_length)
                for line in installment.order_id.order_line:

                    if line.product_id.name in product_list:
                        continue
                    else:

                        if line.product_id.is_unit == True and line.is_debit == False and installment.milestone_id.is_post_cheque == False and installment.milestone_id.is_ejari == False and installment.milestone_id.is_debit == False and installment.milestone_id.is_utility_charge == False and installment.milestone_id.is_renewal == False and installment.milestone_id.is_chiller_charges == False:
                            # for plan in installment.order_id.plan_ids:
                            price_unit = float(line.price_subtotal * (installment.percentage / 100))
                            print(
                                f"value in order line lenght---------------in creating invoice line ---------------------------------------------------------------{order_line_length}")
                            # price_unitvar = installment.amount

                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------ist----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': price_unitvar,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    'analytic_distribution': {
                                        line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_unit == True and line.is_debit == False and installment.milestone_id.is_post_cheque == False and installment.milestone_id.is_ejari == False and installment.milestone_id.is_debit == False and installment.milestone_id.is_utility_charge == False and installment.milestone_id.is_renewal == False and installment.milestone_id.is_chiller_charges == False:
                            print(
                                f"value in order line lenght---------------in creating invoice line second---------------------------------------------------------------{order_line_length}")
                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------2nd----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    # 'price_unit': installment.amount,
                                    'price_unit': line.price_subtotal,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_unit == True and line.is_debit == True and installment.milestone_id.is_debit == True and installment.milestone_id.is_post_cheque == False and installment.milestone_id.is_ejari == False and installment.milestone_id.is_utility_charge == False and installment.milestone_id.is_renewal == False and installment.milestone_id.is_chiller_charges == False:
                            print(
                                f"value in order line lenght---------------in creating invoice line third---------------------------------------------------------------{order_line_length}")
                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------3rd----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': price_unitvar,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_sec == True and installment.milestone_id.is_post_cheque == True:
                            print(
                                f"value in order line lenght---------------in creating invoice line 4th---------------------------------------------------------------{order_line_length}")
                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------4th----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': line.price_subtotal,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_ejari == True and installment.milestone_id.is_ejari == True:
                            print(
                                f"value in order line lenght---------------in creating invoice line 5th---------------------------------------------------------------{order_line_length}")
                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------5th----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    # 'price_unit': installment.amount,
                                    'price_unit': line.price_subtotal,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_renewal == True and installment.milestone_id.is_renewal == True:
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    # 'price_unit': installment.amount,
                                    'price_unit': line.price_subtotal,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif line.product_id.is_utility_charge == True and installment.milestone_id.is_utility_charge == True:
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': line.price_subtotal,
                                    'tax_ids': line.tax_id,
                                    'commission_status': line.commission_status,
                                    'analytic_distribution': {line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    # 'analytic_distribution': line.order_id.analytic_account_id.id or False,
                                    'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        if line.product_id.is_chiller_charges == True and installment.is_chiller_charges == True and installment.milestone_id.is_invoice == True:
                            price_unit = float(line.price_subtotal * (installment.percentage / 100))
                            print(
                                f"value in order line lenght---------------in creating invoice line ---------------------------------------------------------------{order_line_length}")
                            # price_unitvar = installment.amount

                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------ist----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': price_unit,
                                    'commission_status': line.commission_status,
                                    'tax_ids': line.tax_id,
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    'analytic_distribution': {
                                        line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                        elif installment.milestone_id.is_invoice == False and line.product_id.is_chiller_charges == True and installment.is_chiller_charges == True:
                            # price_unit = float(line.price_unit * (installment.percentage / 100))
                            print(
                                f"value in order line lenght---------------in creating invoice line ---------------------------------------------------------------{order_line_length}")
                            # price_unitvar = installment.amount

                            print(
                                f"prince unit -----{price_unitvar}---------------installment amount in wizard---{price_unitvar}-----------ist----------------------------------------------------{order_line_length}")
                            inv_lines.append((
                                0,
                                0,
                                {
                                    'product_id': line.product_id.id,
                                    # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                    'name': line.name + f' Period: {installment.start_date if installment.start_date else installment.order_id.start_date} - {installment.end_date if installment.end_date else installment.order_id.end_date}',
                                    'quantity': line.product_uom_qty,
                                    'product_uom_id': line.product_uom.id,
                                    'price_unit': price_unitvar,
                                    'commission_status': line.commission_status,
                                    'tax_ids': line.tax_id,
                                    # 'analytic_account_id': line.product_id.units_analytic_account,
                                    'analytic_distribution': {
                                        line.product_id.units_analytic_account.id: 100 or False},
                                    # 'analytic_tag_ids': line.product_id.analytic_tag_id,
                                    'sale_line_ids': line,
                                },
                            ))
                inv_vals = {
                    'reference': installment.milestone_id.id,
                    'partner_id': installment.order_id.partner_id.id,
                    'invoice_date': installment.start_date or date.today(),
                    # 'invoice_date_due': date.today(),
                    'invoice_date_due': installment.start_date or date.today(),
                    'invoice_payment_term_id': installment.order_id.payment_term_id.id,
                    'invoice_line_ids': inv_lines,
                    'move_type': 'out_invoice',
                    'so_ids': installment.order_id.id,
                    'state': 'draft',
                    'project': installment.order_id.project.id,
                    'building': installment.order_id.building.id,
                    'floor': installment.order_id.floor.id,
                    'unit': installment.order_id.unit.ids,
                    'invoice_origin': installment.order_id.name,
                    # 'unit': installment.order_id.unit.id,
                }
                invoice = self.env['account.move'].create(inv_vals)
                print(invoice)
                installment.move_id = invoice.id

    # def create_inv(self):
    #     for installment in self:
    #         if installment.move_id:
    #             raise UserError('Invoice Already Attached')
    #         # if installment.milestone_id.is_post_cheque:
    #         #     raise UserError('Unable to create Invoice for "Security Cheque"')
    #         if installment.order_id.order_line:
    #             inv_lines = []
    #             for line in installment.order_id.order_line:
    #                 inv_lines.append((
    #                     0,
    #                     0,
    #                     {
    #                         'product_id': line.product_id.id,
    #                         'name': line.name + f' Period: {installment.order_id.start_date} - {installment.order_id.end_date}',
    #                         'quantity': line.product_uom_qty,
    #                         'product_uom_id': line.product_uom.id,
    #                         'price_unit': installment.amount,
    #                         'tax_ids': line.tax_id,
    #                         'analytic_account_id': line.product_id.units_analytic_account,
    #                         'analytic_tag_ids': line.product_id.analytic_tag_id,
    #                         'sale_line_ids': line,
    #                     },
    #                 ))
    #             inv_vals = {
    #                 'partner_id': installment.order_id.partner_id.id,
    #                 'invoice_date': installment.start_date or date.today(),
    #                 'invoice_date_due': date.today(),
    #                 'invoice_line_ids': inv_lines,
    #                 'move_type': 'out_invoice',
    #                 'so_ids': installment.order_id.id,
    #                 'state': 'draft',
    #                 'project': installment.order_id.project.id,
    #                 'building': installment.order_id.building.id,
    #                 'floor': installment.order_id.floor.id,
    #                 'invoice_origin': installment.order_id.name,
    #                 'unit': installment.order_id.unit.id,
    #             }
    #             invoice = self.env['account.move'].create(inv_vals)
    #             print(invoice)
    #             installment.move_id = invoice.id


class RentInstallmentLines(models.Model):
    _name = 'rent.installment.line'

    milestone_id = fields.Many2one('payment.plan', string='Milestone')
    amount = fields.Float('Amount', compute='_compute_amount', readonly=False)
    move_id = fields.Many2one('account.move', string='Invoice')
    invoice_date = fields.Date('Inv Date', related='move_id.invoice_date')
    invoice_payment_date = fields.Date('Payment Due Date', compute="_compute_payment_date")
    invoice_status = fields.Char(compute='_compute_invoice_status', string='Inv Status')
    inv_status = fields.Selection(related='move_id.state')
    payment_status = fields.Char(compute='_compute_payment_status', string='Payment Status')
    pymt_status = fields.Selection(related='move_id.payment_state')
    order_id = fields.Many2one('sale.order')
    date = fields.Date('Date')
    pdc_payment_id = fields.Many2one('pdc.payment', string='PDC')
    pdc_state = fields.Selection(related='pdc_payment_id.state')

    @api.depends('move_id')
    def _compute_payment_date(self):
        for rec in self:
            if rec.move_id:
                print(self.env['account.payment'].search([('ref', '=', rec.move_id.name)]))
                payments = self.env['account.payment'].search([('ref', '=', rec.move_id.name)])
                if payments:
                    rec.invoice_payment_date = payments[-1].date
                else:
                    rec.invoice_payment_date = False
            else:
                rec.invoice_payment_date = False

    @api.depends('inv_status')
    def _compute_invoice_status(self):
        for rec in self:
            if rec.inv_status:
                print(dict(self.fields_get(allfields=['inv_status'])['inv_status']['selection'])[rec.inv_status])
                # print(dict(self._fields['move_id.state'].selection).get(self.move_id.state))
                rec.invoice_status = dict(self.fields_get(allfields=['inv_status'])['inv_status']['selection'])[
                    rec.inv_status]
            else:
                rec.invoice_status = ''

    @api.depends('pymt_status')
    def _compute_payment_status(self):
        for rec in self:
            if rec.pymt_status:
                rec.payment_status = dict(self.fields_get(allfields=['pymt_status'])['pymt_status']['selection'])[
                    rec.pymt_status]
            else:
                rec.payment_status = ''

    def _compute_amount(self):
        for rec in self:
            if rec.order_id.rent_plan_ids:
                for plan in rec.order_id.rent_plan_ids:
                    if plan.milestone_id == rec.milestone_id:
                        # rec.amount = plan.amount / plan.no_of_cheques
                        rec.amount = plan.amount
                        break
                    else:
                        rec.amount = 0
            else:
                rec.amount = 0

    def unlink(self):
        if self.move_id:
            self.move_id.unlink()
        if self.pdc_payment_id:
            self.pdc_payment_id.unlink()
        return super(RentInstallmentLines, self).unlink()

    # def create_inv(self):
    #     for installment in self:
    #         if installment.move_id:
    #             raise UserError('Invoice Already Attached')
    #         # if installment.milestone_id.is_post_cheque:
    #         #     raise UserError('Unable to create Invoice for "Security Cheque"')
    #         if installment.order_id.order_line:
    #             inv_lines = []
    #             for line in installment.order_id.order_line:
    #                 inv_lines.append((
    #                     0,
    #                     0,
    #                     {
    #                         'product_id': line.product_id.id,
    #                         'name': line.name + f' Period: {installment.order_id.start_date} - {installment.order_id.end_date}',
    #                         'quantity': line.product_uom_qty,
    #                         'product_uom_id': line.product_uom.id,
    #                         'price_unit': installment.amount,
    #                         'tax_ids': line.tax_id,
    #                         'analytic_account_id': line.product_id.units_analytic_account,
    #                         'analytic_tag_ids': line.product_id.analytic_tag_id,
    #                         'sale_line_ids': line,
    #                     },
    #                 ))
    #                 print(self.env['rent.payment.plan.line'].search(
    #                     [('milestone_id', '=', installment.milestone_id.id),
    #                      ('order_id', '=', installment.order_id.id)]))
    #                 print(self.env['rent.payment.plan.line'].search(
    #                     [('milestone_id', '=', installment.milestone_id.id),
    #                      ('order_id', '=', installment.order_id.id)]).start_date)
    #             inv_vals = {
    #                 'partner_id': installment.order_id.partner_id.id,
    #                 'invoice_date': self.env['rent.payment.plan.line'].search(
    #                     [('milestone_id', '=', installment.milestone_id.id),
    #                      ('order_id', '=', installment.order_id.id)]).start_date or date.today(),
    #                 'invoice_date_due': installment.pdc_payment_id.date_payment or date.today(),
    #                 'invoice_line_ids': inv_lines,
    #                 'move_type': 'out_invoice',
    #                 'so_ids': installment.order_id.id,
    #                 'state': 'draft',
    #                 'project': installment.order_id.project.id,
    #                 'building': installment.order_id.building.id,
    #                 'floor': installment.order_id.floor.id,
    #                 'invoice_origin': installment.order_id.name,
    #                 'unit': installment.order_id.unit.id,
    #             }
    #             invoice = self.env['account.move'].create(inv_vals)
    #             print(invoice)
    #             installment.move_id = invoice.id
    #             installment.pdc_payment_id.move_ids = [installment.move_id.id]
    #             installment.pdc_payment_id.move_id = installment.move_id.id
    #             for r in installment.pdc_payment_id.move_ids:
    #                 r.is_pdc_created = True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_ejari = fields.Boolean('Ejari', default=False)
    is_debit = fields.Boolean('Debit Note', default=False)
    is_renewal = fields.Boolean('Is renewal', default=False)
    is_utility_charge = fields.Boolean('Is Utility Charge', default=False)
    is_chiller_charges = fields.Boolean('Is Chiller Charge', default=False)
    chiller_charge_config = fields.Boolean('Chiller Charge Config', compute='_compute_chiller_charge')

    def _compute_chiller_charge(self):
        for rec in self:
            chiller_charge = self.env["ir.config_parameter"].sudo().get_param('marquespoint_overall.is_chiller_charges')
            rec.chiller_charge_config = chiller_charge

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.product_id:
            res.analytic_tag_ids = res.product_id.analytic_tag_id
        return res
