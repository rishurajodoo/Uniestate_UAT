from odoo import api, fields, models
from odoo.exceptions import UserError


class UnitWizardInherit(models.Model):
    _inherit = 'create.units.wizard'

    unit_detail_ids = fields.One2many('unit.detail', 'unit_wizard_id')
    for_rent = fields.Boolean(default=True)
    for_sale = fields.Boolean(default=False)

    @api.constrains('for_sale', 'for_rent')
    def _constrains_on_sale_selection(self):
        for rec in self:
            if rec.for_sale and rec.for_rent:
                raise UserError("You Can't be able to select both Sale and Rent on same time")

    unit_type_id = fields.Many2one('unit.type', 'Unit Type')
    sub_unit_id = fields.Many2one('sub.unit.type', 'Sub Unit Type')


class UnitDetail(models.Model):
    _name = 'unit.detail'

    name = fields.Char('Name')
    unit_wizard_id = fields.Many2one('create.units.wizard')

    @api.onchange('for_rent', 'for_sale')
    def _onchange_rent_sale(self):
        for line in self:
            if line.for_rent:
                line.for_sale = False
            elif line.for_sale:
                line.for_rent = False
