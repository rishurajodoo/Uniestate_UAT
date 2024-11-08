from odoo import _, api, fields, models, http
from odoo.exceptions import ValidationError
from odoo.http import request


class PortalAttendance(models.Model):
    _name = "portal.attendance"
    _description = "Portal Attendance"
    _inherit = "portal.mixin"
    _rec_name = "start_date"

    # new fields # T4964
    start_date = fields.Datetime("Start Date", required=True)
    end_date = fields.Datetime("End Date")
    date = fields.Date(string="Date", compute="_compute_date")
    employee_id = fields.Many2one(
        "portal.employee", string="Portal Employee", required=True
    )

    @api.constrains("start_date", "end_date")
    def check_to_start_date(self):
        """add validation for start date and end date # T4964"""
        for attendance in self:
            if not attendance.start_date or not attendance.end_date:
                continue
            if attendance.end_date < attendance.start_date:
                raise ValidationError(
                    _("Start date can not be larger than End date!!!")
                )

    @api.depends("start_date")
    def _compute_date(self):
        """compute date based on start date # T4964"""
        for attendance in self:
            if not attendance.start_date:
                attendance.date = False
                continue
            attendance.date = attendance.start_date.date()

    def _compute_access_url(self):
        super(PortalAttendance, self)._compute_access_url()
        for attendance in self:
            attendance.access_url = "/my/attendance/%s" % attendance.id
