from odoo import api, fields, models, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    admin_fees_type = fields.Selection([
        ('percentage', '%'),
        ('fixed_amount', 'Fixed Amount')], string='Admin/Transfer Fees Type')
    percentage = fields.Float(string="Percentage")
    fixed_amount = fields.Float(string="Fixed Amount")
    token_money_due_days = fields.Integer(string=" Token Money due days")

    renewal_charges = fields.Selection([
        ('renewal_percentage', '%'),
        ('renewal_fixed_amount', 'Fixed Amount')], string='Renewal Charges')
    renewal_percentage = fields.Float(string="Renewal Percentage")
    renewal_fixed_amount = fields.Float(string="Renewal Fixed Amount")
    sale_booking_type = fields.Selection([
        ('sale_booking_percentage', '%'),
        ('sale_booking_fixed_amount', 'Fixed Amount')], string='Sale Booking Type')
    sale_booking_percentage = fields.Float(string="Sale Booking Percentage")
    sale_booking_amount = fields.Float(string="Sale Booking Fixed Amount")

    @api.onchange('admin_fees_type')
    def onchange_admin_fees_type(self):
        for rec in self._origin:
            sale_ids = self.env['sale.order'].search([('project_id', '=', rec.id)])
            for sale_id in sale_ids:
                if rec.admin_fees_type == 'percentage':
                    sale_id.admin_fees_due = (sale_id.tax_totals * rec.project_id.percentage) / 100
                elif rec.admin_fees_type == 'fixed_amount':
                    sale_id.admin_fees_due = rec.project_id.fixed_amount
