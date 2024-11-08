from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class WebsitePortalEmployee(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        """Inherit Method to add key(value) of emloyees count"""
        values = super(WebsitePortalEmployee, self)._prepare_home_portal_values(
            counters
        )
        if "portal_employee_count" not in counters:
            return values
        portal_employee = request.env["portal.employee"]
        domain = self.get_portal_employee_domain()
        values["portal_employee_count"] = (
            portal_employee.search_count(domain)
            if portal_employee.check_access_rights("read", raise_exception=False)
            else 0
        )
        return values

    def get_portal_employee_domain(self):
        """Return Domain for records to be shown"""
        user = request.env.user
        domain = [
            ("main_user_id", "=", user.id),
        ]
        return domain

    @http.route(
        ["/my/portal_employees", "/my/portal_employees/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_employees_list(self, page=1, sortby=None, **kw):
        """List all Portal Employees"""
        values = self._prepare_portal_layout_values()
        portal_employee = request.env["portal.employee"]
        domain = self.get_portal_employee_domain()
        # count for portal employees
        portal_employee_count = portal_employee.search_count(domain)

        searchbar_sortings = {
            "date": {"label": _("Create Date"), "order": "create_date desc"},
            "name": {"label": _("Name"), "order": "name"},
        }
        # default sortby order
        if not sortby:
            sortby = "date"
        sort_order = searchbar_sortings[sortby]["order"]

        # make pager
        pager = portal_pager(
            url="/my/portal_employees",
            url_args={"sortby": sortby},
            total=portal_employee_count,
            page=page,
            step=self._items_per_page,
        )
        # search the count to display, according to the pager data
        portal_employees = portal_employee.search(
            domain, order=sort_order, limit=self._items_per_page, offset=pager["offset"]
        )
        values.update(
            {
                "portal_employees": portal_employees,
                "page_name": "portal_employee",
                "pager": pager,
                "default_url": "/my/portal_employees",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render(
            "employee_activity_portal.portal_my_employees_list", values
        )

    def _portal_employees_get_edit_page_values(
        self, portal_employee, access_token, **kwargs
    ):
        """Get values of portal employee in edit page"""
        values = {"portal_employee": portal_employee}

        return self._get_page_view_values(
            document=portal_employee,
            access_token=access_token,
            values=values,
            session_history="my_employees_list",
            no_breadcrumbs=False,
            **kwargs
        )

    @http.route(
        ["/my/portal_employees/<int:employee>"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_employee_edit(self, employee, access_token, **kw):
        """Edit portal Employee template render with values"""
        try:
            employee_sudo = self._document_check_access(
                "portal.employee",
                employee,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/page_403")

        values = self._portal_employees_get_edit_page_values(
            employee_sudo, access_token, **kw
        )
        return request.render(
            "employee_activity_portal.portal_employee_edit_template", values
        )

    @http.route(
        """/my/portal_employees/continue/<int:employee>""",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def portal_employee_edit_action_continue(self, employee, access_token, **kwargs):
        """Write Portal Employee"""
        try:
            employee_sudo = self._document_check_access(
                "portal.employee",
                employee,
                access_token=access_token,
            )
        except (AccessError, MissingError):
            return request.redirect("/page_403")

        employee_sudo.write(
            {
                "name": kwargs.get("portal_employee"),
                "phone": kwargs.get("phone"),
                "email": kwargs.get("email"),
            }
        )
        val = {
            "success": _("Successfully updated Employee details."),
        }
        return self.portal_my_employee_edit(
            employee=employee, access_token=access_token, **val
        )

    @http.route(
        ["/my/portal_register_employee"],
        type="http",
        auth="public",
        website=True,
    )
    def portal_my_employee_register(self, **kw):
        """Register Portal Employee template render"""
        return request.render(
            "employee_activity_portal.portal_employee_register_template"
        )

    @http.route(
        """/my/portal_register_employee/continue""",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def portal_employee_create_action_continue(self, **kwargs):
        """Create Portal Employee"""
        user = request.env.user
        request.env["portal.employee"].create(
            {
                "name": kwargs.get("name"),
                "phone": kwargs.get("phone"),
                "email": kwargs.get("email"),
                "main_user_id": user.id,
            }
        )
        return self.portal_my_employees_list()
