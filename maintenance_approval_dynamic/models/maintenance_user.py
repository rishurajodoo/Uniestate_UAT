from odoo import models, fields, api, _


class UserConfirm(models.Model):
    _name = 'user.sale'
    _description = 'Maintenance Users'
    _inherit = ['mail.thread']

    approver_ids = fields.Many2many(comodel_name='res.users', string="Users")
