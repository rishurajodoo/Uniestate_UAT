from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from datetime import timedelta


class ProjectProjectInherit(models.Model):
    _inherit = 'project.project'

    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code', default="New")
    # parent_project = fields.Many2one(comodel_name='project.project', string='Parent Project')
    parent_project = fields.Many2one(
        comodel_name='project.project',
        relation='contents_found_rel',
        column1='lot_id',
        column2='content_id',
        string='Parent Project')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    analytic_tag_id = fields.Many2one('account.analytic.plan', string="Analytic Tag")
    number_of_buildings = fields.Integer("Number Of Buildings", compute='_compute_number_of_buildings')

    def _compute_number_of_buildings(self):
        for rec in self:
            if not rec.id:
                rec.number_of_buildings = 0
                continue
            buildings = self.env['property.building'].search_count([('project_id', '=', rec.id)])
            if buildings:
                rec.number_of_buildings = buildings
            else:
                rec.number_of_buildings = 0

    def create_building(self):
        data = {
            'name': self.name,
            'project_id': self.id,
        }
        self.env['property.building'].create(data)

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = vals['name']
        result = super(ProjectProjectInherit, self).create(vals)
        analytic_tag = self.env['account.analytic.plan'].create({
            'name': result.code,
            'project_id': result.id,
        })
        # analytic_account = self.env['account.analytic.account'].create({
        #     'name': result.code,
        #     'project_id': result.id,
        #     'plan_id': analytic_tag.id
        # })
        # result.analytic_account_id = analytic_account.id
        result.analytic_tag_id = analytic_tag.id
        return result

    def unlink(self):
        for rec in self:
            analytic_accounts = self.env['account.analytic.account'].search([('project_id', '=', rec.id)])
            analytic_tag = self.env['account.analytic.plan'].search([('project_id', '=', rec.id)])
            building_ids = self.env['property.building'].search([('project_id', '=', rec.id)])
            if analytic_accounts:
                analytic_accounts.unlink()
            if analytic_tag:
                analytic_tag.unlink()
            if building_ids:
                building_ids.unlink()
            return super(ProjectProjectInherit, self).unlink()

    @api.onchange('code')
    def _on_change_code(self):
        if self.analytic_account_id:
            self.analytic_account_id.name = self.code
        else:
            analytic_account = self.env['account.analytic.account'].create({
                'name': self.code,
                'plan_id': self.analytic_tag_id.id
            })
            self.analytic_account_id = analytic_account.id
        if self.analytic_tag_id:
            self.analytic_tag_id.name = self.code
        else:
            self.env['account.analytic.plan'].create({
                'name': self.code,
            })
            self.analytic_tag_id.name = self.code


class OLBuilding(models.Model):
    _name = 'property.building'

    image_1920 = fields.Binary('Image')
    name = fields.Char("Name")
    project_id = fields.Many2one("project.project", "Project")
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code', default="New")
    number_of_floors = fields.Integer("Number Of Floors", compute='_compute_number_of_floors')
    floor_ids = fields.One2many('property.floor', 'building_id', string='Floor')
    project_analytical = fields.Many2one(related="project_id.analytic_account_id", string="Project Analytic Account")
    building_account_analytical = fields.Many2one('account.analytic.account', string="Building Account Analytical")
    analytic_tag_id = fields.Many2one('account.analytic.plan', string="Analytic Tag")
    plot_no = fields.Char('Plot Number')
    facility_charges = fields.Float(string='Facility Charges/SQF')
    tax_afm_id = fields.Many2one('account.tax', string='Tax for AFM')

    def _compute_number_of_floors(self):
        for rec in self:
            floors = self.env['property.floor'].search_count([('building_id.id', '=', rec.id)])
            if floors:
                rec.number_of_floors = floors
            else:
                rec.number_of_floors = 0

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            buildings = self.env['property.building'].search([('project_id', '=', self.project_id.id)]).ids
            if vals.get('project_id'):
                project = self.env['project.project'].search([('id', '=', vals['project_id'])])
                if project.code:
                    vals['code'] = project.code + "-" + f'{len(buildings) + 1:02}' or 'New'
        result = super(OLBuilding, self).create(vals)
        return result

    def unlink(self):
        for rec in self:
            analytic_accounts = self.env['account.analytic.account'].search([('building_id', '=', rec.id)])
            analytic_tag = self.env['account.analytic.plan'].search([('building_id', '=', rec.id)])
            floor_ids = self.env['property.floor'].search([('building_id', '=', rec.id)])
            if analytic_accounts:
                analytic_accounts.unlink()
            if analytic_tag:
                analytic_tag.unlink()
            if floor_ids:
                floor_ids.unlink()
            return super(OLBuilding, self).unlink()

    # def generate_floor(self):
    #     if self.number_of_floors:
    #         floor_obj=self.env['property.floor']
    #         for i in range(self.number_of_floors):
    #             floor_obj.create({
    #                 'code':self.code+'-'+f'{i+1:02}',
    #                 'building_id':self.id
    #             })
    #     else:
    #         raise UserError("Enter Number Of Floors First")


class FloorName(models.Model):
    _name = "floor.name"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=1)

class OLFloor(models.Model):
    _name = "property.floor"

    name = fields.Many2one('floor.name', string='Name')
    project_id = fields.Many2one("project.project", "Project")
    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code')
    units = fields.Many2many(comodel_name='product.product', string='Units')
    building_id = fields.Many2one(comodel_name='property.building', string='Building')
    unit_ids = fields.One2many('product.product', 'floor_id', string='Unit')
    project_analytical = fields.Many2one(related="building_id.project_id.analytic_account_id",
                                         string="Project Analytic Account")
    building_analytic_account = fields.Many2one(related="building_id.building_account_analytical",
                                                string="Building Analytic Account")
    floor_analytic_account = fields.Many2one('account.analytic.account', string="Floor Account Analytical")
    project_name = fields.Many2one(related="building_id.project_id", string="Project Name")
    number_of_units = fields.Integer("Number Of Units", compute='_compute_number_of_units')
    analytic_tag_id = fields.Many2one('account.analytic.plan', string="Analytic Tag")

    def _compute_number_of_units(self):
        for rec in self:
            units = self.env['product.product'].search_count([('floor_id.id', '=', rec.id)])
            if units:
                rec.number_of_units = units
            else:
                rec.number_of_units = 0

    def unlink(self):
        for rec in self:
            analytic_accounts = self.env['account.analytic.account'].search([('floor_id', '=', rec.id)])
            analytic_tag = self.env['account.analytic.plan'].search([('floor_id', '=', rec.id)])
            unit_ids = self.env['product.product'].search([('floor_id', '=', rec.id)])
            if analytic_accounts:
                analytic_accounts.unlink()
            if analytic_tag:
                analytic_tag.unlink()
            if unit_ids:
                unit_ids.unlink()
            return super(OLFloor, self).unlink()


class PDC(models.Model):
    _name = "post.date.checks"

    customer_name = fields.Many2one("res.partner", string="Customer Name")
    name_of_cheque = fields.Char(string="Name of Cheque")
    date_of_cheqeu = fields.Date(string="Date of Cheque")
    Bank = fields.Char(string="Bank")
    attach = fields.Many2many('ir.attachment', 'ir_attach_rel', 'unit_ids', 'attachment_id', string="Attachments",
                              help="If any")
    type_char = fields.Char("Type")


class ProductInh(models.Model):
    _inherit = 'product.product'

    short_name = fields.Char(string='Short Name')
    code = fields.Char(string='Code', default="New")
    building = fields.Many2one(comodel_name='property.building', string='Building',
                               domain='[("project_id", "=", project)]')
    view_type = fields.Selection(string='View Type', selection=[
        ('front', 'Front View'),
        ('rear', 'Rear View'),
        ('road', 'Road View'),
        ('park', 'Park View'),
        ('golf', 'Golf View'),
    ])
    property_name = fields.Char(string='Name')
    category = fields.Selection(string='Category', selection=[('rent', 'Rent'), ('sale', 'Sale'), ])
    property_price = fields.Float(string='Property Price')
    allow_discount = fields.Float(string='Allow Discount')
    reasonable_price = fields.Float(string='Reasonable Price')
    property_owner = fields.Many2one(comodel_name='res.partner', string='Property Owner')
    lessor = fields.Many2one(comodel_name='res.partner', string="Lessor's")
    construction_status = fields.Char(string='Construction Status')
    floor_id = fields.Many2one('property.floor', string='Floor', domain='[("building_id", "=", building)]')
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('booked', 'Booked'),
        ('sold', 'Sold'),
        ('cancel', 'Cancel'),
    ], default='available')
    sale_order = fields.Many2one('sale.order', string='Sale Order')
    so_amount = fields.Float(string='SO Amount')
    project_analytical = fields.Many2one(related="floor_id.building_id.project_id.analytic_account_id",
                                         string="Project Analytic Account")
    building_analytic_account = fields.Many2one(related="floor_id.building_id.building_account_analytical",
                                                string="Building Analytic Account")
    floor_analytic_account = fields.Many2one(related="floor_id.floor_analytic_account",
                                             string="Floor Account Analytical")
    units_analytic_account = fields.Many2one('account.analytic.account', string="Units Account Analytical")
    order = fields.Many2one(related='sale_order.order_line.product_id')
    # new fields

    furnishing = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Furnishing')
    build_up_area = fields.Float('Build Up Area')
    carpet_area = fields.Float('Carpet Area')
    bedroom = fields.Integer('Bedroom')
    washroom = fields.Integer('Washroom')
    balconies = fields.Integer('Balconies')
    plot_num = fields.Char(string='Plot No#')
    analytic_tag_id = fields.Many2one('account.analytic.plan', string="Analytic Tag")
    floor_name = fields.Many2one('floor.name')

    invoice_date = fields.Date(string='Invoice Date')

    def generate_invoices_active(self):
        return {'name': _("Create Invoices"),
                'type': 'ir.actions.act_window',
                'res_model': 'invoice.date.wizard',
                'view_id': self.env.ref('ol_property_custom.invoice_date_wizard_view_form').id,
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_product_ids': self.ids},
                }

    def action_block_activate(self):
        for rec in self:
            rec.active = False

    def action_un_block_activate(self):
        for rec in self:
            rec.active = True

    def unlink(self):
        for rec in self:
            analytic_accounts = self.env['account.analytic.account'].search([('unit_id', '=', rec.id)])
            analytic_tag = self.env['account.analytic.plan'].search([('unit_id', '=', rec.id)])
            partner_ids = self.env['res.partner'].search([('name', '=', rec.name)])
            if analytic_accounts:
                analytic_accounts.unlink()
            if analytic_tag:
                analytic_tag.unlink()
            if partner_ids:
                partner_ids.unlink()
            return super(ProductInh, self).unlink()


class PropertyConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    account_afm = fields.Many2one('account.account', string='Account for AFM', config_parameter='ol_property_custom.account_afm')
    tax_afm = fields.Many2one('account.tax', string='Tax for AFM', config_parameter='ol_property_custom.tax_afm')
    admin_fee_product = fields.Many2one('product.template', string='Admin Fee Product', config_parameter='ol_property_custom.admin_fee_product')

class WhatsappSendMessage(models.TransientModel):
   _name = 'invoice.date.wizard'
   _description = "Invoice Date Wizard"

   product_ids = fields.Many2many('product.product', string="Invoice")
   invoice_date = fields.Date(string='Invoice Date')

   def action_create_invoices(self):
       bill = {}
       for rec in self.product_ids:
           bill = {
               'partner_id': rec.property_owner.id,
               'invoice_date': self.invoice_date,
               'date': self.invoice_date,
               'state': 'draft',
               'is_afm': True,
               'project': rec.project.id,
               'building': rec.building.id,
               'floor': rec.floor_id.id,
               'unit': rec.ids,
               'move_type': 'out_invoice'}
           invoice_line_ids = []
           invoice_line_ids += [(0, 0, {
               'product_id': rec.id,
               'name': f"Facility Charges for {rec.name}",
               'price_unit': rec.building.facility_charges,
               'quantity': rec.property_size,
               'tax_ids': rec.building.tax_afm_id.ids,
               'account_id': int(self.env['ir.config_parameter'].get_param('ol_property_custom.account_afm')),
               'analytic_distribution': {rec.units_analytic_account.id: 100}
           })]
           if invoice_line_ids:
               bill.update({'invoice_line_ids': invoice_line_ids})
           record = self.env['account.move'].create(bill)


class AnalyticAccountInherited(models.Model):
    _inherit = "account.analytic.account"

    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building')
    floor_id = fields.Many2one("property.floor", string="Floor")
    unit_id = fields.Many2one("product.product", string="Unit")


class AnalyticTagsInherited(models.Model):
    _inherit = "account.analytic.plan"

    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building')
    floor_id = fields.Many2one("property.floor", string="Floor")
    unit_id = fields.Many2one("product.product", string="Unit")


class CrmLeadInherited(models.Model):
    _inherit = "crm.lead"

    project_id = fields.Many2one('project.project', string='Project')
    building_id = fields.Many2one('property.building', string='Building', domain="[('project_id', '=', project_id)]")
    floor_id = fields.Many2one("property.floor", string="Floor", domain='[("building_id", "=", building_id)]')
    unit_id = fields.Many2many("product.product", string="Unit",
                              domain="[('state', '=', 'available'), ('floor_id', '=', floor_id)]")
    broker_id = fields.Many2many('res.partner', string="Broker", domain=[("agent", "=", True)])
    # partner_id = fields.Many2one(comodel_name='res.partner', domain='[("is_unit", "=", False)]')

    # def action_sale_quotations_new(self):
    #     print('action_sale_quotations_new called')
    #     if not self.partner_id:
    #         return self.env["ir.actions.actions"]._for_xml_id("sale_crm.crm_quotation_partner_action")
    #     else:
    #         return self.action_new_quotation()
    #
    # def action_new_quotation(self):
    #     # agent_ids = [
    #     #     (6, 0, {"agent_id": x.id, "commission_id": x.commission_id.id})
    #     #     for x in self.broker_id
    #     # ]
    #     # print(agent_ids)
    #     print('action_new_quotation called')
    #     print(self.env['res.partner'].search([('name', '=', self.unit_id.name)]))
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
    #     action['context'] = {
    #         # 'default_broker_id': self.broker_id.ids,
    #         'search_default_opportunity_id': self.id,
    #         'default_opportunity_id': self.id,
    #         'search_default_partner_id': self.env['res.partner'].search([('name', '=', self.unit_id.name)]).id,
    #         'default_partner_id': self.env['res.partner'].search([('name', '=', self.unit_id.name)]).id,
    #         'default_project': self.project_id.id,
    #         'default_building': self.building_id.id,
    #         'default_floor': self.floor_id.id,
    #         'default_purchaser_ids': [(0, 0, {
    #             'purchase_individual': self.partner_id.id,
    #             'purchase_company': self.company_id.id or self.env.company.id,
    #         })],
    #         'default_campaign_id': self.campaign_id.id,
    #         'default_medium_id': self.medium_id.id,
    #         'default_origin': self.name,
    #         'default_source_id': self.source_id.id,
    #         'default_company_id': self.company_id.id or self.env.company.id,
    #         'default_tag_ids': [(6, 0, self.tag_ids.ids)]
    #
    #     }
    #     if self.team_id:
    #         action['context']['default_team_id'] = self.team_id.id,
    #     if self.user_id:
    #         action['context']['default_user_id'] = self.user_id.id
    #     return action
    #
    # def action_view_sale_quotation(self):
    #     print('action_view_sale_quotation called')
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
    #     action['context'] = {
    #         'search_default_draft': 1,
    #         'search_default_partner_id': self.partner_id.id,
    #         'default_partner_id': self.partner_id.id,
    #         'default_opportunity_id': self.id
    #     }
    #     action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
    #     quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
    #     if len(quotations) == 1:
    #         action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
    #         action['res_id'] = quotations.id
    #     return action
    #
    # def action_view_sale_order(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
    #     action['context'] = {
    #         'search_default_partner_id': self.partner_id.id,
    #         'default_partner_id': self.partner_id.id,
    #         'default_opportunity_id': self.id,
    #     }
    #     action['domain'] = [('opportunity_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel'))]
    #     orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'sent', 'cancel'))
    #     if len(orders) == 1:
    #         action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
    #         action['res_id'] = orders.id
    #     return action
