from odoo import models, fields, api, _


class MaintenanceOperationType(models.Model):
    _name = "maintenance.operation.type"
    _description = 'Maintenance Operation Type'

    name = fields.Char('Name')
