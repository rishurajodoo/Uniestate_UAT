from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    outstanding_invoice = fields.Float(string="Outstanding Invoice", compute='compute_not_paid_invoice', store=True)
    new_owner = fields.Many2one('res.partner', string="New Owner")
    admin_fees_due = fields.Float(string="Admin Fees Due", compute='_compute_project_percentage', store=True)

    def show_invoices(self):
        return {
            'name': _('Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('so_ids', 'in', [self.id])],
            'type': 'ir.actions.act_window',
        }

    def compute_not_paid_invoice(self):
        for rec in self:
            draft_invoice = rec.invoice_ids.filtered(lambda l: l.payment_state == 'not_paid')
            partial_posted_invoice = rec.invoice_ids.filtered(
                lambda l: l.state == 'posted' and l.payment_state == 'partial')
            if partial_posted_invoice:
                draft_invoice_amount = sum(draft_invoice.mapped('amount_residual_signed'))
                partial_invoice_amount = sum(partial_posted_invoice.mapped('amount_residual'))
                rec.outstanding_invoice = draft_invoice_amount + partial_invoice_amount
            elif draft_invoice:
                rec.outstanding_invoice = sum(draft_invoice.mapped('amount_residual_signed'))
            else:
                rec.outstanding_invoice = rec.outstanding_invoice

    @api.depends('state', 'project.admin_fees_type', 'project.percentage', 'project.fixed_amount')
    def _compute_project_percentage(self):
        for rec in self:
            if rec.project:
                if rec.project.admin_fees_type == 'percentage':
                    print("total amount of order line", rec.amount_total)
                    rec.admin_fees_due = (sum(rec.order_line.product_template_id.mapped(
                        'property_price')) * rec.project.percentage) / 100
                    # rec.admin_fees_due = (rec.amount_total * rec.project.percentage) / 100
                elif rec.project.admin_fees_type == 'fixed_amount':
                    rec.admin_fees_due = rec.project.fixed_amount
            else:
                rec.admin_fees_due = rec.admin_fees_due

    def confirm_to_cancel_draft_invoice_and_make_new_sale(self):
        if not self.new_owner:
            raise ValidationError(_("Please set the new owner field, as this step is necessary to proceed further."))
        if not self.env['ir.config_parameter'].get_param(
                'unietstate_sale_transfer_process.custom_admin_fees_product_id'):
            raise ValidationError("Please Configure the admin product in settings !!!")
        draft_invoice = self.env['account.move'].search([('so_ids', 'in', self.ids), ('state', '=', 'draft')])
        purchaser_vals = {'purchaser_id': self.id, 'purchase_individual': self.new_owner.id}
        purchaser_ids = self.env['purchaser.company'].create(purchaser_vals)
        total_price = sum(draft_invoice.invoice_line_ids.mapped('price_subtotal'))
        sale_vals = {
            'partner_id': self.partner_id.id,
            'sale_order_template_id': self.sale_order_template_id.id,
            'project': self.project.id,
            'building': self.building.id,
            'floor': self.floor.id,
            'unit': [(6, 0, self.unit.ids)],
            # 'order_lines': self.invoice_line_ids.ids,
            'purchaser_ids': purchaser_ids.ids,
            'for_sale': True,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'company_id': self.company_id.id,
            'require_signature': self.require_signature,
            'require_payment': self.require_payment,
            'client_order_ref': self.client_order_ref,
            'tag_ids': self.tag_ids.ids,
            'incoterm': self.incoterm.id,
            'incoterm_location': self.incoterm_location,
            'picking_policy': self.picking_policy,
            'commitment_date': self.commitment_date,
            'delivery_status': self.delivery_status,
            'plan_ids': self.plan_ids.ids,
            'date_order': self.date_order
        }
        sale_order_new = self.env['sale.order'].create(sale_vals)
        for invoice in draft_invoice:
            invoice.state = 'cancel'
        if self.admin_fees_due > 0:
            admin_product_id = int(
                self.env['ir.config_parameter'].get_param('unietstate_sale_transfer_process.admin_fees_product_id'))
            analytic_distribution = self.invoice_ids[0].invoice_line_ids[0].analytic_distribution
            # tax_ids = draft_invoice.invoice_line_ids[0].tax_ids.ids
            price_unit = self.admin_fees_due
            quantity = 1.0
            account_id = self.invoice_ids[0].invoice_line_ids[0].account_id.id

            invoice_line_ids = [(0, 0, {
                'product_id': admin_product_id,
                'name': "Admin Fee Charges",
                'price_unit': price_unit,
                'quantity': quantity,
                # 'tax_ids': tax_ids,
                'account_id': account_id,
                'analytic_distribution': analytic_distribution,
            })]

            inv_vals = {
                'partner_id': self.purchaser_ids[0].purchase_individual.id,
                'invoice_date': datetime.datetime.now(),
                'invoice_line_ids': invoice_line_ids,
                'move_type': 'out_invoice',
                'so_ids': self.id,
                'project': self.project.id,
                'building': self.building.id,
                'floor': self.floor.id,
                'unit': [(6, 0, self.unit.ids)],
                'state': 'draft',
            }
            invoice = self.env['account.move'].create(inv_vals)

            # move_id = self.env['account.move'].create({
            #     'partner_id': sale_order_new.partner_id.id,
            #     'invoice_date': datetime.datetime.now(),
            #     'so_ids': self.id,
            #     'invoice_line_ids': invoice_line_ids
            # })
            print("move_id.........", invoice)
            # for order_line_custom in self.order_line:

            # product_id =
            # move_lines = self.env['account.move.line'].create({
            #     'invoice_id': move_id.id,
            #
            # })

        for invoice_line in self.order_line:
            self.env['sale.order.line'].create({'order_id': sale_order_new.id,
                                                'product_id': invoice_line.product_id.id,
                                                'product_uom': invoice_line.product_uom.id,
                                                'product_uom_qty': invoice_line.product_uom_qty,
                                                'price_unit': self.outstanding_invoice,
                                                'tax_id': invoice_line.tax_id.ids,
                                                'price_subtotal': invoice_line.price_subtotal})

    # for sale in self.browse(self.id):
    #     sale.copy({
    #         'purchaser_ids': purchaser_ids.ids,
    #     })

    # purchaser_ids = self.env['purchaser.company'].create(vals)
    # sale.copy({
    #     'purchaser_ids': purchaser_ids.ids
    # })

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for unit in self.unit:
            so_amount = sum(self.order_line.filtered(lambda l: l.product_id == unit).mapped('price_unit'))
            self.env['tenancy.contract'].create({
                'project_id': self.project.id,
                'floor_id': self.floor.id,
                'unit_id': unit.ids,
                'partner_id': self.partner_id.id,
                'order_id': self.id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'building_id': self.building.id,
                'amount': so_amount,
            })
        return res
