from odoo import api, fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_issue = fields.Date(string="Date of issue")
    place_of_issue = fields.Char(string="Place of issue")

