from odoo import fields, models, api, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    cancellation_percentage = fields.Float(string='Cancellation %')
    # renewable_product_ids = fields.Many2many('product.product', 'renewal_product_rel', 'product_id', 'project_id',
    #                                          string='Renewable Product')
    early_termination_product = fields.Many2one('product.product', string='Early Termination Product')
    # maintenance_product = fields.Many2many('product.product', 'maintenance_product_rel', 'product_id', 'project_id',
    #                                        string='Maintenance Product')
    sales_booking_product = fields.Many2one('product.product', string='Sales Booking Product')
    lease_booking_product = fields.Many2one('product.product', string='Lease Booking Product')
    renewal_changes_item = fields.Many2one('product.product', string='Renewal Charges Item')
