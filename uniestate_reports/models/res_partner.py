from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dob = fields.Date(string='Date Of Birth')
    is_resident = fields.Boolean(string='Is Resident')
    phone_o = fields.Char(string='Phone(O)')
