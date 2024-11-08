from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date


class MaintenanceRequestInherited(models.Model):
    _inherit = 'maintenance.request'

    operation_id = fields.Many2one('maintenance.operation.type', 'Operation Type')
    unit_id = fields.Many2one('product.product', 'Unit')
    floor_id = fields.Many2one('property.floor', 'Floor')
    building_id = fields.Many2one('property.building', 'Building')
    project_id = fields.Many2one('project.project', 'Project')
    invoice_amount = fields.Float('Invoice Amount')
    actual_amount = fields.Float('Actual Amount')
    move_id = fields.Many2one('account.move', 'Invoice')
    tenancy_id = fields.Many2one('tenancy.contract', sttring='Tenancy Contract ID')
    tenancy_state = fields.Selection([
        ('new', 'New'),
        ('renew', 'Renew'),
        ('open', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Tenancy State', default='new')
    maintenance_type = fields.Selection([('corrective', 'Reactive'), ('preventive', 'Preventive')],
                                        string='Maintenance Type', default="corrective")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    petty_cash_ids = fields.Many2many('snd.petty.cash', string="Petty Cash ID's")
    is_petty = fields.Boolean('Is Petty', compute='_compute_actual_amount')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order ID', compute='_get_sale_order_id')
    is_ecr = fields.Boolean(string="IS ECR?", default=False, readonly=True)
    maintenance_category_id = fields.Many2one('maintenance.category', string='Category')

    def move_to_in_progress(self):
        new_stage = self.env['maintenance.stage'].search([('name', '=', 'In Progress')], limit=1)
        if new_stage:
            self.write({'stage_id': new_stage.id, 'all_level_approved': True})

    @api.depends('unit_id')
    def _get_sale_order_id(self):
        if self.unit_id:
            self.sale_order_id = self.unit_id.sale_order.id
        else:
            self.sale_order_id = False

    def _compute_actual_amount(self):
        for rec in self:
            petty_cash_ids = self.env['snd.petty.cash'].search([('request_id', '=', rec.id)])
            rec.actual_amount = (
                sum(pc.amount for pc in petty_cash_ids) if petty_cash_ids else 0
            )
            print(rec.actual_amount)
            print('is petty compute field')
            rec.is_petty = bool(petty_cash_ids)

    def get_actual_amount(self):
        for rec in self:
            petty_cash_ids = self.env['snd.petty.cash'].search([('request_id', '=', rec.id)])
            rec.actual_amount = (
                sum(pc.amount for pc in petty_cash_ids) if petty_cash_ids else 0
            )

    @api.onchange('unit_id')
    def on_unit_change(self):
        for rec in self:
            print('unit id onchange working')
            if not rec.is_ecr and rec.unit_id:
                rec.tenancy_id = rec.unit_id.tenancy_id
                rec.tenancy_state = rec.unit_id.tenancy_state
                rec.start_date = rec.unit_id.start_date
                rec.end_date = rec.unit_id.end_date


    def create_invoice(self):
        for rec in self:
            if rec.move_id:
                raise UserError('Invoice Already Attached on this Maintenance Request')
            else:
                inv_lines = [
                    (
                        0,
                        0,
                        {
                            'product_id': line.product_id.id,
                            'quantity': line.Qty,
                            'product_uom_id': line.product_id.uom_id.id,
                            'price_unit': line.cost,
                            'tax_ids': line.product_id.taxes_id.ids,
                        },
                    )
                    for line in self.sparepart_ids
                ]

                if self.unit_id.sale_order:
                    pass
                else:
                    raise UserError('Sale Order not Attached with Following Unit The Partner is required for Invoice')
                inv_vals = {
                    'name': '',
                    'partner_id': self.unit_id.sale_order.partner_id.id,
                    'invoice_date': date.today(),
                    'invoice_line_ids': inv_lines,
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'so_ids': self.sale_order_id.id,
                    'project': self.project_id.id,
                    'building': self.building_id.id,
                    'floor': self.floor_id.id,
                    'invoice_origin': self.name,
                    'unit': self.unit_id.ids,
                }
                invoice = self.env['account.move'].create(inv_vals)
                rec.move_id = invoice.id
            print('Invoice is Created')

    def create_petty_cash_entries(self):
        if self.env['snd.petty.cash'].search([('request_id', '=', self.id)]):
            return {
                'name': _('Petty Cash'),
                'view_mode': 'tree,form',
                'res_model': 'snd.petty.cash',
                'domain': [('request_id', '=', self.id)],
                'context': {'default_request_id': self.id,
                            'default_unit_id': self.unit_id.id,
                            'default_floor_id': self.floor_id.id,
                            'default_building_id': self.building_id.id,
                            'default_project_id': self.project_id.id,
                            'default_vendor_id': self.unit_id.sale_order.partner_id.id,
                            },
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref("snd_petty_cash.snd_petty_cash_tree").id, 'tree'),
                          (self.env.ref("snd_petty_cash.snd_petty_cash_form").id, 'form'), ]
            }
        else:
            return {
                'name': 'Petty Cash',
                'type': 'ir.actions.act_window',
                'res_model': 'snd.petty.cash',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_request_id': self.id,
                            'default_unit_id': self.unit_id.id,
                            'default_floor_id': self.floor_id.id,
                            'default_building_id': self.building_id.id,
                            'default_project_id': self.project_id.id,
                            'default_vendor_id': self.unit_id.sale_order.partner_id.id,
                            },
                'view_id': self.env.ref("snd_petty_cash.snd_petty_cash_form").id,
            }


class MaintenanceCategory(models.Model):
    _name = 'maintenance.category'
    _description = "Maintenance Category"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
