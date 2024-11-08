import uuid

from odoo import api, fields, models


class PortalEmployee(models.Model):
    _name = "portal.employee"
    _description = "Portal Employee"

    @api.model
    def _default_work_address_id(self):
        return self.env.company.partner_id

    name = fields.Char(string="Name", required=True)
    email = fields.Char(
        string="Email",
    )
    phone = fields.Char(
        string="Phone",
    )
    work_address_id = fields.Many2one(
        "res.partner",
        "Address",
        default=_default_work_address_id,
        help="Address where employees are working",
    )
    main_user_id = fields.Many2one(
        "res.users",
        string="User",
    )
    access_token = fields.Char("Access Token")

    @api.model
    def create(self, vals):
        res = super(PortalEmployee, self).create(vals)
        res.generate_token()
        return res

    def generate_token(self):
        for employee in self:
            employee.access_token = str(uuid.uuid4())

    def get_employee(self, access_token):
        employee = self.search(["access_token", "=", access_token])
        return employee


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    access_token = fields.Char("Access Token")
    employee_attendance_state = fields.Selection(
        string="Employee Attendance State",
        selection=[("checked_in", "Checked In"), ("checked_out", "Checked Out")],
        compute="_compute_employee_attendance_state",
    )

    def _compute_employee_attendance_state(self):
        for rec in self:
            rec.employee_attendance_state = False
            last_attendance = self.env["hr.attendance"].search(
                [("employee_id", "=", rec.id)], limit=1, order="check_in desc"
            )
            if last_attendance:
                rec.employee_attendance_state = (
                    "checked_in"
                    if last_attendance and not last_attendance.check_out
                    else "checked_out"
                )

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        res.generate_token()
        return res

    def generate_token(self):
        for employee in self:
            employee.access_token = str(uuid.uuid4())

    def get_employee(self, access_token):
        employee = self.search(["access_token", "=", access_token])
        return employee


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    access_token = fields.Char("Access Token")

    @api.model
    def create(self, vals):
        res = super(HrEmployeePublic, self).create(vals)
        res.generate_token()
        return res

    def generate_token(self):
        for employee in self:
            employee.access_token = str(uuid.uuid4())

    def get_employee(self, access_token):
        employee = self.search(["access_token", "=", access_token])
        return employee
