
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for broker in res.opportunity_id.broker_id:
            commission_amount = 0
            if broker.agent_type == 'agent':
                if res.opportunity_id.for_sale:
                    commission_percent = res.opportunity_id.project_id.sale_external_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
                if res.opportunity_id.for_rent:
                    commission_percent = res.opportunity_id.project_id.rent_external_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
            elif broker.agent_type == 'agent1':
                if res.opportunity_id.for_sale:
                    commission_percent = res.opportunity_id.project_id.sale_internal_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
                if res.opportunity_id.for_rent:
                    commission_percent = res.opportunity_id.project_id.rent_internal_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
            elif broker.agent_type == 'freelance':
                if res.opportunity_id.for_sale:
                    commission_percent = res.opportunity_id.project_id.sale_freelance_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
                if res.opportunity_id.for_rent:
                    commission_percent = res.opportunity_id.project_id.rent_freelance_agent_commission.fix_qty
                    commission_amount = (commission_percent / 100) * res.opportunity_id.expected_revenue
            self.env['sale.commission.line'].create({
                'order_id': res.id,
                'date': res.date_order,
                'agent_id': broker.id,
                'commission_amount': commission_amount,
            })
            if broker.commission_id:
                commission_settlement = self.env['commission.settlement'].search([('agent_id','=',broker.id)])
                for commission in commission_settlement:
                        self.env['sale.commission.settlement.line'].create({
                            'order_id': res.id,
                            'date': res.date_order,
                            'commission_id': commission.id,
                        })
        return res
