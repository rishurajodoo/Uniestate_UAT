# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class statement_of_account_report(models.Model):
#     _name = 'statement_of_account_report.statement_of_account_report'
#     _description = 'statement_of_account_report.statement_of_account_report'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
