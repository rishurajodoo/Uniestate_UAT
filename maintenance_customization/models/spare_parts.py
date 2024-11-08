import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
from lxml import etree
# from odoo.addons.base_addons.hr_maintenance.models.maintenance_equipment import MaintenanceEquipment as OriginalMaintenanceEquipment

# import json
from odoo.osv import expression


class CheckList(models.Model):
    _name = 'check.list'

    _description = 'CheckList model'
    maintenance_equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    description = fields.Char(string="Description")
    temperature = fields.Char(string="Temperature")
    pr_bar = fields.Char(string="PR(BAR)")
    remarks = fields.Char(string="Remarks")
    ohter_infor = fields.Char(string="Other Info")
    state = fields.Selection(
        [('draft', 'Draft'), ('on_hold', 'ON Hold'), ('progress', 'Progress'), ('completed', 'Completed'), ],
        string='Status', default='draft')


class SpareParts(models.Model):
    _name = 'spare.parts'
    # sequence = fields.Char(string="Sequence", readonly=True, default=lambda self:_('New'))
    _description = 'SpareParts model'
    product_id = fields.Many2one('product.product', string='Product')
    from_location_id = fields.Many2one('stock.location', related="maintenance_request_id.component_location_id",
                                       store=True, string='From')
    to_location_id = fields.Many2one('stock.location', related="maintenance_request_id.component_destination_id",
                                     store=True, string='To')
    Qty = fields.Float(string='Quantity')
    act_Qty = fields.Float(string='Act Qtu', compute="compute_act_Qty")
    cost = fields.Float(string="cost", related="product_id.lst_price", store=True, readonly=False)
    total_cost = fields.Float(string="Total Cost", compute="compute_total_cost")
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    uom_id = fields.Many2one('uom.uom', store=True, string='Unit of Measure', related="product_id.uom_id", )

    def compute_act_Qty(self):
        for rec in self:
            rec.act_Qty = rec.Qty

    def compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.Qty * rec.cost

    def open_corresponding_move(self):
        return {
            'name': _('Moved Item'),
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            # tree,
            'context': {},
            'domain': [('name', '=', self.maintenance_request_id.name), ('product_id', '=', self.product_id.id),
                       ('location_id', '=', self.from_location_id.id),
                       ('location_dest_id', '=', self.to_location_id.id), ('state', '=', 'done'), ],
            # ('order_id', '=', rec.order_id.id)
            # ('asset_id', '=', self.id), ('name', '=', self.name)
            'target': 'current',
            'type': 'ir.actions.act_window',
        }


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _description = "Maintenance Request is inherited"
    # _inherits = {'maintenance.request': 'employee_id'}

    # @api.returns('self')
    # def _default_employee_get(self):
    #     return self.env.user.employee_id
    # employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_get)
    # owner_user_id = fields.Many2one(compute='_compute_owner', store=True)
    # equipment_id = fields.Many2one(domain="['|', ('employee_id', '=', employee_id), ('employee_id', '=', False)]")
    # picking_type_id = fields.Many2one(
    # 'stock.picking.type', required=True,
    # string='Operation Type',
    # default=lambda self: self.env['stock.picking.type'].browse(122))
    picking_type_id = fields.Many2one(
        'stock.picking.type', required=True,
        string='Operation Type')
    total_check_list_no = fields.Integer("Total Check List No", compute='_compute_checklist_stats', store=True)
    completed_row = fields.Integer("Completed Rows", compute='_compute_checklist_stats', store=True)
    draft_row = fields.Integer("Draft Rows", compute='_compute_checklist_stats', store=True)
    component_location_id = fields.Many2one(
        'stock.location'
        , compute="_compute_location_id",
        string='From Location'
    )

    component_destination_id = fields.Many2one('stock.location', string='To Location', )
    state = fields.Selection([('draft', 'Draft'), ('Repaired', 'Repaired'), ], string='Status', readonly=True,
                             store=True, default='draft')

    sparepart_ids = fields.One2many('spare.parts', 'maintenance_request_id', string='Spare Parts')
    checklist_ids = fields.One2many('check.list', 'maintenance_request_id', string='Check List')
    checklist = fields.Boolean(string='Checklist')

    # @api.onchange('picking_type_id')
    # def _compute_location_id(self):
    #     print(f"--------------------------------------------------------------------------------------------------------------------")
    #     for picking in self:
    #         if picking.id:  # Check if the record has an ID
    #             print(f"--------------------------------------------------------------------------------------------------------------------second time vala")
    #             picking = picking.with_company(picking.company_id)
    #             if picking.picking_type_id:
    #                 if picking.picking_type_id.default_location_src_id:
    #                     location_id = picking.picking_type_id.default_location_src_id.id
    #                     picking.component_location_id = location_id
    @api.depends('checklist_ids', 'checklist_ids.state')
    def _compute_checklist_stats(self):
        for record in self:
            if record.checklist_ids:
                total_check_list_no = len(record.checklist_ids)
                # completed_row = record.checklist_ids.search_count([('state','=','completed')])
                # draft_row = record.checklist_ids.search_count([])
                # print(f"total checks----------{total_check_list_no}---------total completed----{completed_row}-----total draft----{draft_row}")
                record.total_check_list_no = ((len(record.checklist_ids)) / total_check_list_no) * 100
                record.completed_row = (len(record.checklist_ids.filtered(
                    lambda r: r.state == 'completed')) / total_check_list_no) * 100
                record.draft_row = (len(record.checklist_ids.filtered(
                    lambda r: r.state == 'draft')) * 100) / total_check_list_no

    @api.depends('picking_type_id')
    def _compute_location_id(self):
        for picking in self:
            picking = picking.with_company(picking.company_id)
            if not picking.component_location_id and picking.picking_type_id:
                if picking.picking_type_id.default_location_src_id:
                    picking.component_location_id = picking.picking_type_id.default_location_src_id.id

            if not picking.component_destination_id and picking.picking_type_id:
                if picking.picking_type_id.default_location_dest_id:
                    picking.component_destination_id = picking.picking_type_id.default_location_dest_id.id

    @api.onchange('component_location_id')
    def _onchange_component_location_id(self):
        if self.component_location_id and self.picking_type_id.default_location_src_id:
            self.picking_type_id.default_location_src_id = self.component_location_id

    @api.onchange('component_destination_id')
    def _onchange_component_destination_id(self):
        if self.component_destination_id and self.picking_type_id.default_location_dest_id:
            self.picking_type_id.default_location_dest_id = self.component_destination_id

    # def in_new_requestToprogress(self):
    #     if self.stage_id.name == 'New Request':
    #         # Change the stage to "Repaired"
    #         new_stage = self.env['maintenance.stage'].search([('name', '=', 'In Progress')], limit=1)
    #         if new_stage:
    #             self.write({'stage_id': new_stage.id})
    #             self.state = 'draft'

    def move_to_next_stage(self):
        if self.stage_id.name == 'Repaired':
            # Change the stage to "Repaired"
            new_stage = self.env['maintenance.stage'].search([('name', '=', 'Repaired')], limit=1)
            if new_stage:
                self.write({'stage_id': new_stage.id})
                # self.state = 'Repaired'
                tranfers_obj = self.env['stock.picking']

                move_ids = []

                for spare_part in self.sparepart_ids:
                    stock_move = self.env['stock.move'].search([('spare_part_id', '=', spare_part.id)])
                    if not stock_move:
                        move_ids.append((
                            0,
                            0,
                            {
                                'product_id': spare_part.product_id.id,
                                'spare_part_id': spare_part.id,
                                # 'name': line.name + f' Period: {installment.start_date} - {installment.end_date}',
                                'quantity': spare_part.act_Qty,
                                # 'date': fields.Datetime.now(),
                                'product_uom_qty': spare_part.Qty,
                                'product_uom': spare_part.product_id.uom_id.id,
                                'location_id': spare_part.from_location_id.id,
                                # 'location_dest_id': self.env.ref('stock.stock_location_output'),
                                'location_dest_id': spare_part.to_location_id.id,
                                'name': self.name,
                                'state': 'done',
                                'origin': self.name,
                            },
                        ))

                if move_ids:
                    tranfer_values = {
                        'picking_type_id': self.picking_type_id.id,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'move_ids': move_ids,
                        'project': self.project_id.id,
                        'building': self.building_id.id,
                        'floor': self.floor_id.id,
                        'unit': self.unit_id.id,
                        'tenancy_id': self.tenancy_id.id,
                        'tenancy_state': self.tenancy_state,
                        'start_date': self.start_date,
                        'end_date': self.end_date
                    }

                    # Create the stock move
                    picking = tranfers_obj.create(tranfer_values)
                    picking.move_ids.write({'date': picking.scheduled_date})
                    picking.state = 'done'
        return True


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    spare_part_id = fields.Many2one('spare.parts', string='Spare Part')
    tenancy_id = fields.Many2one('tenancy.contract', string='Tenancy Contract')
    tenancy_state = fields.Selection([
        ('new', 'New'),
        ('renew', 'Renew'),
        ('open', 'In Progress'),
        ('closed', 'Closed'),
    ], string='Tenancy State', default='new')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def _set_scheduled_date(self):
        for picking in self:
            if picking.state in ('done', 'cancel'):
                # raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
                picking.move_ids.write({'date': picking.scheduled_date})


class StockMove(models.Model):
    _inherit = 'stock.move'

    spare_part_id = fields.Many2one('spare.parts', string='Spare Part')
