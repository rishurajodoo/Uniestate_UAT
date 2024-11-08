from odoo import models, fields

class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    journal_entry_count = fields.Integer(compute='_compute_journal_entry_count', string="Journal Entries")


    def _compute_journal_entry_count(self):
        for record in self:
            record.journal_entry_count = self.env['account.move'].search_count([
                ('hr_salary_attachment_id', '=', record.id)
            ])

    def create_new_journal_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'default_type': 'entry','default_hr_salary_attachment_id': self.id},
            'target': 'current',
        }

    def action_view_journal_entries(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('hr_salary_attachment_id', '=', self.id)],
            'target': 'current',
        }
