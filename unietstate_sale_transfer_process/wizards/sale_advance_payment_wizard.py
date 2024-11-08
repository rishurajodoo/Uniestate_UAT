# due_date
from datetime import datetime, timedelta

from odoo import _, api, exceptions, fields, models


class AccountVoucherWizardPurchase(models.TransientModel):
    _inherit = "account.voucher.wizard.sale"

    due_date = fields.Date('Due Date')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        sale_order = self.env[self.env.context.get('active_model')].browse(active_id)
        if sale_order:
            project_id = sale_order.project
            due_date = datetime.today() + timedelta(days=project_id.token_money_due_days)
            if sale_order.for_sale and sale_order.project:
                if sale_order.project.sale_booking_type == 'sale_booking_fixed_amount':
                    amount = 0
                    for so_line in sale_order.order_line:
                        if so_line.product_id.is_unit:
                            amount = amount + so_line.price_total
                    res.update(
                        {
                            # "amount_advance": sale_order.project.sale_booking_amount
                            "amount_advance": amount

                        }
                    )
                elif sale_order.project.sale_booking_type == 'sale_booking_percentage':
                    if sale_order.project.sale_booking_percentage != 0:
                        unit_amount = 0
                        for so_line in sale_order.order_line:
                            if so_line.product_id.is_unit:
                                unit_amount = unit_amount + so_line.price_total
                        amount = (sale_order.project.sale_booking_percentage / 100) * unit_amount
                        res.update(
                            {
                                "amount_advance": amount
                            }
                        )
            elif sale_order.for_rent and sale_order.project:
                res.update(
                    {
                        "amount_advance": 1000
                    }
                )
            res.update(
                {
                    "due_date": due_date
                }
            )
        return res
