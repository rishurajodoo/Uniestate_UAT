from odoo import _, http, fields
from odoo.http import request, route
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.tools import format_datetime

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

from ..models.misc_utils import datetime_to_odoo

STEP = 10


# class PortalAttendance(http.Controller):


class WebsitePortalAttendance(CustomerPortal):

    @http.route(['/my/timeoff_request'], type='http', auth="user", website=True)
    def portal_timeoff_request(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        leave_types = request.env['hr.leave.type'].sudo().search([])
        values = {
            'employee': employee,
            'leave_types': leave_types,
            'csrf_token': request.csrf_token(),
            'page_name': 'portal_timeoff_request',
        }
        return request.render("employee_activity_portal.portal_timeoff_request", values)

    @http.route(['/my/timeoff_request/submit'], type='http', auth="user", methods=['POST'], website=True)
    def portal_timeoff_request_submit(self, **post):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
        leave_type_id = int(post.get('leave_type'))
        date_from = post.get('date_from')
        date_to = post.get('date_to')
        description = post.get('description')
        attachment = post.get('attachment')
        
        # Checking if any overlapping leaves exist
        overlapping_leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ['confirm', 'validate']),
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from)
        ])

        if overlapping_leaves:
            error_message = "You've already booked time off which overlaps with this period: from %s to %s" % (overlapping_leaves.date_from, overlapping_leaves.date_to)
            return request.render("employee_activity_portal.portal_timeoff_request", {
                'error': error_message,
                'leave_types': request.env['hr.leave.type'].sudo().search([]),
                'csrf_token': request.csrf_token(),
            })

        
        # Validate required fields
        if not leave_type_id or not date_from or not date_to:
            return request.render("employee_activity_portal.portal_timeoff_request", {
                'error': 'Please fill in all required fields!',
                'leave_types': request.env['hr.leave.type'].sudo().search([]),
                'csrf_token': request.csrf_token(),
            })
        
        # Create a time off request
        leave_request = request.env['hr.leave'].sudo().create({
            'employee_id': employee.id,
            'holiday_status_id': leave_type_id,
            'date_from': date_from,
            'date_to': date_to,
            'number_of_days': (fields.Date.from_string(date_to) - fields.Date.from_string(date_from)).days + 1,
            'name': description,
            'state': 'confirm',  # It can be 'draft' or 'confirm' based on workflow
        })

        # Handle attachment if provided
        if attachment:
            attachment_data = request.httprequest.files.get('attachment')
            request.env['ir.attachment'].sudo().create({
                'name': attachment_data.filename,
                'res_model': 'hr.leave',
                'res_id': leave_request.id,
                'datas': attachment_data.read(),
                'type': 'binary',
            })

        return request.redirect('/my/timeoff')

    @http.route(['/my/timeoff'], type='http', auth="user", website=True)
    def portal_my_timeoff(self, **kwargs):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        
        # Fetch the time off data
        timeoff_allocations = request.env['hr.leave.allocation'].sudo().search([('employee_id', '=', employee.id),('state', '=', 'validate') ])
        # timeoff_requests = request.env['hr.leave'].sudo().search([('employee_id', '=', employee.id)])
        timeoff_requests = request.env['hr.leave'].sudo().search([('employee_id', '=', employee.id)])

        leave_types = request.env['hr.leave.type'].sudo().search([])

        values = {
            'employee': employee,
            'timeoff_allocations': timeoff_allocations,
            'timeoff_requests': timeoff_requests,
            'leave_types': leave_types,
            'csrf_token': request.csrf_token(),
            'page_name': 'portal_timeoff',
            'timeoff_check': 1
        }
        
        return request.render("employee_activity_portal.portal_my_timeoff", values)

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_portal_layout_values()
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", request.env.user.id)], limit=1)
        )

        values["employee"] = employee
        values["employee_attendance_state"] = employee.employee_attendance_state
        print("\n\n Employee", values["employee"], employee.employee_attendance_state)
        return request.render("portal.portal_my_home", values)

    def _prepare_home_portal_values(self, counters):
        """Prepare value for /my/attendance"""
        values = super(WebsitePortalAttendance, self)._prepare_home_portal_values(
            counters
        )

        if "portal_attendance_count" not in counters:
            return values

        portal_attendance = request.env["hr.attendance"]
        domain = self.get_portal_attendance_domain()
        values["portal_attendance_count"] = (
            portal_attendance.search_count(domain)
            if portal_attendance.check_access_rights("read", raise_exception=False)
            else 0
        )
        values["check_count"] = 1
        values["timeoff_count"] = 1
        values["timeoff_req_count"] = 1
        return values

    @http.route(["/my/attendance/check_in"], type="http", auth="public", website=True)
    def portal_attendance_check_in(self, **kw):
        # Get the current employee linked to the user
        employee = request.env["hr.employee"].search(
            [("user_id", "=", request.env.user.id)], limit=1
        )
        if employee:
            # Call the check_in method
            employee.sudo()._attendance_action_change()
        return request.redirect("/my/home")

    # @http.route(["/my/attendance/check_out"], type="http", auth="public", website=True)
    # def portal_attendance_check_out(self, **kw):
    #     # Get the current employee linked to the user
    #     employee = request.env["hr.employee"].search(
    #         [("user_id", "=", request.env.user.id)], limit=1
    #     )
    #     if employee:
    #         # Call the check_out method
    #         employee.sudo()._attendance_action_change()
    #     return request.redirect("/my/home")

    @http.route(
        ["/my/attendance", "/my/attendance/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_attendance(self, page=1, sortby=None, **kw):
        """render page for list of attendance"""
        values = self._prepare_portal_layout_values()
        domain = self.get_portal_attendance_domain()
        # portal_attendance = request.env["portal.attendance"]
        portal_attendance = request.env["hr.attendance"]
        searchbar_sortings = {
            "date": {"label": _("Check IN Date"), "order": "check_in desc, id desc"},
        }
        # default sort by value
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        # portal_attendance count
        portal_attendance_count = portal_attendance.search_count(domain)

        pager = portal_pager(
            url="/my/attendance",
            url_args={"sortby": sortby},
            total=portal_attendance_count,
            page=page,
            step=STEP,
        )
        # search the count to display, according to the pager data
        portal_attendances = portal_attendance.search(
            domain, order=order, limit=STEP, offset=pager["offset"]
        )
        request.session["my_portal_attendance_history"] = portal_attendances.ids[:100]
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", request.env.user.id)], limit=1)
        )
        # if not employee:
        #     return request.not_found()
        # last_attendance = (
        #     request.env["hr.attendance"]
        #     .sudo()
        #     .search([("employee_id", "=", employee.id)], limit=1, order="check_in desc")
        # )

        # employee_attendance_state = (
        #     "checked_in"
        #     if last_attendance and last_attendance.check_out is None
        #     else "checked_out"
        # )
        values.update(
            {
                "portal_attendances": portal_attendances,
                "page_name": "portal_attendance",
                "pager": pager,
                "default_url": "/my/attendance",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                # "employee_attendance_state": employee_attendance_state,
                "employee": employee,
            }
        )
        return request.render(
            "employee_activity_portal.portal_my_portal_attendance", values
        )

    def get_portal_attendance_domain(self):
        """pass domain for portal attendance"""
        current_user = request.env.user
        domain = [
            ("employee_id.user_id", "=", current_user.id),
        ]
        return domain

    def _portal_attendance_get_page_view_values(
        self, portal_attendance, access_token, **kwargs
    ):
        """return value of edit view page in portal attendance"""
        values = {
            "portal_attendance": portal_attendance,
            "format_datetime": lambda dt: format_datetime(
                request.env, dt, dt_format=False
            ),
        }
        return self._get_page_view_values(
            document=portal_attendance,
            access_token=access_token,
            values=values,
            session_history="my_portal_attendance_history",
            no_breadcrumbs=False,
            **kwargs
        )

    # @http.route(
    #     ["/my/attendance/<int:attendance>"],
    #     type="http",
    #     auth="public",
    #     website=True,
    # )
    # def portal_my_attendance_form(self, attendance, access_token=None, **kw):
    #     """render page for edit view of portal attendance # T4964"""
    #     try:
    #         portal_attendance = (
    #             request.env["portal.attendance"].browse(attendance).sudo()
    #         )
    #     except Exception:
    #         return request.redirect("/page_404")
    #     if not portal_attendance.exists():
    #         return request.redirect("/page_404")

    #     try:
    #         self._document_check_access(
    #             "portal.employee",
    #             portal_attendance.employee_id.id,
    #             access_token=access_token,
    #         )
    #     except (AccessError, MissingError):
    #         return request.redirect("/page_403")

    #     values = self._portal_attendance_get_page_view_values(
    #         portal_attendance, access_token, **kw
    #     )

        # return request.render(
        #     "employee_activity_portal.portal_attendance_form_template", values
        # )

    @http.route(
        """/my/attendance/continue/<int:portal_attendance>""",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def action_attendance_continue(self, portal_attendance, access_token, **kwargs):
        """on submit save value in portal.attendance and
        if given value save then send success message # T4964"""
        try:
            portal_attendance_id = (
                request.env["portal.attendance"].browse(portal_attendance).sudo()
            )
        except Exception:
            return request.redirect("/page_404")
        if not portal_attendance_id.exists():
            return request.redirect("/page_404")

        try:
            self._document_check_access(
                "portal.employee",
                portal_attendance_id.employee_id.id,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/page_403")

        datetime_format = "%m/%d/%Y %H:%M:%S"
        current_user_timezone = request.env.user.tz

        try:
            start_date = kwargs.get("startdate-%s" % (portal_attendance_id.id))
            convert_start_date = datetime_to_odoo(
                datetime_val=start_date,
                datetime_format=datetime_format,
                from_tz=current_user_timezone,
                to_utc=True,
            )
        except Exception:
            error = {"error": _("Invalid value in Start Date.")}
            return self.portal_my_attendance_form(
                attendance=portal_attendance, access_token=access_token, **error
            )

        try:
            end_date = kwargs.get("enddate-%s" % (portal_attendance_id.id))
            convert_end_date = datetime_to_odoo(
                datetime_val=end_date,
                datetime_format=datetime_format,
                from_tz=current_user_timezone,
                to_utc=True,
            )
        except Exception:
            error = {"error": _("Invalid value in End Date.")}
            return self.portal_my_attendance_form(
                attendance=portal_attendance, access_token=access_token, **error
            )

        try:
            portal_attendance_id.write(
                {"start_date": convert_start_date, "end_date": convert_end_date}
            )
        except ValidationError:
            error = {"error": _("Start date can not be larger than End date!!!.")}
            return self.portal_my_attendance_form(
                attendance=portal_attendance, access_token=access_token, **error
            )
        except Exception:
            error = {
                "error": _("Somthing went wrong.Please try after refreshing page.")
            }
            return self.portal_my_attendance_form(
                attendance=portal_attendance, access_token=access_token, **error
            )

        val = {
            "success": _("Successfully updated attendance value."),
        }
        return self.portal_my_attendance_form(
            attendance=portal_attendance, access_token=access_token, **val
        )

    @http.route(
        """/page_403""", type="http", auth="public", website=True, sitemap=False
    )
    def website_403(self, **kwargs):
        return request.render("http_routing.403", {}, status=403)

    @http.route(
        """/page_404""", type="http", auth="public", website=True, sitemap=False
    )
    def website_404(self, **kwargs):
        return request.render("http_routing.404", {}, status=404)
