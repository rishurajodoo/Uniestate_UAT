from odoo import fields, models, api, _


class AccountMoveInherited(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(AccountMoveInherited, self).create(vals)
        tags = []
        if res.unit:
            if res.unit.analytic_tag_id:
                tags = res.unit.analytic_tag_id.ids
            if res.building:
                if res.building.analytic_tag_id:
                    tags.append(res.building.analytic_tag_id.id)
            if res.floor:
                if res.floor.analytic_tag_id:
                    tags.append(res.floor.analytic_tag_id.id)
            if res.invoice_line_ids:
                for inv_line in res.invoice_line_ids:
                    # inv_line.analytic_tag_ids = res.unit.analytic_tag_id or None
                    inv_line.analytic_tag_ids = tags or None
                    analytic = {}
                    for rec in res.unit.units_analytic_account:
                        analytic.update({rec.id: 100})
                    # inv_line.analytic_distribution = {res.unit.units_analytic_account: 100}
                    inv_line.analytic_distribution = analytic
                    # inv_line.analytic_account_id = res.unit.units_analytic_account.id or None
            if res.line_ids:
                for line in res.line_ids:
                    # line.analytic_tag_ids = res.unit.analytic_tag_id or None
                    line.analytic_tag_ids = tags or None
                    analytic = {}
                    for rec in res.unit.units_analytic_account:
                        analytic.update({rec.id: 100})
                    line.analytic_distribution = analytic
                    # line.analytic_account_id = res.unit.units_analytic_account.id or None
        return res
