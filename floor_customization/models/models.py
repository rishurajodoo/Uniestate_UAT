from odoo import api, fields, models


class PropertyFloorInherit(models.Model):
    _inherit = 'property.floor'

    floor_type = fields.Selection([
        ('commercial', 'Commercial'),
        ('residential', 'Residential'),
    ])

    floor_type_id = fields.Many2one('floor.type', 'Floor Type')


class FloorType(models.Model):
    _name = 'floor.type'

    name = fields.Char('Name')


class FloorWizardInherit(models.Model):
    _inherit = 'create.floor.wizard'

    floor_detail_ids = fields.One2many('floor.detail', 'floor_wizard_id')


class FloorDetail(models.Model):
    _name = 'floor.detail'

    name = fields.Many2one('floor.name', string='Name')
    floor_type_id = fields.Many2one('floor.type', 'Floor Type')
    floor_wizard_id = fields.Many2one('create.floor.wizard')

