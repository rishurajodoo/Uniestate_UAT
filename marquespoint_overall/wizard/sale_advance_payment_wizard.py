from odoo import _, api, exceptions, fields, models


class AccountVoucherWizardPurchase(models.TransientModel):
    _name = "account.voucher.wizard.sale"
    _description = "Account Voucher Wizard Sale"

    order_id = fields.Many2one("sale.order", required=True)
    journal_id = fields.Many2one(
        "account.journal",
        "Journal",
        # required=True,
        domain=[("type", "in", ("bank", "cash"))],
    )
    journal_currency_id = fields.Many2one(
        "res.currency",
        "Journal Currency",
        store=True,
        readonly=False,
        compute="_compute_get_journal_currency",
    )
    currency_id = fields.Many2one("res.currency", "Currency", readonly=True)
    amount_total = fields.Monetary(readonly=True)
    amount_advance = fields.Monetary(
        "Amount advanced", required=True, currency_field="journal_currency_id"
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    currency_amount = fields.Monetary(
        "Curr. amount",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_currency_amount",
        store=True,
    )
    payment_ref = fields.Char("Ref.")
    due_date = fields.Date('Due Date')
    reference_id = fields.Many2one("payment.plan",string="Reference")

    @api.depends("journal_id")
    def _compute_get_journal_currency(self):
        for wzd in self:
            wzd.journal_currency_id = (
                    wzd.journal_id.currency_id.id or self.env.user.company_id.currency_id.id
            )

    @api.constrains("amount_advance")
    def check_amount(self):
        if self.journal_currency_id.compare_amounts(self.amount_advance, 0.0) <= 0:
            raise exceptions.ValidationError(_("Amount of advance must be positive."))
        if self.env.context.get("active_id", False):
            if (
                    self.currency_id.compare_amounts(
                        self.currency_amount, self.order_id.amount_residual
                    )
                    > 0
            ):
                raise exceptions.ValidationError(
                    _("Amount of advance is greater than residual amount on purchase")
                )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        sale_ids = self.env.context.get("active_ids", [])
        if not sale_ids:
            return res
        sale_id = fields.first(sale_ids)
        sale = self.env["sale.order"].browse(sale_id)
        if "amount_total" in fields_list:
            res.update(
                {
                    "order_id": sale.id,
                    "amount_total": sale.amount_residual,
                    "currency_id": sale.currency_id.id,
                }
            )
        return res

    @api.depends("journal_id", "date", "amount_advance")
    def _compute_currency_amount(self):
        if self.journal_currency_id != self.currency_id:
            amount_advance = self.journal_currency_id._convert(
                self.amount_advance,
                self.currency_id,
                self.order_id.company_id,
                self.date or fields.Date.today(),
            )
        else:
            amount_advance = self.amount_advance
        self.currency_amount = amount_advance

    def _prepare_payment_vals(self, sale):
        partner_id = sale.partner_id.id
        booking_id = self.env['payment.plan'].search([('is_booked', '=', True)])
        return {
            "date": self.date,
            "due_date": self.due_date,
            "amount": self.amount_advance,
            "payment_type": "inbound",
            "partner_type": "customer",
            "ref": self.payment_ref or sale.name,
            "journal_id": self.journal_id.id,
            "currency_id": self.journal_currency_id.id,
            "partner_id": partner_id,
            'state': 'draft',
            "payment_method_id": self.env.ref(
                "account.account_payment_method_manual_out"
            ).id,
        }

    def make_advance_payment(self):
        self.ensure_one()
        payment_obj = self.env["account.payment"]
        sale_obj = self.env["sale.order"]

        sale_ids = self.env.context.get("active_ids", [])
        if sale_ids:
            order_id = fields.first(sale_ids)
            sale = sale_obj.browse(order_id)
            payment_vals = self._prepare_payment_vals(sale)
            payment = payment_obj.create(payment_vals)
            sale.account_payment_ids |= payment
            # payment.action_post()
            product_name = self.order_id.partner_id.name
            print(f'product_name: {product_name}')
            product_unit = self.env['product.product'].search([('name', '=', self.order_id.partner_id.name)])
            print(product_unit)
            product_unit.state = 'reserved'

        return {
            "type": "ir.actions.act_window_close",
        }
