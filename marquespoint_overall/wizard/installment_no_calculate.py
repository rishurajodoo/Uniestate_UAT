from odoo import fields, models, api, _


class MileStoneTrigger(models.TransientModel):
    _name = 'milestone.trigger'
    _description = 'Mile Stone Trigger'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    building_id = fields.Many2one('property.building', string="Building")
    unit_id = fields.Many2one('product.product', string="Unit")
    milestone_id = fields.Many2one('payment.plan', string="Milestone", required=True)
    start_date = fields.Date('Start Date', required=True)

    def action_save(self):
        domain = []

        if self.project_id:
            domain.append(('project', '=', self.project_id.id))
        if self.building_id:
            domain.append(('building', '=', self.building_id.id))
        if self.unit_id:
            domain.append(('unit', '=', self.unit_id.id))

        sale_order_ids = self.env['sale.order'].search(domain)
        for sale in sale_order_ids:
            for plan in sale.plan_ids:
                if plan.milestone_id.id == self.milestone_id.id:
                    if not plan.start_date:
                        plan.start_date = self.start_date
                    for invoice in sale.invoice_ids:
                        if invoice.reference.id == plan.milestone_id.id:
                            if not invoice.invoice_date:
                                invoice.invoice_date = self.start_date
