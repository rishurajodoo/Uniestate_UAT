from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Left Side
    payment_ref = fields.Char('Payment Reference')
    attendant = fields.Many2one('res.partner', 'Attendant')
    project_name = fields.Many2one('project.project', 'Project Name')
    project_shipment = fields.Char('Project Shipment')
    project_code = fields.Char('Project Code')
    po_no = fields.Char(string='PO No', compute='compute_po_no')
    po_type = fields.Selection([
        ('project', 'Project'),
        ('other', 'Other')
    ], string='PO Type')
    # Right Side
    sub_contractor = fields.Many2one('res.partner', 'Sub-Contractor')
    contract_order = fields.Char('Contract/Order')
    retention = fields.Float('Retention (%)')
    retention_amount = fields.Float('Retention Amount', compute='_compute_retention_amount')
    advance = fields.Float('Advance (%)')
    advance_amount = fields.Float('Advance Amount', compute='_compute_advance_amount')

    @api.depends('retention')
    def _compute_retention_amount(self):
        for rec in self:
            if rec.retention:
                rec.retention_amount = rec.amount_untaxed * (rec.retention / 100)
            else:
                rec.retention_amount = 0

    @api.depends('advance')
    def _compute_advance_amount(self):
        for rec in self:
            if rec.advance:
                rec.advance_amount = rec.amount_untaxed * (rec.advance / 100)
            else:
                rec.advance_amount = 0

    def _prepare_invoice(self, ):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'payment_reference': self.payment_ref,
            'attendant': self.attendant.id,
            'project_name': self.project_name.id,
            'project': self.project_name.id,
            'project_shipment': self.project_shipment,
            'project_code': self.project_code,
            'po_no': self.id,
            'po_type': self.po_type,
            'retention': self.retention,
            'retention_amount': self.retention_amount,
            'advance': self.advance,
            'advance_amount': self.advance_amount,
            'confirmation_date': self.date_approve,
            'sub_contractor': self.sub_contractor.id,
            'contract_order': self.contract_order,
        })
        return invoice_vals

    # @api.depends('project_name')
    # def _on_project_name_change(self):
    #     print('_on_project_name_change')
    #     for rec in self:
    #         if rec.project_name:

    @api.depends('order_line.invoice_lines.move_id')
    def compute_po_no(self):
        for order in self:
            invoices = order.mapped('order_line.invoice_lines.move_id')
            temp = ''
            for inv in invoices:
                temp += inv.name
                temp += ','
            order.po_no = temp.rstrip(',')

    def grand_total_in_words(self, grand_total):
        return self.currency_id.amount_to_text(grand_total)

    def get_vat_amount(self):
        vat = 0
        subtotal = 0
        for rec in self.order_line:
            vat += rec.taxes_id.amount
            subtotal += rec.price_subtotal
        avg_vat = vat / len(self.order_line)
        return subtotal * (avg_vat / 100)


class PurchaseOrderLines(models.Model):
    _inherit = 'purchase.order.line'

    contract_per_amount = fields.Char('% Contract Amount', compute='_compute_contract_per_amount')

    @api.depends('price_unit', 'product_qty', 'price_subtotal', 'order_id.amount_untaxed')
    def _compute_contract_per_amount(self):
        for rec in self:
            # print(rec.invoice_lines)
            # temp = [float(line.contract_per_amount.replace('%', '')) for line in rec.invoice_lines]
            # temp = sum(temp)
            # print(temp)
            if rec.price_unit or rec.product_qty or rec.price_subtotal or rec.order_id.amount_untaxed:
                try:
                    rec.contract_per_amount = f'{round((rec.price_subtotal / rec.order_id.amount_untaxed) * 100, 2)}%'
                except Exception:
                    rec.contract_per_amount = '0.00%'
            else:
                rec.contract_per_amount = '0.00%'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()

        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'contract_per_amount': self.contract_per_amount,
            'contract_amount': self.price_subtotal,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution

        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res
