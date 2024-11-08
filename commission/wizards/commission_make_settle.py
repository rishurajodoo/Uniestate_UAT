# Copyright 2022 Quartile
# Copyright 2014-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models


class CommissionMakeSettle(models.TransientModel):
    _name = "commission.make.settle"
    _description = "Wizard for settling commissions"

    date_to = fields.Date("Up to", required=True, default=fields.Date.today)
    agent_ids = fields.Many2many(
        comodel_name="res.partner", domain="[('agent', '=', True)]"
    )
    settlement_type = fields.Selection(selection=[], required=True)
    can_settle = fields.Boolean(
        compute="_compute_can_settle",
        help="Technical field for improving UX when no extra *commission is installed.",
    )

    @api.depends("date_to")  # use this unrelated field to trigger the computation
    def _compute_can_settle(self):
        """Check if there's any settlement type for making the settlements."""
        self.can_settle = bool(
            self.env[self._name]._fields["settlement_type"].selection
        )

    def _get_period_start(self, agent, date_to):
        if agent.settlement == "monthly":
            return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == "biweekly":
            if date_to.day >= 16:
                return date(month=date_to.month, year=date_to.year, day=16)
            else:
                return date(month=date_to.month, year=date_to.year, day=1)
        elif agent.settlement == "quaterly":
            # Get first month of the date quarter
            month = (date_to.month - 1) // 3 * 3 + 1
            return date(month=month, year=date_to.year, day=1)
        elif agent.settlement == "semi":
            if date_to.month > 6:
                return date(month=7, year=date_to.year, day=1)
            else:
                return date(month=1, year=date_to.year, day=1)
        elif agent.settlement == "annual":
            return date(month=1, year=date_to.year, day=1)

    def _get_next_period_date(self, agent, current_date):
        if agent.settlement == "monthly":
            return current_date + relativedelta(months=1)
        elif agent.settlement == "biweekly":
            if current_date.day == 1:
                return current_date + relativedelta(days=15)
            else:
                return date(
                    month=current_date.month, year=current_date.year, day=1
                ) + relativedelta(months=1, days=-1)
        elif agent.settlement == "quaterly":
            return current_date + relativedelta(months=3)
        elif agent.settlement == "semi":
            return current_date + relativedelta(months=6)
        elif agent.settlement == "annual":
            return current_date + relativedelta(years=1)

    # def _get_settlement(self, agent, company, sett_from, sett_to):
    #     self.ensure_one()
    #     return self.env["commission.settlement"].search(
    #         [
    #             ("agent_id", "=", agent.id),
    #             ("date_from", "=", sett_from),
    #             ("date_to", "=", sett_to),
    #             ("company_id", "=", company.id),
    #             ("state", "=", "settled"),
    #             ("settlement_type", "=", self.settlement_type),
    #         ],
    #         limit=1,
    #     )

    def _prepare_settlement_vals(self, agent, company, sett_from, sett_to):
        return {
            "agent_id": agent.id,
            "date_from": sett_from,
            "date_to": sett_to,
            "company_id": company.id,
            "settlement_type": self.settlement_type,
        }

    def _prepare_settlement_line_vals(self, settlement, line):
        """Hook for returning the settlement line dictionary vals."""
        return {
            "settlement_id": settlement.id,
        }

    def _get_agent_lines(self, date_to_agent):
        """Need to be extended according to settlement_type."""
        raise NotImplementedError()

    # def action_settle(self):
    #     self.ensure_one()
    #     settlement_obj = self.env["commission.settlement"]
    #     settlement_line_obj = self.env["commission.settlement.line"]
    #     settlement_ids = []
    #     if self.agent_ids:
    #         agents = self.agent_ids
    #     else:
    #         agents = self.env["res.partner"].search([("agent", "=", True)])
    #     print(f'agents: {agents}')
    #     date_to = self.date_to
    #     for agent in agents:
    #         date_to_agent = self._get_period_start(agent, date_to)
    #         print(f'date_to_agent: {date_to_agent}')
    #         # Get non settled elements
    #         agent_lines = self._get_agent_lines(agent, date_to_agent)
    #         print(f'agent_lines: {agent_lines}')
    #         for company in agent_lines.mapped("company_id"):
    #             settlement = settlement_obj.create(
    #                 self._prepare_settlement_vals(
    #                     agent, company, self.date_from, self.date_to
    #                 )
    #             )
    #             sale_commission_ids = agent.sale_commission_ids.filtered(lambda
    #                                                                          l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled')
    #             settlement.sale_commission_ids = sale_commission_ids.ids
    #             for data in agent.sale_commission_ids.filtered(
    #                     lambda l: l.date >= self.date_from and l.date <= self.date_to and l.settlement_status == 'un_settled'):
    #                 data.settlement_status = 'settled'
    #             settlement_ids.append(settlement.id)
    #         # TODO: Do creates in batch
    #         settlement_line_obj.create(
    #             self._prepare_settlement_line_vals(settlement, line)
    #         )
    #         print(
    #             f'self._prepare_settlement_line_vals(settlement, line): {self._prepare_settlement_line_vals(settlement, line)}')
    #     # go to results
    #     if len(settlement_ids):
    #         return {
    #             "name": _("Created Settlements"),
    #             "type": "ir.actions.act_window",
    #             "views": [[False, "list"], [False, "form"]],
    #             "res_model": "commission.settlement",
    #             "domain": [["id", "in", settlement_ids]],
    #         }

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
        print(f'agents: {agents}')
        date_to = self.date_to
        for agent in agents:
            date_to_agent = self._get_period_start(agent, date_to)
            print(f'date_to_agent: {date_to_agent}')
            # Get non settled elements
            agent_lines = self._get_agent_lines(agent, date_to_agent)
            print(f'agent_lines: {agent_lines}')
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
        print("settlement_line_obj", settlement_line_obj)
        # go to results
        if len(settlement_ids):
            return {
                "name": _("Created Settlements"),
                "type": "ir.actions.act_window",
                "views": [[False, "list"], [False, "form"]],
                "res_model": "commission.settlement",
                "domain": [["id", "in", settlement_ids]],
            }
