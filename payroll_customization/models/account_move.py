from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    hr_salary_attachment_id = fields.Many2one("hr.salary.attachment", string="Hr Salary Attachment Id")