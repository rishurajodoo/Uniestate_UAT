# _prepare_exchange_difference_move_vals


from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    reference = fields.Many2one('payment.plan', string='Reference')
    tax_closing_show_multi_closing_warning = fields.Char()
    ref = fields.Char(
        string='Reference',
        copy=False,
        tracking=True,
        index='trigram',
        compute='_compute_ref',
        store=True,
        readonly=False
    )

    @api.depends("reference")
    def _compute_ref(self):
        for rec in self:
            if rec.reference:
                rec.ref = rec.reference.name
            else:
                rec.ref = ''


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals):
        move_line = super(AccountMoveLine, self).create(vals)
        for line in move_line:
            if move_line.move_id.move_type == 'entry':
                analytic_distribution = {}
                for rec in move_line.move_id.order_id.unit:
                    analytic_distribution.update({rec.units_analytic_account.id: 100})
                line.analytic_distribution = analytic_distribution
