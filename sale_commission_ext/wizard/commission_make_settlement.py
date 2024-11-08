
from odoo import _, api, fields, models
from odoo.exceptions import  ValidationError


class CommissionMakeSettle(models.TransientModel):
    _inherit = "commission.make.settle"

    date_from = fields.Date(string='Date From', required=True)
    sale_order_domain = fields.Char(string='Order Domain', compute='_compute_sale_order_domain', store=True)
    agent_ids = fields.Many2many(
        comodel_name="res.partner",  store=True, domain="[('agent', '=', True)]"
    )
    settlement_type = fields.Selection(
        selection_add=[("sale_invoice", "Sales Invoices")],
        ondelete={"sale_invoice": "cascade"}, default='sale_invoice'
    )
    filter_agent_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_agent1_rel",
        column1="partner_id",
        column2="agent_id",domain="[('agent', '=', True)]"
    )

    def unlink(self):
        for record in self:
            print("svdhsgdhsdgshgdjs")
            record.agent_ids = [(5, 0, 0)]  # Clear the many2many field
        return super(CommissionMakeSettle, self).unlink()

    @api.onchange('filter_agent_ids')
    def _onchange_filter_agent_ids(self):
        sale_agent_ids = []
        if self.filter_agent_ids:
            for partner in self.filter_agent_ids:
                sale_agent_ids.append(partner.id)
            unique_ids = list(set(filter(lambda x: x is not False, sale_agent_ids)))
            self.agent_ids = [(6, 0, unique_ids)]

    @api.depends('date_from', 'date_to')
    def _compute_sale_order_domain(self):
        self.sale_order_domain = []
        sale_agent_ids = []
        sale_orders = self.env['sale.order'].search([('date_order', '>=', self.date_from), ('date_order', '<=', self.date_to)])
        if sale_orders:
            for rec in sale_orders:
                for partner in rec.partner_agent_ids:
                    sale_agent_ids.append(partner.id)
        unique_ids = list(set(filter(lambda x: x is not False, sale_agent_ids)))
        if sale_agent_ids:
            domain = [('id', 'in', sale_agent_ids)]
            self.agent_ids = [(6,0, unique_ids)]
            self.sale_order_domain = domain

    def action_settle(self):
        self.ensure_one()
        settlement_obj = self.env["commission.settlement"]
        settlement_line_obj = self.env["commission.settlement.line"]
        sale_commission_line_obj = self.env["sale.commission.settlement.line"]
        settlement_ids = []
        if self.agent_ids:
            agents = self.agent_ids
        else:
            agents = self.env["res.partner"].search([("agent", "=", True)])
        print(f'newwwwwwww: {self.agent_ids}')
        date_to = self.date_to
        for agent in agents:
            date_to_agent = self._get_period_start(agent, date_to)
            print(f'date_to_agent: {date_to_agent}')
            # Get non settled elements
            agent_lines = self._get_agent_lines(agent, date_to_agent)
            if not agent_lines:
                sale_commission_ids = agent.sale_commission_ids.filtered(lambda
                                                                             l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled')
                if sale_commission_ids:
                    settlement = settlement_obj.create(
                        self._prepare_settlement_vals(
                            agent, self.env.company, self.date_from, self.date_to
                        )
                    )

                    print("sale_commission_idsssss", sale_commission_ids)
                    settlement.sale_commission_ids = sale_commission_ids.ids
                    for data in agent.sale_commission_ids.filtered(
                            lambda l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled'):
                        data.settlement_status = 'settled'
                    settlement_ids.append(settlement.id)
                    commission = False
                    for commission_line in sale_commission_ids:
                        if commission_line.order_id.state == 'sale' and commission_line.order_id.commission_id:
                            commission = commission_line.order_id.commission_id.id
                            line = {
                                # "invoice_agent_line_id": commission_line.id,
                                "date": commission_line.date,
                                "commission_id": commission,
                                "settled_amount": commission_line.commission_amount,
                                "settlement_id": settlement.id
                            }
                            # TODO: Do creates in batch
                            settlement_line_obj.create(
                                line
                            )
                            sale_commission_line_obj.create({
                                'order_id': commission_line.order_id.id,
                                'commission_id': settlement.id,
                                "date": commission_line.order_id.date_order
                            })
            for company in agent_lines.mapped("company_id"):
                agent_lines_company = agent_lines.filtered(
                    lambda r: r.object_id.company_id == company
                )
                pos = 0
                while pos < len(agent_lines_company):
                    line = agent_lines_company[pos]
                    print(f'agent_lines_company: {line}')
                    pos += 1
                    settlement = settlement_obj.create(
                        self._prepare_settlement_vals(
                            agent, company, self.date_from, self.date_to
                        )
                    )
                    sale_commission_ids = agent.sale_commission_ids.filtered(lambda
                                                                                 l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled')
                    settlement.sale_commission_ids = sale_commission_ids.ids
                    for data in agent.sale_commission_ids.filtered(
                            lambda l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled'):
                        data.settlement_status = 'settled'
                    settlement_ids.append(settlement.id)
                    # TODO: Do creates in batch
                    settlement_line_obj.create(
                        self._prepare_settlement_line_vals(settlement, line=False)
                    )
        # go to results
        if len(settlement_ids):
            return {
                "name": _("Created Settlements"),
                "type": "ir.actions.act_window",
                "views": [[False, "list"], [False, "form"]],
                "res_model": "commission.settlement",
                "domain": [["id", "in", settlement_ids]],
            }




