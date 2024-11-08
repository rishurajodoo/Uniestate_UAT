# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Project(models.Model):
    _inherit = 'project.project'

    project_reg_number = fields.Integer(string='Project Registration No')
