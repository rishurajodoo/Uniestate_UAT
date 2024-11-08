from odoo import api, fields, models


class BuildingType(models.Model):
    _name = 'building.type'

    name = fields.Char('Name')
